# 命令指南

KToolBox 使用 Cyclopts 命令、慣例的連字號選項與 Rich 說明。說明會直接列印，永遠不會開啟分頁器。

```bash
ktoolbox --help
ktoolbox sync --help
```

![KToolBox 命令概覽](../../assets/cli-overview.png)

全域選項可放在命令之前或之後：

```bash
ktoolbox --config ./ktoolbox.toml --plain sync
ktoolbox creator list --json --config ./ktoolbox.toml
```

使用 `--verbose` 顯示診斷記錄、`--quiet` 隱藏進度與一般記錄、`--plain` 顯示穩定的逐行進度、`--no-color` 保留互動式版面但移除 ANSI 色彩。

## 下載單篇作品

傳入 Pawchive 頁面 URL，或傳入三個識別值：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download \
  --service fanbox \
  --creator-id 6570768 \
  --post-id 1836570 \
  --output downloads
```

使用 `--revision-id` 選擇一個修訂。因為 Pawchive 沒有單一修訂詳細資料端點，KToolBox 會取得修訂清單並比對該 ID。設定 `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` 可在下載目前作品時包含所有修訂。

中斷後重新執行相同命令。完整檔案會略過，相容的暫存檔則會透過 HTTP Range 請求續傳。明確的 `download` 不會套用同步忽略規則。

## 同步創作者

`sync` 接受任意數量的創作者 URL、`service:id` 識別值或儲存在專案清單中的別名：

```bash
# 一次有數量限制的創作者同步。
ktoolbox sync fanbox:123 --length 1

# 多位創作者共用一個並行下載池。
ktoolbox sync fanbox:123 patreon:456 studio-c --length 10
```

省略 `--length` 會遍歷所有可用頁面。`--offset` 在 CLI 邊界代表作品索引；KToolBox 會將它轉換為 Pawchive 每頁 50 項的偏移量。

```bash
ktoolbox sync fanbox:123 --offset 10 --length 5
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

每位創作者儲存為 `Creator name [service-creator_id]`。最多同時執行 `job.creator_concurrency` 個創作者生產者；其有界佇列會送入一個公平的輪詢排程器，而 `job.count` 控制檔案傳輸並行度。第一批工作出現後就會開始下載，不必等待所有創作者。

一位創作者失敗不會捨棄其他創作者已完成的工作。失敗的創作者保留先前索引，最終命令會在列印摘要後以狀態 `1` 結束。

## 維護清單

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add https://pawchive.pw/patreon/user/456 --alias studio-b
ktoolbox creator disable studio-b
ktoolbox creator list
ktoolbox creator enable studio-b
ktoolbox creator remove studio-b
```

不帶目標執行 `ktoolbox sync`，即可同步清單中所有已啟用項目。明確指定的已停用創作者仍會執行。`service:id` 識別值必須唯一，別名可省略但若提供也必須唯一，寫入設定時會保留註解。

## 排除非創作類作品

在 `ktoolbox.toml` 中定義有順序的欄位忽略規則。規則可全域套用或只套用到選定的 `service:id` 創作者，並可檢查標題、內容、標籤、檔名、ID 和巢狀清單路徑。第一條符合的規則會在建立詳細資料、修訂、中繼資料、目錄或下載工作前排除作品。

完整範例請參閱[設定指南](../configuration/guide.md#post-blockers)。`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 僅為遷移而保留，仍是已棄用的全域標題忽略規則。

## 查看公開資料

```bash
ktoolbox creator search --name example --service fanbox
ktoolbox post search --creator-id 6570768 --service fanbox --query preview --offset 0
ktoolbox post show fanbox 6570768 1836570
```

查詢命令預設使用精簡 Rich 表格。加入 `--json` 可讓 stdout 輸出機器可讀資料；記錄和進度仍使用 stderr。`--dump path.json` 還會將驗證後的模型寫入檔案。

## 設定工具

```bash
ktoolbox config path
ktoolbox config validate
ktoolbox config example
ktoolbox config edit
ktoolbox site-version
```

編輯器需要可選的 `urwid` 相依套件。它會編輯 dotenv 設定與清單/忽略規則專案文件，並在儲存前驗證。

## 執行可選的專案面板

安裝 `ktoolbox[webui]` 並設定帳號後，將面板繫結到專案目錄。若缺少 `ktoolbox.toml`，在終端機警告後會自動建立：

```bash
ktoolbox webui . --host 127.0.0.1
```

面板會將相同的下載、同步、清單、忽略規則、查詢與設定流程呈現為受管理的專案操作，並提供持久化工作進度與控制。監聽網路介面前請先閱讀 [WebUI 指南](../webui.md)。

## 結束狀態

| 代碼 | 含義 |
| --- | --- |
| `0` | 命令成功完成。 |
| `1` | 遠端操作、創作者或檔案下載失敗；保留部分檔案。 |
| `2` | 引數或設定無效。 |
| `130` | 使用者中斷命令。 |

預期內的失敗不會列印 Python 追蹤資訊。
