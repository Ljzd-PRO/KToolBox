# 歡迎使用 KToolBox

KToolBox 用於從 Pawchive 下載公開作品。建議使用 WebUI：常用操作都有引導式表單，離開頁面後仍可查看工作進度。

!!! warning "全新大版本"
    v1 尚未經過足夠廣泛的實際驗證，部分功能仍可能出錯。遷移前請備份原有設定與下載；遇到異常時歡迎回報。

## 從 WebUI 開始

1. 安裝 WebUI 版本。
2. 為同步專案建立一個目錄。
3. 在該目錄中啟動 KToolBox。

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

瀏覽器會自動開啟。使用終端機顯示的 `admin` 使用者名稱與隨機密碼登入，加入創作者，然後建立第一個工作。需要時 KToolBox 會自動建立 `ktoolbox.toml`，並預設下載至 `downloads` 目錄。

![KToolBox WebUI 概覽](../assets/webui/40-overview-showcase-desktop-light.png)

## 選擇下一步

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **加入創作者並下載**

    根據[專案工作流程](webui/project-workflows.md)加入創作者、搜尋作品、建立工作和調整忽略規則。

-   :material-progress-download: **查看工作進度**

    在[工作與即時更新](webui/tasks.md)中了解進度、重試、暫停、停止、重新執行和安全清理。

-   :material-calendar-sync-outline: **定時執行**

    根據[自動同步指南](automatic-sync.md)建立週期計畫。

-   :material-folder-cog-outline: **設定名稱與目錄**

    使用[命名格式指南](naming.md)設定預設輸出和易讀的目錄結構。

</div>

## 進階入口

一般使用者首次執行不需要閱讀以下頁面。

| 目標 | 指南 |
| --- | --- |
| 固定登入帳號或部署至其他裝置 | [WebUI 部署參考](webui/reference.md) |
| 在終端機中自動化 | [命令列指南](commands/guide.md)與[命令參考](commands/reference.md) |
| 查看所有設定 | [設定指南](configuration/guide.md)與[設定參考](configuration/reference.md) |
| 連接 AI 用戶端或 Python 程式 | [MCP](mcp.md) 與 [Python API](api.md) |
| 升級舊專案或解決問題 | [遷移指南](migration-v1.md)與[常見問題](faq.md) |

## 安全預設值

WebUI 預設產生登入憑證、關閉敏感媒體預覽，並使用專案內的輸出目錄。僅在本機使用時請繫結 `127.0.0.1`；不可信網路應使用 HTTPS。KToolBox 不實作 Pawchive 帳號或收藏操作。
