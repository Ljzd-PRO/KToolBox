# 設定指南

KToolBox 有兩層設定：

- `.env`、`prod.env` 和處理程序變數控制 API、傳輸、命名與全域下載行為。
- `ktoolbox.toml` 儲存專案創作者清單和有順序的作品忽略規則。

KToolBox 會從目前工作目錄依序讀取 `.env` 和 `prod.env`。`prod.env` 的值會覆寫 `.env` 中相同的值，而處理程序環境變數具有最高優先權。

巢狀欄位使用雙底線。例如，`KTOOLBOX_API__TIMEOUT` 對應 `config.api.timeout`。

```dotenv
# Pawchive API 請求。
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# 檔案傳輸。
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# 下載工作。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

所有設定均可省略。預設值請參閱[設定參考](reference.md)。

## 產生或編輯設定

從目前模型產生所有可用的 dotenv 金鑰：

```bash
ktoolbox config example
```

可選的終端機編輯器可查看從設定模型 docstring 解析的欄位說明：

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

可選的 [WebUI](../webui.md) 會透過型別化控制項顯示相同的英語與簡體中文雙語 docstring 說明，並提供最終值來源指示、機密遮蔽、dotenv/TOML 原文編輯、驗證、差異預覽和 ETag 衝突保護。

不開啟編輯器即可查看或驗證專案檔案：

```bash
ktoolbox config path
ktoolbox config validate
```

專案路徑的解析順序為：全域 `--config`、`KTOOLBOX_PROJECT_CONFIG`，最後是 `./ktoolbox.toml`。寫入時使用同一目錄的暫存檔和原子取代；TomlKit 會保留註解。

## 創作者清單

每份專案文件都以 `schema_version = 1` 開頭。創作者依不區分大小寫的 `service:id` 保持唯一；可選別名也必須唯一。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

請使用 `creator add`、`remove`、`enable` 和 `disable`，而不是手動編輯簡單清單項目。不帶目標的 `sync` 使用所有已啟用項目；明確指定的別名或識別值不受 `enabled` 影響。

## 作品忽略規則 {#post-blockers}

忽略規則按 TOML 順序執行，第一個符合項會排除作品。全域規則套用於每位同步的創作者；創作者作用域列出確切的 `service:id` 值。停用的規則仍保留在設定中，但不會執行。

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` 支援遞迴 `any`/`all` 群組，群組或條件都可使用 `negate`。條件支援：

| 運算子 | 行為 |
| --- | --- |
| `contains` | 任一選取的純量包含一個設定值。 |
| `equals` | 任一選取的純量等於一個設定值。 |
| `regex` | 任一選取的純量符合一個規則運算式。模式在設定驗證時編譯。 |
| `exists` | 選取的路徑存在且非 null；設定 `expected = false` 可反轉預期。 |

除非設定 `case_sensitive = true`，否則比較不區分大小寫。安全的點分路徑可包含 `[*]` 清單選取器，例如 `tags[*]`、`file.name` 和 `attachments[*].name`。缺少的路徑不會符合。永遠不會評估 Python 運算式或任意程式碼。

忽略規則會在詳細資料、修訂、目錄、中繼資料或下載工作前評估清單回應。被排除的作品與修訂不會進入創作者索引，也不會列印符合的文字。非同步 `PostBlocker` 介面與登錄機制允許日後加入新規則型別，而無需修改同步協調器。

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 仍可作為已棄用的隱含全域標題包含規則使用。KToolBox 不會自動改寫它；請將其遷移到 `ktoolbox.toml`。

## Pawchive 端點

v1 預設值通常不需要覆寫：

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` 可省略，且只會附加到檔案下載器發出的請求。沒有帳號工作階段支援的 `PawchiveClient` 永遠不會傳送它。

## 集合與路徑

在 dotenv 檔案中，集合與清單使用 JSON 陣列：

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

相對輸出與 Bucket 路徑從工作目錄解析。將附件路徑設為 `./`，可把附件直接放入每個作品目錄：

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 命名範本

作品與檔案範本可使用 `id`、`user`、`service`、`title`、`added`、`published` 和 `edited`。檔案範本中的空 `{}` 代表原始或順序基礎檔名。

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

Python 格式規格精確度（如 `{title:.60}`）適合用來處理檔案系統長度限制。

## 限制下載

大小限制以位元組為單位，並在檔案排入佇列前套用。省略任一變數即可停用該邊界。

```dotenv
# 最小 1 KiB，最大 1 MiB。
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# 只取得作品封面，不下載附件。
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` 控制並行創作者生產者。`KTOOLBOX_JOB__COUNT` 則分別控制所有創作者共用的檔案工作者。
