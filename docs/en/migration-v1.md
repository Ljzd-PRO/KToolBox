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
| Python Fire command surface | Cyclopts command tree with hyphenated options and explicit exit codes |
| One creator per synchronization | Any number of targets or an enabled project roster |
| Global `keywords_exclude` only | Ordered global and creator-scoped `field-match` blockers |

The new defaults are:

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## CLI commands

Hidden aliases keep existing automation running temporarily, but each invocation prints a deprecation warning:

| v0 command | v1 command |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

Options are displayed as `--creator-id`, not Python-style underscores. Old underscore spellings remain accepted by compatibility aliases. Help prints directly and no longer requires quitting a pager.

CLI failures now use process status: `0` success, `1` remote/creator/download failure, `2` argument/configuration failure, and `130` interruption. JSON and tables use stdout; progress and logs use stderr.

## Project roster and blockers

Create `ktoolbox.toml` only when you need a reusable roster or structured blockers. A missing file is a valid empty project.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

Move non-empty `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` values to a global `field-match` title condition. The old setting remains active as an implicit blocker and warns, but KToolBox will not rewrite local files. See the [configuration guide](configuration/guide.md#post-blockers).

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` defaults to `4` and limits creator producers. Existing `KTOOLBOX_JOB__COUNT` continues to limit file workers.

## Optional WebUI

v1 adds a new HeroUI panel; it does not migrate or reuse the historical experimental `webui` branch. Install `ktoolbox[webui]`, make sure the bound directory contains `ktoolbox.toml`, and configure a new single account. No default credentials are created.

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env` and `prod.env` are now ignored local files rather than version-controlled examples. Keep credentials and downloader sessions there, use `example.env` as the public template, and audit any older tracked dotenv file before upgrading. The WebUI creates `.ktoolbox/webui.sqlite3` and a project lock; neither changes CLI download output formats.

See the [WebUI guide](webui.md) for HTTP deployment risks and persistent task semantics.

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
