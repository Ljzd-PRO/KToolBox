# 關於 Pawchive

[Pawchive](https://pawchive.pw/) 是 KToolBox v1 唯一支援的後端。KToolBox 使用其公開 API 尋找創作者和作品，然後從 Pawchive 專用檔案主機下載檔案。

## 預設端點

| 用途 | 預設值 |
| --- | --- |
| 公開 API | `https://pawchive.pw/api/v1` |
| 創作者圖示與橫幅 | `https://pawchive.pw` |
| 作品檔案 | `https://file.pawchive.pw/data/...` |

API 請求永遠不會攜帶帳號工作階段。設定 `downloader.session_key` 後，它只會作為 `session` Cookie 傳送給檔案下載請求。

## 支援的 API 範圍

KToolBox 實作了已發佈 OpenAPI 文件中不需要 `cookieAuth` 的全部 14 個操作：創作者與作品探索、個人資料、公告、贊助卡、連結、作品詳細資料、檔案雜湊搜尋、作品標記狀態與提交、修訂、留言和應用程式版本。

需要登入 Pawchive 帳號的 5 個收藏操作被明確排除。

## 負責任地使用

請遵守適用法律、平台條款、創作者權利與儲存空間限制。第一次測試創作者時，請使用有數量限制的同步（`--length`）與檔案大小限制。
