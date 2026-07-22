# Python API

`PawchiveClient`는 인스턴스를 생성하여 사용하는 비동기 클라이언트입니다. 관련 요청에는 하나의 인스턴스를 재사용하고 비동기 컨텍스트 관리자로 닫으세요.

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

성공한 JSON 작업은 생성된 Pydantic v2 모델을 반환합니다. `get_app_version()`은 일반 텍스트를 반환하고, `flag_post()`는 성공한 `201` 응답 후 `None`을 반환합니다.

## 공개 작업

| 클라이언트 메서드 | 요청 | 결과 |
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

`cookieAuth`로 보호되는 5개의 OpenAPI 작업, 즉 계정 즐겨찾기 목록과 게시물 또는 크리에이터 즐겨찾기의 추가 및 삭제는 의도적으로 제외합니다. 게시물 신고는 공개 계약에 속하며 계정 세션을 사용하지 않습니다.

## 매개변수 검증

- `service`, 크리에이터 ID 및 게시물 ID에는 공백이 아닌 문자가 하나 이상 있어야 합니다.
- 검색어를 제공하는 경우 세 글자 이상이어야 합니다.
- API 오프셋은 0 이상이며 50의 배수여야 합니다.
- 파일 해시는 정확히 64자의 16진수여야 합니다.
- 값이 `None`인 선택적 쿼리 매개변수는 요청에서 생략됩니다.

잘못된 값은 요청을 보내기 전에 Pydantic `ValidationError`를 발생시킵니다.

## 오류 계약

모든 API 전용 오류는 `PawchiveError`에서 파생됩니다.

| 예외 | 의미 |
| --- | --- |
| `PawchiveTransportError` | 재시도 후에도 발생한 DNS, 연결, TLS 또는 시간 초과 오류 |
| `PawchiveHTTPError` | 더 구체적인 매핑이 없는 HTTP 오류 |
| `PawchiveAuthenticationError` | HTTP `401` 또는 `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | 이미 신고된 게시물을 포함한 HTTP `409` |
| `PawchiveResponseValidationError` | 잘못된 JSON 또는 모델을 충족하지 못하는 응답 |

`is_post_flagged()`는 의도적인 상태 예외로, `404`를 `False`로 변환합니다. 요청은 `Accept: application/json`을 사용하고 리디렉션을 따르지 않으며 전송 오류, `429`, `5xx` 응답만 재시도합니다. 다른 `4xx` 응답과 응답 검증 실패는 재시도하지 않습니다.

## 모델과 스키마 변경

생성된 모델은 `ktoolbox.api.generated`에 있으며 Pydantic의 `extra="allow"`를 통해 알 수 없는 응답 필드를 보존합니다. 클라이언트는 해당 필드 경로를 `drift_reporter`로 전달합니다. 원격 측정을 통합할 때 사용자 지정 콜백을 전달할 수 있습니다.

수정하지 않은 원본 계약은 `k_generator/pawchive_openapi.json`입니다. 감사 가능한 호환성 수정은 `k_generator/pawchive_openapi.overrides.json`에 저장되며, 이를 통해 `k_generator/pawchive_openapi.normalized.json`과 결정적 생성 모델을 만듭니다.
