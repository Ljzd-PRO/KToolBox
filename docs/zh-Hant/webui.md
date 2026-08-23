# WebUI

KToolBox WebUI 是以 React 和 HeroUI 建置、繫結專案的管理面板。它會編輯與 CLI 相同的設定並呼叫相同的 Python 服務；不會啟動或解析 CLI 子處理程序。工作、嘗試、記錄和擁有權記錄會持久化到所選專案內的 `.ktoolbox/webui.sqlite3`。

## 依工作繼續閱讀

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **管理專案資料**

    在[專案工作流程](webui/project-workflows.md)中管理創作者、作品、命名、設定與選用媒體。

-   :material-arrow-right-circle-outline: **監控下載任務**

    在[任務與即時更新](webui/tasks.md)中建立、診斷、暫停、繼續、重新執行及安全刪除任務。

-   :material-arrow-right-circle-outline: **部署與維護**

    在[部署參考](webui/reference.md)中查看環境變數、備份、執行環境與多語言覆蓋。

</div>

## 安裝與啟動

安裝可選執行環境並建立專案目錄：

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

啟動時可以不設定憑證；未設定時，終端機會輸出本次處理程序使用的 `admin` 使用者名稱和新隨機密碼。如需固定憑證，可透過隱藏的終端機輸入產生 Argon2id 密碼雜湊：

```bash
ktoolbox webui hash-password
```

將帳號儲存在專案的 `.env` 中。請用引號包住雜湊，讓 Shell 風格的 `$` 字元保持原樣：

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

為該專案啟動面板：

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

預設為 `0.0.0.0:8789`，本機瀏覽器會自動開啟。`--host`、`--port` 和 `--no-open` 會覆寫該處理程序的環境設定。若缺少 `ktoolbox.toml`，啟動時會列印警告並以原子方式建立最小有效專案文件。缺少憑證不再阻止啟動：使用者名稱留空時使用 `admin`，兩種密碼均留空時為本次執行產生並在終端機輸出新密碼。

## 安全模型

KToolBox 只有一個本機 WebUI 帳號。明確設定始終優先，`KTOOLBOX_WEBUI__PASSWORD_HASH` 又優先於純文字相容設定 `KTOOLBOX_WEBUI__PASSWORD`。兩種密碼均未設定時，每次啟動都會在記憶體中產生新密碼，並只在該處理程序的終端機中連同有效使用者名稱一起輸出。穩定部署建議設定雜湊，並將兩個 dotenv 檔案排除於版本控制之外。

工作階段使用隨機不透明權杖。SQLite 只儲存權杖雜湊；瀏覽器 Cookie 使用 `HttpOnly` 和 `SameSite=Strict`，並在 HTTPS 請求上變為 `Secure`。變更狀態的請求需要每個工作階段的 CSRF 權杖和同源檢查。登入嘗試會限制速率，API 回應不快取，應用程式會傳送嚴格的內容、框架、引用來源與瀏覽器權限標頭。

內建伺服器使用 HTTP。預設 LAN 監聽器只適合受信任網路，否則密碼、Cookie、路徑、記錄與設定在傳輸中都可被看見。單機使用時請指定 `--host 127.0.0.1`；遠端存取時請在受信任的反向代理終止 HTTPS 並限制網路存取。頁面不安全時，登入頁與應用程式外殼會持續顯示 HTTP 警告。

同一時間只能有一個排程器開啟專案。專案鎖可防止兩個 WebUI 處理程序同時操作其佇列與輸出。

遠端路徑選擇器使用 KToolBox 處理程序的檔案系統權限。限定專案的工作、作品與下載結構欄位無法離開已繫結的專案，符號連結也不能繞過此限制。儲存桶與記錄目錄欄位明確使用主機作用域，可能顯示該帳號可瀏覽位置中的名稱與中繼資料。選擇器可以列出中繼資料、建立目錄，並在明確確認後刪除空目錄。刪除採用非遞迴操作：檔案、符號連結、專案根目錄、主目錄根位置，以及包含任何項目的目錄都不會被刪除。選擇器不會讀取檔案內容、上傳、下載、重新命名或刪除檔案。輸入新檔名只會選取路徑，不會建立空檔案。請將 WebUI 存取視為敏感的主機存取，不要提供給不受信任的使用者。
