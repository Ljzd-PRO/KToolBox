# WebUI 部署參考

完成首次安全設定後，請使用本參考維護、備份及檢查 WebUI 執行個體。

## 關於

關於頁集中顯示版本、授權與執行環境，並提供文件、原始碼及問題回報入口。URL、IP 與監聽位址統一使用行內程式碼樣式。

![深色窄螢幕關於頁](../../assets/webui/32-about-mobile-dark.png)

刪除工作通常只移除其佇列記錄、嘗試和記錄。「刪除輸出」會先產生檔案與位元組數預覽。確認後只移除記錄為由該工作建立且未變更的一般檔案；符號連結、既有檔案、已修改檔案與共用檔案永遠不會被跟隨或移除。

## WebUI 環境參考

| 變數 | 預設值 | 含義 |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | 監聽介面。 |
| `KTOOLBOX_WEBUI__PORT` | `8789` | 監聽連接埠，1–65535。 |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | 啟動後開啟本機 URL。 |
| `KTOOLBOX_WEBUI__USERNAME` | 空 → 啟動時為 `admin` | 可選的單一帳號使用者名稱。 |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | 空 | 建議使用的固定 Argon2id 雜湊。 |
| `KTOOLBOX_WEBUI__PASSWORD` | 空 → 每次啟動隨機產生 | 純文字備用值；存在雜湊時忽略。 |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | 並行頂層工作數，1–16。 |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | 從最後使用起計算的工作階段存續時間。 |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | 從登入起計算的最長工作階段存續時間。 |

工作歷程很重要時，請一起備份 `ktoolbox.toml`、本機 dotenv 檔案和 `.ktoolbox/webui.sqlite3`。WebUI 執行時不要複製資料庫。

## 多語言瀏覽器驗收

七種語言目錄均在桌面與行動裝置接受明暗主題實測。以下是通過驗收的代表性介面；使用者內容和檔案系統路徑會保持原文。

![法語行動版設定頁](../../assets/webui/24-configuration-mobile-fr.png)

![俄語行動版遠端路徑選擇器](../../assets/webui/25-path-picker-mobile-ru.png)

## 相關 WebUI 指南

- [安裝與安全概覽](../webui.md)
- [專案工作流程](project-workflows.md)
- [任務與即時更新](tasks.md)
- [部署參考](reference.md)
