<div align="center">

# KToolBox

用於從 [Pawchive](https://pawchive.pw/) 下載公開作品的易用 WebUI、命令列工具與 Python 用戶端。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/zh-Hant/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 是全新大版本，尚未經過足夠廣泛的實際驗證，部分功能仍可能出錯。遇到異常時歡迎回報。
>
> 由於 Kemono 已無法使用，KToolBox 現在預設使用鏡像站 Pawchive。

## 建議從 WebUI 開始

WebUI 是使用 KToolBox 的建議方式。下載作品、同步創作者、自動同步、命名、篩選、進度及專案設定皆可在介面中完成，不必先學習命令或手動編輯設定檔。

1. 安裝含 WebUI 的 KToolBox：

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. 建立專案目錄並啟動：

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. 瀏覽器會自動開啟。使用終端機顯示的使用者名稱與隨機密碼登入。
4. 在「創作者」頁加入創作者，再到「工作」頁建立同步或下載工作。

缺少 `ktoolbox.toml` 時 KToolBox 會自動建立；預設下載至專案中的 `downloads` 目錄。

![KToolBox WebUI 概覽](docs/assets/webui/40-overview-showcase-desktop-light.png)

繼續閱讀簡短的 [WebUI 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/webui/)，或從[文件首頁](https://ktoolbox.readthedocs.io/latest/zh-Hant/)選擇具體操作。

## WebUI 能做什麼

- 下載單篇作品，並行同步多位創作者。
- 管理創作者清單、忽略規則、命名格式及多個自動同步計畫。
- 持久保存工作歷史，顯示即時進度、總速度與重試，並支援暫停、停止、重新執行及安全清理。
- 透過附說明的表單管理專案設定，並在需要時使用檔案路徑選擇器。
- 支援七種介面語言、回應式版面、明暗主題及可選的 NSFW 媒體預覽。
- 提供內建 MCP 服務，可連接 Codex、Claude、Cursor、VS Code 等用戶端。

## 選用設定

首次執行使用自動產生的帳號即可。如需固定密碼，請產生雜湊並寫入專案 `.env`：

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

僅在本機使用時可加入 `--host 127.0.0.1`。內建服務使用 HTTP；遠端存取時請只在可信網路中使用，或設定 HTTPS 反向代理。

## 進階用法

需要指令碼或終端機工作流程時仍可使用命令列：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

命令參數見[命令列指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/commands/guide/)，AI 用戶端連線見 [MCP 指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/mcp/)，程式整合見 [Python API](https://ktoolbox.readthedocs.io/latest/zh-Hant/api/)。

## 從 v0 升級

升級前請備份 `.env`、`prod.env` 與現有下載。WebUI 會偵測舊命名設定，並引導完成設定及目錄轉換。請先閱讀 [v1 遷移指南](https://ktoolbox.readthedocs.io/latest/zh-Hant/migration-v1/)；遷移或工作失敗時可查看[問題排解](https://ktoolbox.readthedocs.io/latest/zh-Hant/faq/)。

## 開發

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

預設測試完全離線，不得存取 Pawchive 或其他遠端服務。

## 授權

KToolBox 採用 [BSD 3-Clause License](LICENSE)。
