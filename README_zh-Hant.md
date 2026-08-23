<div align="center">

# KToolBox

用於從 [Pawchive](https://pawchive.pw/) 下載公開作品的非同步命令列工具、HeroUI 管理面板與 Python 用戶端。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/zh-Hant/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> **新大版本預覽：** 目前版本尚未經過充分的實際驗證，部分功能可能無法正常運作，但仍可嘗試使用；如遇到問題，歡迎回報。
>
> 由於 Kemono 網站已無法使用，本專案現在預設支援其鏡像站 Pawchive。
>
> 升級前請閱讀 [v1.0.0 發行說明](https://github.com/Ljzd-PRO/KToolBox/releases/tag/v1.0.0)與文件站中的[遷移指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/migration-v1/)。

**文件導覽：** [開始使用](https://ktoolbox.readthedocs.io/latest/zh-Hant/) · [命令列](https://ktoolbox.readthedocs.io/latest/zh-Hant/commands/guide/) · [WebUI](https://ktoolbox.readthedocs.io/latest/zh-Hant/webui/) · [版本遷移](https://ktoolbox.readthedocs.io/latest/zh-Hant/migration-v1/) · [問題排解](https://ktoolbox.readthedocs.io/latest/zh-Hant/faq/)

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
- 透過支援七種語言的響應式 HeroUI 面板管理單一同步專案，提供持久化工作、即時進度、設定表單、創作者與忽略規則編輯，以及明暗主題。
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

WebUI 固定繫結一個包含 `ktoolbox.toml` 的專案目錄。啟動時可以不設定帳號；此時終端機會輸出本次處理程序使用的 `admin` 帳號和新隨機密碼。如需固定憑證，請優先使用 Argon2id 密碼雜湊：

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

![KToolBox 全域設定](docs/assets/webui/30-global-configuration-log-level-light.png)

完整介面支援簡體中文、繁體中文、英語、日語、韓語、法語和俄語。首次使用會跟隨瀏覽器語言；手動選擇會持久保存，並同步切換日期、數字、排序、設定說明、表單驗證和伺服器錯誤訊息。

工作列會在離線顯示快照中保留可讀的作品標題與創作者名稱。桌面與行動版面配置會直接顯示詳細資料、生命週期、編輯、排序和刪除操作；表單開關採用「關閉灰、開啟藍」，核取方塊則只在真正選取時顯示標記。

「全域設定」頁會依欄位語意使用 Select 或 ComboBox，只對真正的位置欄位提供路徑選擇器。已完成同步工作可沿用原記錄「重新執行」；刪除確認顯示可讀目標與可展開的相對檔案預覽，不再揭露內部 UUID。「關於」頁集中顯示版本、授權、執行環境及官方連結，URL 與監聽位址統一使用行內程式碼樣式。

命名設定與預設下載位置均屬於個別專案。「命名格式」頁分別儲存目錄結構與命名範本；相對輸出位置以專案為基準，也支援專案外的主機絕對路徑。可隨時使用的「舊下載目錄轉換」支援多選專案歷程版本，或在高亮編輯器貼上舊 `.env`/TOML；目前專案格式始終是唯讀目標，貼上的原文不會持久化。掃描後的移動支援暫停、繼續或復原。偵測到舊 dotenv 命名鍵時，WebUI 會先要求確認具有備份的設定遷移，且不會自動掃描目錄。請參閱[命名格式指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/naming/)。

「自動同步」頁可建立多個 Cron 或固定間隔的作者同步計畫，預覽未來三次執行時間、暫停或立即執行，並依作者獨立推進成功檢查點。最近更新只彙總作者與新增作品數量，不載入標題或媒體。請參閱[自動同步指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/automatic-sync/)。

可選 NSFW 預覽預設關閉，且只作為目前瀏覽器的顯示偏好儲存。開啟時必須確認，作者頭像、橫幅、作品封面與支援的圖片附件只會透過已登入驗證的同源代理載入；代理會驗證解碼後的點陣圖，並拒絕重新導向、SVG、非圖片、損毀或超限資源。請參閱 [WebUI 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/webui/#可選敏感媒體預覽)。

失敗工作會保留依階段分類且已脫敏的報告，顯示對應創作者或檔案、是否適合重試、安全欄位路徑及處理建議。精簡行動版採用 64px 頂列和 12px 頁面間距，將外觀控制收納至小型 Popover，並依類別摺疊 MCP 工具目錄。

登入後只會建立一個 SSE 連線，自動在分頁之間同步工作、創作者、忽略規則、設定、MCP 權杖和目前開啟的遠端目錄。連線中斷時，本機資料會改為每 10 秒降級重新整理，不會輪詢 Pawchive 搜尋或作品詳細資料；未儲存的表單草稿也不會被外部更新覆寫。

預設監聽 `0.0.0.0:8789`，方便在受信任的區域網路中使用，但 HTTP 無法加密傳輸帳號憑證和專案資料。在不受信任的網路中，請繫結 `127.0.0.1` 或置於 HTTPS 反向代理之後。未設定憑證時，KToolBox 只在目前處理程序中產生並透過終端機顯示憑證。工作生命週期、安全措施與部署方式詳見 [WebUI 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/webui/)。

## MCP

啟動 WebUI 時也會在 `/mcp` 啟動經過篩選的 Streamable HTTP MCP 服務；需要登入的 WebUI REST OpenAPI YAML 位於 `/api/v1/openapi.yaml`。登入後開啟 **MCP** 頁面，再次確認目前帳號密碼即可建立唯讀或管理權杖。權杖明文只顯示一次，並可隨時撤銷。

Codex 設定範例：

```toml
[mcp_servers.ktoolbox]
url = "http://127.0.0.1:8789/mcp"
bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"
```

頁面也提供通用 HTTP、Claude、Cursor 和 VS Code 設定。權限、回傳上限與 HTTPS 建議請參閱 [MCP 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/mcp/)。

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

`.env` 控制執行環境與傳輸行為；專案層級的 `ktoolbox.toml` 儲存命名格式、創作者清單、自動同步計畫與忽略規則：

```toml
schema_version = 5

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
