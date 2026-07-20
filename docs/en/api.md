# Python API

`PawchiveClient` is an instantiated asynchronous client. Reuse one instance for related requests and close it with an asynchronous context manager:

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

Successful JSON operations return generated Pydantic v2 models. `get_app_version()` returns plain text and `flag_post()` returns `None` after a successful `201` response.

## Public operations

| Client method | Request | Result |
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

The five OpenAPI operations protected by `cookieAuth` are deliberately excluded: listing account favorites and adding or removing favorite posts or creators. Post flagging is part of the public contract and does not use an account session.

## Parameter validation

- `service`, creator IDs, and post IDs must contain at least one non-whitespace character.
- Search queries must contain at least three characters when provided.
- API offsets must be non-negative multiples of 50.
- File hashes must be exactly 64 hexadecimal characters.
- Optional query parameters that are `None` are omitted from the request.

Invalid values raise Pydantic `ValidationError` before any request is sent.

## Error contract

All API-specific errors derive from `PawchiveError`:

| Exception | Meaning |
| --- | --- |
| `PawchiveTransportError` | DNS, connection, TLS, or timeout failure after retries |
| `PawchiveHTTPError` | HTTP failure without a more specific mapping |
| `PawchiveAuthenticationError` | HTTP `401` or `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | HTTP `409`, including an already flagged post |
| `PawchiveResponseValidationError` | Invalid JSON or a response that cannot satisfy the model |

`is_post_flagged()` is the one intentional status exception: `404` maps to `False`. Requests use `Accept: application/json`, do not follow redirects, and retry only transport errors, `429`, and `5xx` responses. Other `4xx` responses and response validation failures are never retried.

## Models and schema drift

Generated models live in `ktoolbox.api.generated` and retain unknown response fields through Pydantic's `extra="allow"`. The client reports their field paths through its `drift_reporter`; pass a custom callback when integrating telemetry.

The untouched source contract is `k_generator/pawchive_openapi.json`. Auditable compatibility corrections are stored in `k_generator/pawchive_openapi.overrides.json`, producing `k_generator/pawchive_openapi.normalized.json` and deterministic generated models.
