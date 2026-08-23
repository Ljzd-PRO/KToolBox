# KToolBox

KToolBox 是面向 [Pawchive](https://pawchive.pw/) 公開資料的非同步命令列下載器、HeroUI 專案面板和型別化 Python 用戶端。v1 僅支援 Pawchive，需要 Python 3.10 至 3.14。

!!! warning "v1 是全新大版本"
    此發佈線尚未經過充分的實際使用驗證。請先進行有範圍限制的下載、備份既有設定，並回報非預期行為。由於 Kemono 已無法使用，KToolBox 預設使用 Pawchive 鏡像站。

## 選擇你的使用路徑

<div class="grid cards" markdown>

-   :material-console-line: **從命令列開始**

    安裝 KToolBox，先執行一次有範圍限制的下載，再閱讀[命令指南](commands/guide.md)。

-   :material-view-dashboard-outline: **在瀏覽器中管理專案**

    安裝選用面板，並依照 [WebUI 指南](webui.md)完成登入、安全設定、任務與專案設定。

-   :material-update: **從 v0 升級**

    先備份舊 dotenv 檔案，再依照[遷移至 v1](migration-v1.md)處理既有下載。

-   :material-calendar-sync: **持續更新創作者內容**

    先建立創作者清單，再透過[自動同步](automatic-sync.md)安排週期檢查。

</div>

## 功能

- 下載單篇作品，或並行同步創作者清單。
- 在建立下載工作前套用有順序的全域或創作者層級忽略規則。
- 續傳未完成的檔案，並略過已經存在的檔案。
- 依日期、標題、檔名模式和檔案大小篩選。
- 分別控制封面、附件、正文圖片、中繼資料和外部連結輸出。
- 提供支援七種語言的持久化 WebUI，用於管理專案設定、創作者清單、忽略規則、Pawchive 查詢與工作生命週期。
- 透過經過驗證的 Pydantic 模型提供 Pawchive OpenAPI 的全部 14 個公開操作。

需要帳號驗證的收藏操作明確不予實作。下載器工作階段金鑰即使設定，也只會傳送到檔案主機。

## 安裝

建議使用 `pipx` 隔離安裝：

```bash
pipx install ktoolbox
```

安裝可選的終端機設定編輯器和事件迴圈最佳化支援：

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

需要時另行安裝瀏覽器面板：

```bash
pipx install "ktoolbox[webui]" --force
```

## 快速開始

```bash
# 查看命令和選項。
ktoolbox -h
ktoolbox download -h

# 下載單篇作品。
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# 先從一篇作品開始，再按需要同步更大範圍。
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![KToolBox 命令概覽](../assets/cli-overview.png)

儲存多位創作者並同步所有已啟用項目：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

重複執行時會略過現有檔案。若檔案伺服器支援位元組範圍請求，帶有已設定暫存副檔名的未完成檔案會繼續下載。

未指定 `--output` 時，下載會使用專案預設目錄；未修改設定時就是專案目錄下的 `downloads`。

## 文件地圖

| 目標 | 閱讀 |
| --- | --- |
| 學習日常命令 | [命令指南](commands/guide.md)與[命令參考](commands/reference.md) |
| 執行瀏覽器面板 | [WebUI 指南](webui.md) |
| 安排週期檢查 | [自動同步](automatic-sync.md) |
| 控制目錄與檔名 | [命名格式](naming.md) |
| 理解所有設定 | [設定指南](configuration/guide.md)與[設定參考](configuration/reference.md) |
| 連接其他應用程式 | [MCP](mcp.md)或 [Python API](api.md) |
| 升級或排解問題 | [遷移至 v1](migration-v1.md)與[常見問題](faq.md) |
