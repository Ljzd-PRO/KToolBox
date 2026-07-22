<div align="center">

# KToolBox

用於從 [Pawchive](https://pawchive.pw/) 下載公開作品的非同步命令列工具、HeroUI 管理面板與 Python 用戶端。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/zh-Hant/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

KToolBox v1 僅支援 Pawchive 後端。專案對 Pawchive OpenAPI 文件中的所有公開操作提供型別化存取，並明確排除需要帳號驗證的收藏操作。

## 功能

- 下載單篇作品，或在一條命令中同步任意數量的創作者。
- 在專案層級的 `ktoolbox.toml` 中維護可重複使用、可啟停的創作者清單。
- 使用有順序的全域或創作者層級欄位忽略規則排除非創作類內容。
- 在多個操作間重複使用同一個型別化非同步 `PawchiveClient`。
- 使用 HTTP Range 續傳未完成的檔案，並略過已經存在的檔案。
- 依檔案大小、副檔名、標題關鍵字和發佈日期篩選，可分別控制封面與附件下載。
- 自訂目錄結構、作品目錄名稱、檔案名稱、順序命名和年月分組。
- 儲存作品中繼資料、創作者索引、正文、正文圖片及符合條件的外部連結。
- 將並行創作者產生的工作串流送入公平下載池，並使用顯示單檔速度與總輸送量的穩定 Rich 進度介面。
- 透過英語與簡體中文雙語、響應式 HeroUI 面板管理單一同步專案，提供持久化工作、即時進度、設定表單、創作者與忽略規則編輯，以及明暗主題。
- 預設測試完全離線、以 MockTransport 為基礎，並阻止意外的網路存取。

## 系統需求

- Python 3.10 至 3.14
- Windows、macOS 或 Linux

## 安裝

建議使用 `pipx`：

```bash
pipx install ktoolbox
```

可選的事件迴圈最佳化與終端機設定編輯器相依套件：

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

安裝可選的 WebUI 執行環境：

```bash
pipx install "ktoolbox[webui]" --force
```

## 快速開始

顯示命令說明：

```bash
ktoolbox -h
ktoolbox download -h
```

![KToolBox 命令概覽](docs/assets/cli-overview.png)

下載一篇作品：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

第一次同步創作者時先限制為一篇作品：

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

使用偏移量、日期範圍或標題篩選：

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

儲存經常同步的創作者，之後不帶目標執行 `sync`：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

再次執行時會略過已經下載的檔案；檔案主機支援 Range 時，未完成的暫存檔會繼續下載。

## WebUI

WebUI 固定繫結一個包含 `ktoolbox.toml` 的專案目錄。請設定單一帳號，並優先使用 Argon2id 密碼雜湊：

```bash
ktoolbox webui hash-password
```

將產生的雜湊與帳號名稱寫入專案的 `.env`，然後啟動面板：

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

```bash
ktoolbox webui /path/to/project
```

![KToolBox WebUI 設定](docs/assets/webui/09-configuration-light.png)

工作列會在離線顯示快照中保留可讀的作品標題與創作者名稱。桌面與行動版面配置會直接顯示詳細資料、生命週期、編輯、排序和刪除操作；表單開關採用「關閉灰、開啟藍」，核取方塊則只在真正選取時顯示標記。

預設監聽 `0.0.0.0:8789`，方便在受信任的區域網路中使用，但 HTTP 無法加密傳輸帳號憑證和專案資料。在不受信任的網路中，請繫結 `127.0.0.1` 或置於 HTTPS 反向代理之後。專案沒有預設帳號，未設定有效憑證時會拒絕啟動。工作生命週期、安全措施與部署方式詳見 [WebUI 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/webui/)。

## 設定

KToolBox 會從目前工作目錄依序讀取 `.env` 和 `prod.env`。巢狀欄位使用 `__`：

```dotenv
# Pawchive 預設值，通常不需要覆寫。
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# 下載控制。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

如果設定了 `KTOOLBOX_DOWNLOADER__SESSION_KEY`，它只會傳送給檔案下載請求；API 用戶端永遠不會傳送帳號工作階段。

`.env` 控制執行環境與傳輸行為；專案層級的 `ktoolbox.toml` 儲存創作者清單與忽略規則：

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["進度分享"] }] } }
```

產生設定參考、驗證專案檔案或啟動可選的終端機編輯器：

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

詳見[設定文件](https://ktoolbox.readthedocs.io/latest/zh-Hant/configuration/guide/)與 [`example.env`](example.env)。

## Python API

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

成功呼叫會傳回 Pydantic v2 模型；傳輸、HTTP 狀態、驗證、找不到、衝突和回應驗證失敗分別使用不同的例外類別。詳見 [API 文件](https://ktoolbox.readthedocs.io/latest/zh-Hant/api/)。

## 從 v0 遷移

v1 移除了 Kemono/Coomer 相容層，以及舊的 `BaseAPI`、模組層級 `get_*`、`APIRet` 和包裝回應介面。Fire 命令已由 Cyclopts 取代，請使用 `download`、`sync`、`creator`、`post` 和 `config`；隱藏的舊別名會暫時保留並顯示棄用警告。請將 `KTOOLBOX_API__SESSION_KEY` 移至 `KTOOLBOX_DOWNLOADER__SESSION_KEY`，並閱讀 [v1 遷移指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/migration-v1/)。

儲存庫仍保留歷史 `kemono_openapi.json`，但它只供參考，不再是受支援的執行階段契約。

## 開發

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check k_generator ktoolbox/api ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py tests
poetry run mypy --strict ktoolbox/api/client.py ktoolbox/api/errors.py ktoolbox/api/parameters.py ktoolbox/api/utils.py ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py
poetry run mkdocs build --strict
cd webui && npm ci && npm run typecheck && npm run lint && npm run test && npm run build && npm run test:e2e
```

預設測試必須保持離線，不得存取 Pawchive 或其他遠端服務。

## 授權條款

KToolBox 採用 [BSD 3-Clause License](LICENSE)。
