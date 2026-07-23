# 常見問題

## 為什麼無法使用帳號收藏？

KToolBox v1 實作了不需要登入的 14 個 Pawchive 操作。受 `cookieAuth` 保護的 5 個 OpenAPI 操作被明確排除，因此 API 用戶端永遠不會接受或傳送帳號工作階段。

作品標記是另一個已實作的公開操作。請有意識地呼叫它：成功標記會變更伺服器狀態，已標記的作品可能傳回 `PawchiveConflictError`。

## API 呼叫失敗時該怎麼辦？

CLI 會報告型別化 Pawchive 錯誤，而不是傳回部分解析的回應。常見類別包括傳輸、HTTP、驗證、找不到、衝突與回應驗證錯誤。

- 確認 URL 或 `service`、創作者 ID 和作品 ID 正確。
- 連線緩慢時提高 `KTOOLBOX_API__TIMEOUT`。
- 對暫時性傳輸、`429` 或 `5xx` 失敗調整 `KTOOLBOX_API__RETRY_TIMES` 與 `KTOOLBOX_API__RETRY_INTERVAL`。
- 不要在 API 設定中加入帳號 Cookie；API 請求不使用它。

重新導向、一般 `4xx` 回應、衝突和無效回應資料不會重試。

## 為什麼檔案下載會傳回 403？

如果檔案主機要求特定資源的工作階段，請設定僅供下載器使用的金鑰：

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

Cookie 只限於檔案下載請求，不會傳送到 Pawchive API 請求。請將 `.env` 和 `prod.env` 視為含有機密的本機檔案，不要提交它們。

## 如何續傳中斷的下載？

重新執行相同命令。KToolBox 會略過完整的目的檔案。如果存在帶 `downloader.temp_suffix` 的未完成檔案，且伺服器支援範圍請求，下載器會請求剩餘位元組並驗證合併後的大小。

## 如何停用封面或附件？

```dotenv
# 只下載附件。
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# 只下載封面。
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file` 代表主要作品檔案，通常是封面。兩個選項預設均為 `True`。

## 可以將附件直接儲存在作品目錄嗎？

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 如何避免檔名過長？

使用順序名稱或格式精確度限制：

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## 如何設定 Proxy？

HTTPX 會讀取標準 Proxy 環境變數：

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

PowerShell：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## 為什麼設定編輯器無法開啟？

安裝可選的終端機 UI 相依套件：

```bash
pip install "ktoolbox[urwid]"
# 或
pipx install "ktoolbox[urwid]" --force
```

## 如何定期同步多位創作者？

將每位創作者加入專案清單，可選擇指定簡短別名，然後執行不帶目標的 `sync`：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

使用 `creator disable` 保留項目但不在無目標執行中包含它。仍可明確同步已停用的別名。創作者準備與檔案傳輸有不同的並行限制，因此大型創作者不會獨佔所有就緒下載。

## 如何為不同創作者排除不同主題？

在 `ktoolbox.toml` 中加入不同的 `[[blockers]]` 項目。共用規則設為 `scope.mode = "global"`；指定創作者的規則設為 `scope.mode = "creators"` 並使用確切的 `service:id`。規則按檔案順序評估，第一個符合項後停止。

長時間執行前驗證規則運算式與作用域：

```bash
ktoolbox config validate
```

## 為什麼重新導向記錄中的進度顯示不同？

Rich 即時進度只用於互動式終端機。它會顯示每個作用中檔案的速度和 ETA，以及 `Files` 列中所有作用中下載的總速度。管線、CI、`NO_COLOR` 和 `--plain` 使用穩定逐行輸出，以免記錄訊息破壞 ANSI 即時區域。需要無色的互動式版面時使用 `--no-color`，隱藏進度與一般記錄時使用 `--quiet`。

## 為什麼 WebUI 拒絕啟動？

安裝 `ktoolbox[webui]` 並傳入專案目錄。帳號設定可留空，此時終端機會輸出本次執行使用的 `admin` 使用者名稱和隨機密碼。明確設定的密碼雜湊仍必須是有效的 Argon2 值。缺少 `ktoolbox.toml` 時會在終端機警告後自動建立；專案鎖仍會拒絕同一專案的第二個 WebUI 處理程序。

## 將 WebUI 暴露到網路上安全嗎？

預設伺服器使用純 HTTP，因此只在受信任的 LAN 使用 `0.0.0.0`。本機使用請繫結 `127.0.0.1`，遠端存取請置於 HTTPS 反向代理之後。驗證、CSRF、嚴格 Cookie、速率限制與安全標頭能保護應用程式本身，但無法加密 HTTP 網路路徑。

## WebUI 工作在重新啟動後會怎樣？

排隊中的工作會繼續排隊。原本執行中的工作會標記為 `interrupted`，不會靜默重新啟動，因為其設定與遠端狀態可能已變更。請檢查後手動繼續。已完成檔案與可續傳暫存檔仍可使用。

## 刪除 WebUI 工作會移除無關檔案嗎？

一般刪除只移除工作歷程。刪除輸出需要先預覽並確認，然後檢查工作的成品擁有權記錄與檔案中繼資料。既有、已修改、共用、非一般檔案與符號連結路徑都會略過。

## 如何確認同步失敗的真正原因？

開啟失敗工作並查看「工作失敗原因」。KToolBox 會指出對應創作者或檔案、失敗階段、重試是否可能有效及建議操作。若提示回應格式不相容，通常表示 Pawchive 改變了某個欄位的資料形狀；請先更新 KToolBox，再回報面板中顯示的安全操作名稱與欄位路徑。網路、逾時和限流錯誤可稍後重試。診斷報告已脫敏，不會包含上游回應本文、作品標題、Cookie 或完整下載 URL。

## 必須使用 uvloop 或 winloop 嗎？

不必。它們是可選的事件迴圈最佳化。在 Linux/macOS 使用 `ktoolbox[uvloop]`，Windows 使用 `ktoolbox[winloop]`。兩者都未安裝時，KToolBox 會繼續使用 Python 標準 asyncio 迴圈。

## 為什麼防毒軟體可能標記打包的執行檔？

部分啟發式掃描器會標記 PyInstaller 套件或下載管理器。版本透過儲存庫的公開自動化建置；也可使用 `pipx` 安裝，或稽核原始碼後在本機建置。
