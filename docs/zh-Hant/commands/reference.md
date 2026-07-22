# 命令參考

執行 `ktoolbox COMMAND --help` 查看權威 Cyclopts 說明。命令與選項名稱使用連字號；舊底線拼法仍會由隱藏的相容命令解析。

## 全域選項

| 選項 | 含義 |
| --- | --- |
| `-h`, `--help` | 不透過分頁器，直接列印說明。 |
| `--version` | 列印已安裝的 KToolBox 版本。 |
| `--install-completion` | 為偵測到的 Shell 安裝自動完成。 |
| `--config PATH` | 選擇專案檔案。解析順序為此選項、`KTOOLBOX_PROJECT_CONFIG`，最後是 `./ktoolbox.toml`。 |
| `--verbose` | 包含診斷記錄。 |
| `--quiet` | 隱藏進度與一般記錄。 |
| `--plain` | 強制使用穩定的逐行進度。非 TTY 輸出與 `NO_COLOR` 會自動使用此模式。 |
| `--no-color` | 停用 ANSI 色彩。 |

不帶引數執行 `ktoolbox` 會列印根說明並成功結束。

## 命令樹

| 命令 | 用途 |
| --- | --- |
| `download` | 下載一篇作品或指定修訂。 |
| `sync [TARGET ...]` | 同步明確指定的創作者；未指定目標時同步清單中所有已啟用創作者。 |
| `creator list/add/remove/enable/disable/search` | 管理清單或搜尋 Pawchive 創作者。 |
| `post show/search` | 查看作品或搜尋創作者作品。 |
| `config edit/example/validate/path` | 編輯或查看環境與專案設定。 |
| `site-version` | 列印 Pawchive 應用程式版本。 |
| `webui [PROJECT_DIR]` | 為一個專案執行可選的 HeroUI 面板。 |

## `download`

提供 Pawchive 作品 URL，或同時提供 `--service`、`--creator-id` 和 `--post-id`。

| 引數或選項 | 型別 | 預設值 | 含義 |
| --- | --- | --- | --- |
| `POST` | 字串 | 省略 | Pawchive 作品或修訂 URL。 |
| `--service` | 字串 | 省略 | 創作者服務。 |
| `--creator-id` | 字串 | 省略 | 創作者 ID。 |
| `--post-id` | 字串 | 省略 | 作品 ID。 |
| `--revision-id` | 字串 | 省略 | 從修訂清單選擇此修訂。 |
| `-o`, `--output`, `--path` | 路徑 | `.` | 輸出根目錄。 |
| `--dump-post-data` / `--no-dump-post-data` | 布林值 | 啟用 | 將驗證後的中繼資料儲存到 `post.json`。 |

`download` 有意不套用清單忽略規則。

## `sync`

每個 `TARGET` 可以是 Pawchive 創作者 URL、`service:id` 或清單別名。明確目標即使在清單中停用也會執行；沒有目標時會執行所有已啟用的清單創作者。

| 引數或選項 | 型別 | 預設值 | 含義 |
| --- | --- | --- | --- |
| `TARGET ...` | 字串 | 已啟用清單 | 零位或多位創作者。 |
| `--service` + `--creator-id` | 字串 | 省略 | 加入一位明確創作者；兩者必須同時提供。 |
| `-o`, `--output`, `--path` | 路徑 | `.` | 輸出根目錄。 |
| `--save-creator-indices` | 布林值 | 停用 | 成功生產後以原子方式儲存創作者索引。 |
| `--mix-posts` / `--no-mix-posts` | 布林值 | 環境設定 | 覆寫 `job.mix_posts`。 |
| `--start-time`, `--start` | 日期 | 省略 | 包含端點的發佈日期下限，`YYYY-MM-DD`。 |
| `--end-time`, `--end` | 日期 | 省略 | 包含端點的發佈日期上限，`YYYY-MM-DD`。 |
| `--offset` | 整數 | `0` | 第一篇作品索引。 |
| `--length` | 整數 | 全部 | 每位創作者最多接受的作品數。 |
| `--keywords` | 重複字串 | 環境設定 | 包含標題中含任一值的作品。 |
| `--keywords-exclude` | 重複字串 | 環境設定 | 已棄用的標題排除相容輸入。 |

`job.creator_concurrency` 限制創作者生產，而 `job.count` 限制共用檔案工作者。

## `creator`

| 命令 | 引數與選項 | 含義 |
| --- | --- | --- |
| `creator list` | `--json` | 以 Rich 表格或 JSON 列出清單項目。 |
| `creator add TARGET` | `--alias NAME`, `--disabled` | 加入 URL 或 `service:id`。 |
| `creator remove TARGET` | | 依別名、URL 或識別值移除。 |
| `creator enable TARGET` | | 啟用已儲存的創作者。 |
| `creator disable TARGET` | | 停用已儲存的創作者。 |
| `creator search` | `--name`, `--creator-id`/`--id`, `--service`, `--dump`, `--json` | 篩選公開創作者清單。 |

## `post`

| 命令 | 引數與選項 | 含義 |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`, `--name`, `--service`, `-q`/`--query`, `-o`/`--offset`, `--dump`, `--json` | 搜尋所選創作者的作品。直接 API 查詢至少 3 個字元，API 偏移量須可被 50 整除。 |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`, `--json` | 顯示目前作品中繼資料或一個指定修訂。 |

未使用 `--json` 時，查詢命令會刻意在終端機表格中省略作品正文。

## `config`

| 命令 | 含義 |
| --- | --- |
| `config path` | 列印解析後的專案路徑，不進行換行。 |
| `config validate` | 驗證 Schema 版本、創作者唯一性、忽略規則型別、作用域、條件與規則運算式。 |
| `config example` | 從設定模型 docstring 呈現全部 dotenv 設定。 |
| `config edit` | 開啟可選的 Urwid 編輯器並在儲存前驗證。 |

## `webui`

使用這些命令前請安裝 `ktoolbox[webui]`。預設命令接受專案目錄，若缺少 `ktoolbox.toml`，會在列印警告後建立。未設定帳號時，終端機會輸出本次處理程序使用的 `admin` 使用者名稱和隨機密碼；可透過 WebUI 設定使用固定的自訂憑證。

| 引數或選項 | 預設值 | 含義 |
| --- | --- | --- |
| `PROJECT_DIR` | `.` | 此處理程序服務的固定同步專案。 |
| `--host` | `webui.host` | 覆寫監聽介面。 |
| `--port` | `webui.port` | 覆寫 TCP 連接埠。 |
| `--no-open` | 停用 | 不在預設瀏覽器中開啟本機 URL。 |
| `webui hash-password` | | 透過隱藏的終端機輸入提示兩次，並列印 Argon2id 雜湊。 |

內建伺服器會列印 HTTP 安全警告。將其暴露到 localhost 以外前，請參閱 [WebUI 指南](../webui.md)。

## 相容別名

這些別名不會顯示在說明中，且每次呼叫會發出一次棄用警告：

| 舊名稱 | 替代名稱 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## 結束代碼與串流

| 代碼 | 含義 |
| --- | --- |
| `0` | 成功。 |
| `1` | 遠端、創作者或下載失敗，包括多創作者的部分成功。 |
| `2` | 引數或設定無效。 |
| `130` | 使用者中斷。 |

表格與 JSON 使用 stdout。記錄、進度、警告和錯誤使用 stderr。
