# Python API

`PawchiveClient` 是需要實例化的非同步用戶端。相關請求應重複使用同一個實例，並透過非同步內容管理器關閉：

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

成功的 JSON 操作會傳回產生的 Pydantic v2 模型。`get_app_version()` 傳回純文字；`flag_post()` 收到成功的 `201` 回應後傳回 `None`。

## 公開操作

| 用戶端方法 | 請求 | 結果 |
| --- | --- | --- |
| `list_creators()` | `GET /creators` | `list[CreatorSummary]` |
| `list_recent_posts(query=None, offset=None)` | `GET /posts` | `list[Post]` |
| `get_creator_profile(service, creator_id)` | `GET /{service}/user/{creator_id}/profile` | `CreatorProfile` |
| `list_creator_posts(service, creator_id, query=None, offset=None)` | `GET /{service}/user/{creator_id}` | `list[Post]` |
| `list_announcements(service, creator_id)` | `GET /{service}/user/{creator_id}/announcements` | `list[Announcement]` |
| `list_fancards(service, creator_id)` | `GET /{service}/user/{creator_id}/fancards` | `list[Fancard]` |
| `list_creator_links(service, creator_id)` | `GET /{service}/user/{creator_id}/links` | `list[CreatorProfile]` |
| `get_post(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}` | `Post` |
| `search_file_by_hash(file_hash)` | `GET /search_hash/{file_hash}` | `FileSearchResult` |
| `flag_post(service, creator_id, post_id)` | `POST /{service}/user/{creator_id}/post/{post_id}/flag` | `None` |
| `is_post_flagged(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/flag` | `bool` |
| `list_post_revisions(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/revisions` | `list[Revision]` |
| `list_post_comments(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/comments` | `list[Comment]` |
| `get_app_version()` | `GET /app_version` | `str` |

OpenAPI 中受 `cookieAuth` 保護的 5 個操作被明確排除：列出帳號收藏，以及新增或移除作品、創作者收藏。作品標記屬於公開契約，不使用帳號工作階段。

## 參數驗證

- `service`、創作者 ID 和作品 ID 去除空白後必須非空。
- 提供搜尋字詞時，長度至少為 3 個字元。
- API 偏移量必須為非負的 50 倍數。
- 檔案雜湊必須正好是 64 位十六進位字元。
- 值為 `None` 的可選查詢參數不會傳送。

無效參數會在送出請求前引發 Pydantic `ValidationError`。

## 錯誤契約

所有 API 專用錯誤均繼承自 `PawchiveError`：

| 例外 | 含義 |
| --- | --- |
| `PawchiveTransportError` | 重試後仍發生 DNS、連線、TLS 或逾時錯誤 |
| `PawchiveHTTPError` | 沒有更具體對應的 HTTP 錯誤 |
| `PawchiveAuthenticationError` | HTTP `401` 或 `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | HTTP `409`，包括作品已經標記 |
| `PawchiveResponseValidationError` | JSON 無效或回應無法通過模型驗證 |

`is_post_flagged()` 是唯一有意設定的狀態例外：`404` 轉換為 `False`。請求會攜帶 `Accept: application/json`，不跟隨重新導向，並且只重試傳輸錯誤、`429` 和 `5xx` 回應。其他 `4xx` 與回應驗證錯誤永遠不會重試。

## 模型與 Schema 漂移

產生的模型位於 `ktoolbox.api.generated`，透過 Pydantic 的 `extra="allow"` 保留未知回應欄位。用戶端會將其欄位路徑交給 `drift_reporter`；整合遙測時可傳入自訂回呼。

未經修改的來源契約是 `k_generator/pawchive_openapi.json`。可稽核的相容性修正儲存在 `k_generator/pawchive_openapi.overrides.json`，由此產生 `k_generator/pawchive_openapi.normalized.json` 與確定性的產生模型。
