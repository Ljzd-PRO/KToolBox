# Python API

`PawchiveClient` 是需要实例化的异步客户端。相关请求应复用同一个实例，并通过异步上下文管理器关闭：

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

成功的 JSON 操作会返回生成的 Pydantic v2 模型。`get_app_version()` 返回纯文本；`flag_post()` 收到成功的 `201` 响应后返回 `None`。

## 公开操作

| 客户端方法 | 请求 | 结果 |
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

OpenAPI 中受 `cookieAuth` 保护的 5 个操作明确排除：列出账号收藏，以及添加或删除投稿、作者收藏。投稿标记属于公开契约，不使用账号会话。

## 参数校验

- `service`、作者 ID 和投稿 ID 去除空白后必须非空。
- 提供搜索词时，长度至少为 3 个字符。
- API 偏移量必须非负且为 50 的倍数。
- 文件哈希必须是恰好 64 位十六进制字符。
- 值为 `None` 的可选查询参数不会发送。

非法参数会在发出请求前抛出 Pydantic `ValidationError`。

## 错误契约

所有 API 专用异常均继承自 `PawchiveError`：

| 异常 | 含义 |
| --- | --- |
| `PawchiveTransportError` | 重试后仍发生 DNS、连接、TLS 或超时错误 |
| `PawchiveHTTPError` | 没有更具体映射的 HTTP 错误 |
| `PawchiveAuthenticationError` | HTTP `401` 或 `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | HTTP `409`，包括投稿已经标记 |
| `PawchiveResponseValidationError` | JSON 非法或响应无法通过模型校验 |

`is_post_flagged()` 是唯一有意设置的状态例外：`404` 转换为 `False`。请求携带 `Accept: application/json`，不跟随重定向，并且只重试传输错误、`429` 和 `5xx`。其他 `4xx` 及响应校验错误不会重试。

## 模型与 Schema 漂移

生成模型位于 `ktoolbox.api.generated`，通过 Pydantic 的 `extra="allow"` 保留未知响应字段。客户端会将字段路径交给 `drift_reporter`；集成监控时可传入自定义回调。

未经修改的原始契约为 `k_generator/pawchive_openapi.json`。可审查的兼容修正存放在 `k_generator/pawchive_openapi.overrides.json`，由此生成 `k_generator/pawchive_openapi.normalized.json` 和确定性的模型。
