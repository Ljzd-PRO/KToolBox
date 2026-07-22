<div align="center">

# KToolBox

An asynchronous CLI, HeroUI management panel, and Python client for downloading public posts from [Pawchive](https://pawchive.pw/).

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

KToolBox v1 uses Pawchive as its only supported backend. It provides typed access to every public operation in the Pawchive OpenAPI document and keeps account-authenticated favorites operations out of scope.

## Features

- Download one post or synchronize any number of creators in one command.
- Keep a reusable, enabled/disabled creator roster in project-local `ktoolbox.toml`.
- Exclude non-work posts with ordered global or creator-scoped field blockers.
- Reuse one typed asynchronous `PawchiveClient` across API operations.
- Resume partial downloads with HTTP Range requests and skip existing files.
- Limit file sizes, select extensions, filter titles and dates, and control cover/attachment downloads.
- Customize directory structure, post names, file names, sequential names, and year/month grouping.
- Save post metadata, creator indices, extracted content, content images, and matching external links.
- Stream jobs from concurrent creator producers into one fair download pool with stable Rich progress, per-file speeds, and aggregate throughput.
- Manage one synchronization project through a bilingual, responsive HeroUI panel with persistent tasks, live progress, configuration forms, roster and blocker editors, and light/dark themes.
- Use a fully offline MockTransport-based test suite; accidental network access is blocked in tests.

## Requirements

- Python 3.10 through 3.14
- Windows, macOS, or Linux

## Installation

Using `pipx` is recommended:

```bash
pipx install ktoolbox
```

Optional event-loop and terminal configuration-editor dependencies:

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

Install the optional WebUI runtime:

```bash
pipx install "ktoolbox[webui]" --force
```

## Quick Start

Show command help:

```bash
ktoolbox -h
ktoolbox download -h
```

![KToolBox command overview](docs/assets/cli-overview.png)

Download one post:

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

Synchronize one creator while limiting the first run to one post:

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

Use an offset, date range, or title filters:

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

Save frequently synchronized creators, then run `sync` without targets:

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Downloaded files are skipped on later runs. Incomplete temporary files are resumed when the file host supports ranges.

## WebUI

The WebUI binds to one directory containing `ktoolbox.toml`. It can start without account settings; each such launch prints the `admin` username and a new random password in the terminal. To keep stable custom credentials, configure a single account, preferably with an Argon2id hash:

```bash
ktoolbox webui hash-password
```

Add the printed hash and account name to the project's `.env`, then start the panel:

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

```bash
ktoolbox webui /path/to/project
```

![KToolBox WebUI configuration](docs/assets/webui/09-configuration-light.png)

Task rows preserve readable post titles and creator names in an offline presentation snapshot. Desktop and mobile layouts expose details, lifecycle, editing, ordering, and deletion actions directly, while form switches use gray-off/blue-on tracks and checkboxes show an indicator only when selected.

Creator profiles supply the primary roster name with a resilient 24-hour cache. Data tables support locale-aware sorting, dashboard statistics link to filtered views, and every platform field uses a HeroUI ComboBox with Patreon, Pixiv, and Fanbox suggestions plus custom values.

The default `0.0.0.0:8789` listener is convenient on a trusted LAN, but HTTP does not protect credentials or project data in transit. Bind to `127.0.0.1` or put the service behind HTTPS for untrusted networks. When credentials are not configured, KToolBox generates credentials for the current process and prints them only in its terminal. Filesystem-backed path fields can browse the computer running KToolBox; project fields stay inside the bound project, while the storage-bucket and log-directory fields use the server process's host permissions. Empty directories can only be removed through an explicit, non-recursive confirmation. See the [WebUI guide](https://ktoolbox.readthedocs.io/latest/webui/) for task lifecycle, security, and deployment details.

## Configuration

KToolBox reads `.env`, then `prod.env`, from the current working directory. Nested fields use `__`:

```dotenv
# Pawchive defaults; normally no override is needed.
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# Download controls.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY`, if set, is sent only to file downloads. The API client never sends an account session.

`.env` controls runtime and transfer behavior. A project-level `ktoolbox.toml` stores the creator roster and blockers:

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["progress update"] }] } }
```

Generate references, validate the project file, or launch the optional terminal editor:

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

See [Configuration](https://ktoolbox.readthedocs.io/latest/configuration/guide/) and [`example.env`](example.env).

## Python API

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

Successful calls return Pydantic v2 models. Transport, HTTP status, authentication, not-found, conflict, and response-validation failures use distinct exception classes. See the [API documentation](https://ktoolbox.readthedocs.io/latest/api/).

## Migrating From v0

v1 removes the Kemono/Coomer compatibility layer and the old `BaseAPI`, module-level `get_*`, `APIRet`, and wrapper-response interfaces. Fire commands were replaced by Cyclopts: use `download`, `sync`, `creator`, `post`, and `config`. Hidden aliases remain temporarily available with a deprecation warning. Move `KTOOLBOX_API__SESSION_KEY` to `KTOOLBOX_DOWNLOADER__SESSION_KEY` and review the [v1 migration guide](https://ktoolbox.readthedocs.io/latest/migration-v1/).

The historical `kemono_openapi.json` remains in the repository for reference only; it is not a supported runtime contract.

## Development

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check k_generator ktoolbox/api ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py tests
poetry run mypy --strict ktoolbox/api/client.py ktoolbox/api/errors.py ktoolbox/api/parameters.py ktoolbox/api/utils.py ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py
poetry run mkdocs build --strict
cd webui && npm ci && npm run typecheck && npm run lint && npm run test && npm run build && npm run test:e2e
```

Default tests are hermetic and must not contact Pawchive or any other remote service.

## License

KToolBox is licensed under the [BSD 3-Clause License](LICENSE).
