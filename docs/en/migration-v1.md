# Migrating to v1

KToolBox v1 is a breaking backend and library-API release.

## Before upgrading

1. Back up your `.env` or `prod.env` file.
2. Finish or cancel any running v0 download.
3. Test one bounded creator sync with `--length=1` before a full synchronization.

## Required changes

| v0 behavior | v1 behavior |
| --- | --- |
| Kemono/Coomer endpoints | Pawchive only |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| API and file hosts mixed in API config | API/static hosts in `api`; file host in `downloader` |
| Revision detail request | Fetch revision list, then select by `revision_id` |
| Wrapper responses such as `.data.post` | Typed `Post`, `Revision`, and other Pydantic models directly |

The new defaults are:

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## Library API

The old `BaseAPI`, class invokers, module-level `get_*` functions, `APIRet`, and Kemono response wrappers were removed without compatibility aliases. Use an instantiated asynchronous client:

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

Successful calls return Pydantic v2 models. Failures raise typed `PawchiveError` subclasses; see [API Documentation](api.md).

