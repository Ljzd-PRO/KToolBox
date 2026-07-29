# MCP

KToolBox 會在 WebUI 的同一處理程序與連接埠啟動 Streamable HTTP MCP 服務。它提供經過篩選的專案、工作、創作者、忽略規則、Pawchive 搜尋、命名格式、自動同步及安全設定工具。瀏覽器工作階段與 MCP 用戶端使用不同憑證。

| 服務 | 預設位址 |
| --- | --- |
| WebUI | `http://127.0.0.1:8789/` |
| MCP | `http://127.0.0.1:8789/mcp` |
| WebUI REST OpenAPI | `http://127.0.0.1:8789/api/v1/openapi.yaml` |

下載 OpenAPI 需要已登入的 WebUI 工作階段；儲存庫中的正式契約為 `webui/openapi.yaml`。

## 建立存取權杖

1. 啟動 WebUI 並登入。
2. 開啟側欄中的 **MCP**。
3. 選擇「新增存取權杖」。
4. 填寫容易辨識的名稱，並再次輸入目前的 WebUI 密碼。
5. 選擇「唯讀」或「管理」，再選擇 7、30、90、365 天或永不過期。
6. 立即保存畫面顯示的 `ktmcp_...`；明文只會顯示一次。

KToolBox 只儲存權杖雜湊。MCP 頁面會顯示建立、到期和最後使用時間，並可立即撤銷權杖。永不過期權杖會持續有效直到撤銷，只應在能主動管理生命週期時使用。

## 連線 Codex

將權杖保存在儲存庫之外：

```shell
export KTOOLBOX_MCP_TOKEN="ktmcp_..."
```

在 Codex 設定中加入：

```toml
[mcp_servers.ktoolbox]
url = "http://127.0.0.1:8789/mcp"
bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"
```

MCP 頁面也會產生通用 HTTP、Claude、Cursor、VS Code 和 Codex 設定。範本使用環境變數或受保護輸入，不會直接嵌入權杖。

## 權限與限制

- 唯讀權杖可查看專案摘要、工作、創作者、忽略規則、自動同步狀態、命名歷程、脫敏設定和有限的專案檔案。
- 管理權杖還可執行工具目錄中明確列出的工作、創作者、忽略規則、自動同步及安全結構化設定變更。
- 登入、登出、瀏覽器工作階段、dotenv/TOML 原文編輯、秘密值、任意主機檔案系統、刪除輸出以及無上限記錄或正文均不開放。
- 搜尋與 Pawchive 查詢屬於開放世界操作，可能存取設定的 Pawchive 服務。
- 工具清單、記錄、事件、作品正文和檔案均設有上限或分頁。

執行中版本實際開放的工具以 **MCP** 頁面的目錄為準。

## 安全性

Bearer 權杖可直接存取專案。請勿提交到 Git，也不要放入 Shell 歷程、截圖、記錄或聊天訊息。建議每個用戶端使用獨立權杖，並撤銷不再使用的憑證。

內建伺服器使用 HTTP。同一台電腦上的用戶端應將 WebUI 繫結到 `127.0.0.1`。遠端存取時，請在受信任的反向代理終止 HTTPS 並限制網路存取。切勿透過不受信任的明文網路傳送權杖。

## API 邊界

KToolBox 包含四種不同介面：

- Pawchive OpenAPI 描述上游公開服務；
- [Python API](api.md) 提供型別化 `PawchiveClient`；
- `webui/openapi.yaml` 描述需要驗證的 KToolBox WebUI REST API；
- `/mcp` 提供從 WebUI 契約中篩選產生的 MCP 工具。

WebUI REST 契約與 MCP 都不能取代上游 Pawchive API。
