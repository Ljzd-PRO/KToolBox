# 設定參考

環境變數名稱以 `KTOOLBOX_` 開頭，並以 `__` 連接巢狀模型欄位。顯示為 `path`、`set` 或 `list` 的型別由 Pydantic 解析；dotenv 檔案中的集合請使用 JSON 陣列。

## 根層級

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `ssl_verify` | 布林值 | `True` | 驗證 API 與下載請求的 TLS 憑證。 |
| `json_dump_indent` | 整數 | `4` | JSON 輸出的縮排。 |
| `use_uvloop` | 布林值 | `True` | 已安裝時，在 Unix 使用 uvloop、Windows 使用 winloop。 |

## `api`

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | API URL 配置。 |
| `netloc` | 字串 | `pawchive.pw` | API 主機。 |
| `statics_netloc` | 字串 | `pawchive.pw` | 靜態創作者資源主機。 |
| `path` | 字串 | `/api/v1` | API 根路徑。 |
| `timeout` | 浮點數 | `5.0` | 每個請求的逾時秒數。 |
| `retry_times` | 整數 | `3` | 傳輸、`429` 與 `5xx` 失敗後的額外嘗試次數。 |
| `retry_interval` | 浮點數 | `2.0` | API 嘗試之間的延遲秒數。 |

API 群組刻意不包含工作階段金鑰。

## `downloader`

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | 檔案 URL 配置。 |
| `files_netloc` | 字串 | `file.pawchive.pw` | Pawchive 檔案主機。 |
| `file_path_prefix` | 字串 | `/data` | 加在 API 檔案路徑前的前綴。 |
| `session_key` | 字串 | 空 | 只傳送到檔案請求的可選 Cookie。 |
| `timeout` | 浮點數 | `30.0` | 檔案請求逾時秒數。 |
| `encoding` | 字串 | `utf-8` | 名稱和擷取文字的編碼。 |
| `buffer_size` | 整數 | `20480` | 緩衝檔案 I/O 大小（位元組）。 |
| `chunk_size` | 整數 | `1024` | 串流區塊大小（位元組）。 |
| `temp_suffix` | 字串 | `tmp` | 未完成下載的副檔名。 |
| `retry_times` | 整數 | `10` | 額外下載嘗試次數。 |
| `retry_stop_never` | 布林值 | `False` | 永遠重試並忽略 `retry_times`。 |
| `retry_interval` | 浮點數 | `3.0` | 下載嘗試間的延遲秒數。 |
| `tps_limit` | 浮點數 | `5.0` | 每秒新連線數上限。 |
| `use_bucket` | 布林值 | `False` | 啟用內容定址的本機硬連結儲存。 |
| `bucket_path` | 路徑 | `.ktoolbox/bucket_storage` | 本機 Bucket 目錄。 |
| `reverse_proxy` | 字串 | `{}` | 下載 URL 範本；`{}` 會替換成來源 URL。 |
| `keep_metadata` | 布林值 | `True` | 可用時保留遠端修改中繼資料。 |

目標檔案系統無法建立硬連結時，Bucket 模式會自行停用。

## `job.post_structure`

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `attachments` | 路徑 | `attachments` | 附件子目錄。使用 `./` 代表作品根目錄。 |
| `content` | 路徑 | `content.txt` | 擷取的正文檔案。 |
| `external_links` | 路徑 | `external_links.txt` | 擷取的外部連結檔案。 |
| `file` | 字串 | `{id}_{}` | 封面檔案命名範本。 |
| `revisions` | 路徑 | `revisions` | 修訂子目錄。 |

## `job`

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `count` | 整數 | `4` | 並行下載工作者。 |
| `creator_concurrency` | 整數 | `4` | 向共用檔案工作者供應工作的並行創作者生產者。 |
| `include_revisions` | 布林值 | `False` | 包含目前作品的所有已知修訂。 |
| `post_dirname_format` | 字串 | `{title}` | 每篇作品的目錄範本。 |
| `mix_posts` | 布林值 | `False` | 不使用作品目錄，將所有創作者檔案儲存在一起。 |
| `sequential_filename` | 布林值 | `False` | 依數字順序重新命名附件。 |
| `sequential_filename_excludes` | 集合 | 空 | 保留原始名稱的副檔名。 |
| `filename_format` | 字串 | `{}` | 附件檔名範本。 |
| `allow_list` | 集合 | 空 | 要包含的 Unix Shell 檔名模式。 |
| `block_list` | 集合 | 空 | 要排除的 Unix Shell 檔名模式。 |
| `extract_content` | 布林值 | `False` | 另行儲存作品文字。 |
| `extract_content_images` | 布林值 | `False` | 下載作品內容中引用的圖片。 |
| `extract_external_links` | 布林值 | `False` | 儲存內容中符合條件的外部連結。 |
| `external_link_patterns` | 清單 | 內建 | 用於擷取外部連結的規則運算式。 |
| `group_by_year` | 布林值 | `False` | 依發佈年份分組作品目錄。 |
| `group_by_month` | 布林值 | `False` | 依月份分組；需要先按年份分組。 |
| `year_dirname_format` | 字串 | `{year}` | 年份目錄範本。 |
| `month_dirname_format` | 字串 | `{year}-{month:02d}` | 月份目錄範本。 |
| `keywords` | 集合 | 空 | 不區分大小寫、要包含的標題詞彙。 |
| `keywords_exclude` | 集合 | 空 | 已棄用的標題排除，會轉換為隱含的全域忽略規則。 |
| `download_file` | 布林值 | `True` | 下載主要作品檔案，通常是封面。 |
| `download_attachments` | 布林值 | `True` | 下載附件。 |
| `min_file_size` | 整數 / 省略 | 省略 | 略過小於此位元組數的檔案。 |
| `max_file_size` | 整數 / 省略 | 省略 | 略過大於此位元組數的檔案。 |

命名範本接受 `id`、`user`、`service`、`title`、`added`、`published` 和 `edited`。年與月範本接受 `year` 和 `month`。

## 專案 `ktoolbox.toml`

專案文件與環境設定分開。其路徑依序從全域 `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml` 解析。

### 根層級

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `schema_version` | 常值 `1` | `1` | 專案 Schema 版本；其他值會被拒絕。 |
| `creators` | 表格陣列 | 空 | 已儲存的創作者清單。 |
| `blockers` | 表格陣列 | 空 | 有順序的忽略規則規格。 |

### 創作者項目

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `service` | 非空字串 | 必填 | Pawchive 服務。 |
| `creator_id` | 非空字串 | 必填 | Pawchive 創作者 ID。 |
| `alias` | 字串 / 省略 | 省略 | 唯一的 CLI 目標；禁止使用 `:`。 |
| `enabled` | 布林值 | `True` | 是否由不帶目標的 `sync` 包含。 |

### 忽略規則項目

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `id` | 識別碼 | 必填 | 由字母、數字、`.`、`_` 或 `-` 組成的唯一 ID。 |
| `type` | 字串 | `field-match` | 已登錄的規則實作。未知型別會被拒絕。 |
| `enabled` | 布林值 | `True` | 此規則是否參與評估。 |
| `scope.mode` | `global` / `creators` | `global` | 全域套用或套用到所選識別值。 |
| `scope.creators` | `service:id` 清單 | 空 | 創作者作用域必填且非空；全域作用域禁止使用。 |
| `options.rule` | 條件群組 | `field-match` 必填 | 根遞迴規則。 |

條件群組使用 `kind = "group"`、`mode = "any"` 或 `"all"`、非空 `conditions` 清單，以及可選的 `negate`。欄位條件使用 `kind = "field"`、安全的點分 `field`、`contains`、`equals`、`regex` 或 `exists` 之一，以及可選的 `case_sensitive`、`negate` 或 `expected`。非 `exists` 運算子需要非空 `values` 清單；`exists` 禁止 `values`。

## `webui`

只有安裝 `ktoolbox[webui]` 時才需要這些設定。沒有預設憑證，未提供使用者名稱與任一密碼形式時，伺服器會拒絕啟動。

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `host` | 字串 | `0.0.0.0` | HTTP 監聽介面。受信任的 LAN 以外建議使用 `127.0.0.1`。 |
| `port` | 整數 | `8789` | HTTP 監聽連接埠，範圍 1 至 65535。 |
| `open_browser` | 布林值 | `True` | 啟動後開啟本機面板 URL。 |
| `username` | 字串 | 空 | 單一帳號的必填使用者名稱。 |
| `password_hash` | 機密字串 | 空 | 建議使用的 Argon2id 密碼雜湊。 |
| `password` | 機密字串 | 空 | 純文字備用值；設定 `password_hash` 時會忽略。 |
| `max_active_tasks` | 整數 | `2` | 並行頂層工作數，範圍 1 至 16。 |
| `session_idle_hours` | 整數 | `24` | 從最後一次使用起計算的工作階段到期時間。 |
| `session_absolute_hours` | 整數 | `168` | 從登入起計算的最長工作階段存續時間。 |

所有名稱都使用一般前綴，例如 `KTOOLBOX_WEBUI__PASSWORD_HASH`。使用 `ktoolbox webui hash-password` 產生雜湊；Argon2 雜湊包含 `$` 字元，因此請在 dotenv 檔案中加上引號。命令列的 `--host`、`--port` 和 `--no-open` 會在單次啟動中覆寫對應設定。

## `logger`

| 欄位 | 型別 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `path` | 路徑 / 省略 | 省略 | 記錄檔路徑；省略會停用檔案記錄。 |
| `level` | 字串 / 整數 | `DEBUG` | 最低記錄層級。 |
| `rotation` | 字串 / 整數 / 時間 | `1 week` | Loguru 輪替條件。 |
