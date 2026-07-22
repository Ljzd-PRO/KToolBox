# WebUI

KToolBox WebUI 是以 React 和 HeroUI 建置、繫結專案的管理面板。它會編輯與 CLI 相同的設定並呼叫相同的 Python 服務；不會啟動或解析 CLI 子處理程序。工作、嘗試、記錄和擁有權記錄會持久化到所選專案內的 `.ktoolbox/webui.sqlite3`。

## 安裝與啟動

安裝可選執行環境並建立專案目錄：

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

透過隱藏的終端機輸入產生 Argon2id 密碼雜湊：

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

預設為 `0.0.0.0:8789`，本機瀏覽器會自動開啟。`--host`、`--port` 和 `--no-open` 會覆寫該處理程序的環境設定。若缺少 `ktoolbox.toml`，啟動時會列印警告並以原子方式建立最小有效專案文件。缺少使用者名稱或兩種密碼形式時，啟動仍會失敗。

## 安全模型

KToolBox 只有一個本機 WebUI 帳號，沒有預設憑證。`KTOOLBOX_WEBUI__PASSWORD_HASH` 的優先權高於純文字相容設定 `KTOOLBOX_WEBUI__PASSWORD`。建議使用雜湊，並將兩個 dotenv 檔案排除於版本控制之外。

工作階段使用隨機不透明權杖。SQLite 只儲存權杖雜湊；瀏覽器 Cookie 使用 `HttpOnly` 和 `SameSite=Strict`，並在 HTTPS 請求上變為 `Secure`。變更狀態的請求需要每個工作階段的 CSRF 權杖和同源檢查。登入嘗試會限制速率，API 回應不快取，應用程式會傳送嚴格的內容、框架、引用來源與瀏覽器權限標頭。

內建伺服器使用 HTTP。預設 LAN 監聽器只適合受信任網路，否則密碼、Cookie、路徑、記錄與設定在傳輸中都可被看見。單機使用時請指定 `--host 127.0.0.1`；遠端存取時請在受信任的反向代理終止 HTTPS 並限制網路存取。頁面不安全時，登入頁與應用程式外殼會持續顯示 HTTP 警告。

同一時間只能有一個排程器開啟專案。專案鎖可防止兩個 WebUI 處理程序同時操作其佇列與輸出。

## 專案工作流程

介面在第一次使用時跟隨瀏覽器語言，並支援持久的英語/簡體中文選擇。主題在選擇淺色或深色前會跟隨作業系統。可選藍色、翠綠、紫色、玫瑰色與琥珀色重點色；表單開關啟用時固定為藍色，以在不同色盤間保持一致狀態。桌面使用精簡側邊欄，窄螢幕使用 Drawer。

![淺色設定編輯器](../assets/webui/09-configuration-light.png)

可編輯區域使用柔和的次要表面，欄位背景清楚分隔。欄位圖示便於掃視；表單開關與核取方塊會和標籤靠左對齊，不會看起來像置中的操作按鈕。開關關閉時軌道為灰色，開啟時為藍色；核取方塊只在選取或不確定時顯示指示。可編輯對話框內容與固定操作列共用連續表面。

主要區域包括：

- **概覽：**專案路徑、佇列健康狀態、作用中傳輸總量與最近工作。
- **工作：**建立、排序、編輯、暫停、繼續、停止、重新執行、刪除和查看同步或單篇下載。
- **創作者：**搜尋 Pawchive，並新增、重新命名、啟用、停用或移除清單項目。
- **作品：**在不呈現遠端媒體或展開正文的情況下搜尋、查看修訂並建立下載工作。
- **忽略規則：**排序並限定 `field-match` 規則的作用域，組合巢狀 `any`/`all`、包含、等於、規則運算式與存在條件。
- **設定：**透過型別化表單或進階文字檢視編輯 `.env`、`prod.env` 和 `ktoolbox.toml`。
- **系統：**查看專案與應用程式版本，並下載範例環境檔案。

![窄螢幕工作編輯器](../assets/webui/19-task-form-mobile-light-zh.png)

![窄螢幕創作者清單](../assets/webui/12-creators-mobile-light-zh.png)

## 設定編輯

表單標籤使用明確的英語與簡體中文文字，而非 Python 識別碼。欄位說明取自英語和中文設定類別的 `:ivar field:` docstring，而 Pydantic 提供型別、預設值、範圍與機密中繼資料。

`.env` 和 `prod.env` 分頁會顯示每個最終有效值與來源 Chip。由處理程序環境覆寫的值為唯讀。機密值預設遮蔽。進階文字編輯會顯示額外警告，因為它可能揭露機密。

儲存前，伺服器會解析並驗證建議檔案，然後傳回語意差異。儲存使用 ETag 拒絕過期編輯，並以原子方式取代檔案。TOML 編輯器使用現有 TomlKit/Pydantic 儲存，因此結構化清單與忽略規則變更後仍保留註解。

![深色設定編輯器](../assets/webui/20-configuration-1024-dark-zh.png)

![限定作用域的忽略規則編輯器](../assets/webui/17-blocker-form-1024-light-zh.png)

## 工作生命週期

`sync` 和 `download` 工作會保留對應 CLI 的完整輸入。建立工作時，無目標同步會解析目前已啟用的清單。之後每次嘗試都會收到不可變且已遮蔽的設定快照；後續設定編輯只影響未來嘗試。

每個工作也會儲存僅用於顯示的快照，包含標準化目標金鑰以及可選的作品標題與創作者名稱。即使離線也保持可讀，永遠不影響執行、去重或資源鎖定。佇列列會優先顯示此目標而非輸出路徑，詳細資料、暫停/繼續、停止、編輯、排序與刪除控制則保持直接可見。

![以可讀目標顯示的桌面工作佇列](../assets/webui/21-task-queue-1440-dark-zh.png)

![直接顯示操作的行動工作佇列](../assets/webui/22-task-queue-mobile-light-zh.png)

![深色工作編輯器](../assets/webui/18-task-form-1024-dark-zh.png)

頂層佇列預設執行兩個工作（`KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS`），每個工作仍保留所設定的創作者與檔案並行度。相同的作用中工作會解析為現有工作。標準化輸出、創作者或作品重疊的工作會在 `blocked` 中等待資源鎖釋放。

即時事件使用支援重新連線的 SSE。REST 工作狀態仍是權威來源。詳細檢視會報告已準備創作者、檔案、位元組、總進度、總速度與單檔速度、ETA、略過/失敗數、作用中項目和結構化記錄。

![即時工作進度](../assets/webui/14-task-running-1024-dark-zh.png)

暫停採合作方式：作用中網路串流會關閉，完成檔案與可續傳暫存檔會保留，繼續會建立新嘗試。停止會保留工作定義，以便編輯和重新執行。處理程序重新啟動會將先前執行中的工作標記為 `interrupted`；復原永遠需要明確操作。

刪除工作通常只移除其佇列記錄、嘗試和記錄。「刪除輸出」會先產生檔案與位元組數預覽。確認後只移除記錄為由該工作建立且未變更的一般檔案；符號連結、既有檔案、已修改檔案與共用檔案永遠不會被跟隨或移除。

## WebUI 環境參考

| 變數 | 預設值 | 含義 |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | 監聽介面。 |
| `KTOOLBOX_WEBUI__PORT` | `8789` | 監聽連接埠，1–65535。 |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | 啟動後開啟本機 URL。 |
| `KTOOLBOX_WEBUI__USERNAME` | 空 | 必填的單一帳號使用者名稱。 |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | 空 | 建議使用的 Argon2id 雜湊。 |
| `KTOOLBOX_WEBUI__PASSWORD` | 空 | 純文字備用值；存在雜湊時忽略。 |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | 並行頂層工作數，1–16。 |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | 從最後使用起計算的工作階段存續時間。 |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | 從登入起計算的最長工作階段存續時間。 |

工作歷程很重要時，請一起備份 `ktoolbox.toml`、本機 dotenv 檔案和 `.ktoolbox/webui.sqlite3`。WebUI 執行時不要複製資料庫。
