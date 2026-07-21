# KToolBox

KToolBox is an asynchronous command-line downloader, HeroUI project panel, and typed Python client for public [Pawchive](https://pawchive.pw/) data. Version 1 supports Pawchive exclusively and requires Python 3.10 through 3.14.

## What it does

- Downloads one post or concurrently synchronizes a roster of creators.
- Applies ordered global or creator-scoped blockers before creating download work.
- Resumes partial files and skips files that already exist.
- Filters by date, title, filename pattern, and file size.
- Controls cover, attachment, content image, metadata, and external-link output separately.
- Provides a persistent, bilingual WebUI for project configuration, roster and blocker editing, Pawchive queries, and task lifecycle control.
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

## Next steps

- [Command guide](commands/guide.md)
- [WebUI guide](webui.md)
- [Configuration guide](configuration/guide.md)
- [Python API](api.md)
- [Migrating to v1](migration-v1.md)
- [FAQ](faq.md)
