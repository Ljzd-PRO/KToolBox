# 遷移至 v1

KToolBox v1 是會破壞相容性的後端與程式庫 API 版本。

## 升級前

1. 備份 `.env` 或 `prod.env` 檔案。
2. 完成或取消任何正在執行的 v0 下載。
3. 完整同步前，先使用 `--length=1` 測試一次有數量限制的創作者同步。

## 必要變更

| v0 行為 | v1 行為 |
| --- | --- |
| Kemono/Coomer 端點 | 僅 Pawchive |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| API 與檔案主機混合在 API 設定中 | API/靜態主機位於 `api`；檔案主機位於 `downloader` |
| 修訂詳細資料請求 | 取得修訂清單，再按 `revision_id` 選擇 |
| `.data.post` 等包裝回應 | 直接傳回型別化 `Post`、`Revision` 和其他 Pydantic 模型 |
| Python Fire 命令介面 | 使用連字號選項與明確結束代碼的 Cyclopts 命令樹 |
| 每次同步一位創作者 | 任意數量的目標或已啟用的專案清單 |
| 僅全域 `keywords_exclude` | 有順序的全域與創作者層級 `field-match` 忽略規則 |

新的預設值如下：

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## CLI 命令

隱藏別名會讓現有自動化暫時維持運作，但每次呼叫都會顯示棄用警告：

| v0 命令 | v1 命令 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

選項顯示為 `--creator-id`，而不是 Python 風格的底線。舊底線拼法仍可由相容別名接受。說明會直接顯示，不再需要退出分頁器。

CLI 失敗現在使用處理程序狀態：`0` 成功、`1` 遠端/創作者/下載失敗、`2` 引數/設定失敗、`130` 中斷。JSON 與表格使用 stdout；進度與記錄使用 stderr。

## 專案清單與忽略規則

只有在需要可重複使用的清單或結構化忽略規則時才建立 `ktoolbox.toml`。缺少此檔案代表有效的空專案。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

將非空的 `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 值移至全域 `field-match` 標題條件。舊設定仍會作為隱含忽略規則生效並顯示警告，但 KToolBox 不會改寫本機檔案。請參閱[設定指南](configuration/guide.md#post-blockers)。

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` 預設為 `4`，用於限制創作者生產者。現有的 `KTOOLBOX_JOB__COUNT` 繼續限制檔案工作者。

## 可選 WebUI

v1 新增 HeroUI 面板；它不會遷移或重複使用歷史實驗性 `webui` 分支。安裝 `ktoolbox[webui]`、選擇專案目錄並設定新的單一帳號。缺少 `ktoolbox.toml` 時會在警告後自動建立；不會建立預設憑證。

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env` 和 `prod.env` 現在是忽略的本機檔案，而不是受版本控制的範例。請將憑證與下載器工作階段保存在其中，以 `example.env` 作為公開範本，並在升級前稽核任何較舊的受追蹤 dotenv 檔案。WebUI 會建立 `.ktoolbox/webui.sqlite3` 和專案鎖；兩者都不會變更 CLI 下載輸出格式。

HTTP 部署風險和持久化工作語意請參閱 [WebUI 指南](webui.md)。

## 程式庫 API

舊的 `BaseAPI`、類別呼叫器、模組層級 `get_*` 函式、`APIRet` 與 Kemono 回應包裝已移除，且沒有相容別名。請使用實例化的非同步用戶端：

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

成功呼叫會傳回 Pydantic v2 模型；失敗會引發型別化的 `PawchiveError` 子類別。請參閱 [API 文件](api.md)。
