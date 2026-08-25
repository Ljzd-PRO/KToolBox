<div align="center">

# KToolBox

An easy-to-use WebUI, CLI, and Python client for downloading public works from [Pawchive](https://pawchive.pw/).

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 is a new major version and has not yet received enough real-world validation. Some features may still fail. Please report anything unexpected.
>
> Kemono is no longer available, so KToolBox now uses the Pawchive mirror by default.

## Start with the WebUI

The WebUI is the recommended way to use KToolBox. It covers downloads, creator synchronization, automatic schedules, naming, filters, progress, and project configuration without requiring you to edit commands or configuration files first.

1. Install KToolBox with the WebUI:

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. Create a project directory and start it:

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. The browser opens automatically. Sign in with the username and random password printed in the terminal.
4. Add creators on **Creators**, then create a synchronization or download task on **Tasks**.

KToolBox creates `ktoolbox.toml` when it is missing and downloads to the project's `downloads` directory by default.

![KToolBox WebUI overview](docs/assets/webui/40-overview-showcase-desktop-light.png)

Read the short [WebUI guide](https://ktoolbox.readthedocs.io/latest/webui/) for the next steps, or open the [documentation home](https://ktoolbox.readthedocs.io/latest/) to choose a specific workflow.

## What the WebUI includes

- Single-work downloads and concurrent synchronization of many creators.
- A reusable creator roster, filters, naming templates, and automatic synchronization plans.
- Persistent task history, live progress, aggregate speed, retries, pause, stop, rerun, and safe cleanup.
- Project-level settings with readable descriptions and filesystem pickers where appropriate.
- Seven interface languages, responsive layouts, light and dark themes, and optional NSFW media previews.
- A built-in MCP service for Codex, Claude, Cursor, VS Code, and compatible clients.

## Optional setup

The generated login is convenient for a first run. For a stable password, generate a hash and add it to the project's `.env`:

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

For local-only access, start with `--host 127.0.0.1`. The built-in server uses HTTP, so use a trusted network or an HTTPS reverse proxy for remote access.

## Advanced use

The command line remains available for scripts and terminal workflows:

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

See the [CLI guide](https://ktoolbox.readthedocs.io/latest/commands/guide/) for commands, the [MCP guide](https://ktoolbox.readthedocs.io/latest/mcp/) for AI clients, and the [Python API guide](https://ktoolbox.readthedocs.io/latest/api/) for integrations.

## Upgrading from v0

Back up `.env`, `prod.env`, and existing downloads before upgrading. WebUI detects legacy naming settings and guides you through configuration and directory conversion. Read the [v1 migration guide](https://ktoolbox.readthedocs.io/latest/migration-v1/) before changing an existing project; see [troubleshooting](https://ktoolbox.readthedocs.io/latest/faq/) if a migration or task fails.

## Development

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

Default tests are offline and must not contact Pawchive or any other remote service.

## License

KToolBox is licensed under the [BSD 3-Clause License](LICENSE).
