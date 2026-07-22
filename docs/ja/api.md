# Python API

`PawchiveClient` はインスタンス化して使う非同期クライアントです。関連するリクエストには 1 つのインスタンスを再利用し、非同期コンテキストマネージャーで閉じてください。

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

成功した JSON 操作は生成済み Pydantic v2 モデルを返します。`get_app_version()` はプレーンテキストを返し、`flag_post()` は成功を示す `201` レスポンスの後に `None` を返します。

## 公開操作

| クライアントメソッド | リクエスト | 結果 |
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

`cookieAuth` で保護された 5 つの OpenAPI 操作、つまりアカウントのお気に入り一覧と、投稿またはクリエイターのお気に入りへの追加・削除は意図的に除外しています。投稿のフラグ操作は公開契約に含まれ、アカウントセッションを使用しません。

## パラメーター検証

- `service`、クリエイター ID、投稿 ID には、空白以外の文字が 1 つ以上必要です。
- 検索クエリを指定する場合は 3 文字以上必要です。
- API オフセットは 0 以上かつ 50 の倍数でなければなりません。
- ファイルハッシュはちょうど 64 桁の 16 進数でなければなりません。
- `None` のオプションのクエリパラメーターはリクエストから省略されます。

無効な値はリクエストを送信する前に Pydantic `ValidationError` を発生させます。

## エラー契約

API 固有のエラーはすべて `PawchiveError` を継承します。

| 例外 | 意味 |
| --- | --- |
| `PawchiveTransportError` | 再試行後も DNS、接続、TLS、タイムアウトのいずれかが失敗 |
| `PawchiveHTTPError` | より具体的な対応がない HTTP エラー |
| `PawchiveAuthenticationError` | HTTP `401` または `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | すでにフラグ済みの投稿を含む HTTP `409` |
| `PawchiveResponseValidationError` | 無効な JSON、またはモデルを満たさないレスポンス |

`is_post_flagged()` は意図的なステータス例外で、`404` を `False` に変換します。リクエストは `Accept: application/json` を使用し、リダイレクトには従わず、トランスポートエラー、`429`、`5xx` のレスポンスだけを再試行します。その他の `4xx` とレスポンス検証エラーは再試行しません。

## モデルとスキーマのずれ

生成済みモデルは `ktoolbox.api.generated` にあり、Pydantic の `extra="allow"` によって未知のレスポンスフィールドを保持します。クライアントはそのフィールドパスを `drift_reporter` に渡します。テレメトリーを統合するときは独自のコールバックを指定できます。

変更していない元の契約は `k_generator/pawchive_openapi.json` です。監査可能な互換性修正は `k_generator/pawchive_openapi.overrides.json` に保存され、`k_generator/pawchive_openapi.normalized.json` と決定的な生成モデルを作成します。
