# KToolBox

KToolBox is an asynchronous command-line downloader, HeroUI project panel, and typed Python client for public [Pawchive](https://pawchive.pw/) data. Version 1 supports Pawchive exclusively and requires Python 3.10 through 3.14.

!!! warning "v1 is a new major version"
    This release line has not yet received enough real-world validation. Begin with a bounded download, keep a backup of existing configuration, and report unexpected behavior. Because Kemono is no longer available, KToolBox uses the Pawchive mirror by default.

## Choose your path

<div class="grid cards" markdown>

-   :material-console-line: **Start with the command line**

    Install KToolBox, run one bounded download, and continue with the [Command Guide](commands/guide.md).

-   :material-view-dashboard-outline: **Manage a project in your browser**

    Install the optional panel and follow the [WebUI Guide](webui.md) for login, security, tasks, and project settings.

-   :material-update: **Upgrade from v0**

    Back up the old dotenv files and follow [Migrating to v1](migration-v1.md) before changing existing downloads.

-   :material-calendar-sync: **Keep creators up to date**

    Build a roster first, then use [Automatic synchronization](automatic-sync.md) for recurring checks.

</div>

## What it does

- Downloads one post or concurrently synchronizes a roster of creators.
- Applies ordered global or creator-scoped blockers before creating download work.
- Resumes partial files and skips files that already exist.
- Filters by date, title, filename pattern, and file size.
- Controls cover, attachment, content image, metadata, and external-link output separately.
- Provides a persistent WebUI in seven languages for project configuration, roster and blocker editing, Pawchive queries, and task lifecycle control.
- Exposes all 14 public Pawchive OpenAPI operations through validated Pydantic models.

Account-authenticated favorites operations are intentionally not implemented. A downloader session key, when configured, is sent only to the file host.

## Install

Using `pipx` keeps the application isolated:

```bash
pipx install ktoolbox
```

Install optional terminal editor and optimized event-loop support:

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

Install the browser panel separately when needed:

```bash
pipx install "ktoolbox[webui]" --force
```

## Quick start

```bash
# Inspect commands and options.
ktoolbox -h
ktoolbox download -h

# Download one post.
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# Start with one post before synchronizing a larger range.
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![KToolBox command overview](../assets/cli-overview.png)

Save multiple creators and synchronize all enabled entries:

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Existing files are skipped on repeat runs. An incomplete file with the configured temporary suffix is resumed when the file server supports byte ranges.

Without `--output`, downloads use the project's default location: `downloads` under the project directory unless you changed it.

## Documentation map

| Goal | Read |
| --- | --- |
| Learn everyday commands | [Command Guide](commands/guide.md) and [Command Reference](commands/reference.md) |
| Run the browser panel | [WebUI Guide](webui.md) |
| Schedule recurring checks | [Automatic synchronization](automatic-sync.md) |
| Control directories and filenames | [Naming format](naming.md) |
| Understand every setting | [Configuration Guide](configuration/guide.md) and [Configuration Reference](configuration/reference.md) |
| Connect another application | [MCP](mcp.md) or [Python API](api.md) |
| Upgrade or solve a problem | [Migrating to v1](migration-v1.md) and [FAQ](faq.md) |
