# WebUI

WebUI 是使用 KToolBox 的建議方式。它在瀏覽器介面中集中管理一個同步專案的設定、工作、進度與歷史。

## 首次執行

安裝 WebUI 版本，建立專案目錄並啟動 KToolBox：

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

瀏覽器會自動開啟。使用終端機顯示的 `admin` 使用者名稱與隨機密碼登入。缺少 `ktoolbox.toml` 時 KToolBox 會自動建立；新工作預設使用專案中的 `downloads` 目錄。

![KToolBox WebUI 概覽](../assets/webui/40-overview-showcase-desktop-light.png)

## 第一次同步

1. 開啟「創作者」，選擇「加入創作者」。
2. 貼上 Pawchive 創作者 URL，或填寫平台與 ID。
3. 開啟「工作」，選擇「建立工作」，再選擇「同步創作者」。
4. 首次檢查新創作者與命名格式時，建議先設定較小的作品數量限制。
5. 開啟工作詳情，查看下載、速度、重試與有用的活動記錄。

已完成的檔案會保留；相容的暫存檔可繼續下載；單一創作者失敗也不會刪除同一工作中其他創作者已成功下載的內容。

## 依目標繼續閱讀

<div class="grid cards" markdown>

-   :material-folder-account-outline: **創作者、作品、忽略規則與命名**

    日常專案管理請閱讀[專案工作流程](webui/project-workflows.md)。

-   :material-progress-download: **進度與工作控制**

    暫停、停止、重新執行、錯誤診斷與安全清理請參閱[工作與即時更新](webui/tasks.md)。

-   :material-server-security: **帳號與部署**

    只有需要固定憑證、遠端存取、備份或詳細安全機制時，才需要閱讀[部署參考](webui/reference.md)。

-   :material-update: **現有 v0 專案**

    轉換舊設定或下載前，請先閱讀[遷移指南](migration-v1.md)。

</div>

## 選用的固定帳號

首次執行使用自動產生的憑證即可。如需在重新啟動後維持相同帳號，請產生密碼雜湊：

```bash
ktoolbox webui hash-password
```

將結果寫入專案 `.env`：

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## 安全存取

內建服務使用 HTTP。僅在本機使用時，請繫結至 `127.0.0.1`：

```bash
ktoolbox webui . --host 127.0.0.1
```

遠端存取請使用可信網路或 HTTPS 反向代理。能夠登入的使用者可查看專案路徑、設定與工作記錄，請勿向不可信使用者開放。同一專案一次只能由一個 WebUI 程序管理。
