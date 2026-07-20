# Command Guide

Use hyphenated command and option names. Python Fire also accepts underscores, but hyphens are easier to read.

```bash
ktoolbox -h
ktoolbox sync-creator -h
```

## Download one post

Pass either a Pawchive page URL or the three identity values:

```bash
ktoolbox download-post https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download-post \
  --service=fanbox \
  --creator-id=6570768 \
  --post-id=1836570 \
  --path=downloads
```

Use `--revision-id` to select a revision. KToolBox fetches the revision list and matches the requested ID; Pawchive has no separate single-revision endpoint. Set `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` to include all revisions when downloading the current post.

If a transfer is interrupted, rerun the same command. Completed files are skipped and compatible temporary files are resumed.

## Synchronize a creator

Start with a bounded run when checking a new creator:

```bash
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --length=1
```

Omitting `--length` follows all available pages. `--offset` is a post index at the CLI boundary and may be any non-negative integer; KToolBox converts it into Pawchive's 50-item page offsets.

```bash
# First 10 posts.
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --length=10

# Posts 11 through 15.
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --offset=10 --length=5
```

Filter by inclusive publication dates or case-insensitive title text:

```bash
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 \
  --start-time=2025-01-01 --end-time=2025-03-01

ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 \
  --keywords=preview --keywords-exclude=archive
```

Dates use `%Y-%m-%d`. Enable `--save-creator-indices=True` to write a resumable creator index, or `--mix-posts=True` to place files directly in the creator directory without per-post directories or an index.

## Inspect public data

```bash
# Search the public creator list locally.
ktoolbox search-creator --name=example --service=fanbox

# Search posts for a known creator.
ktoolbox search-creator-post --id=6570768 --service=fanbox --q=preview --o=0

# Validate and print one post model.
ktoolbox get-post fanbox 6570768 1836570
```

Use `--dump=path.json` with search and `get-post` commands to write JSON instead of relying on terminal output.

## Configuration utilities

```bash
ktoolbox config-editor
ktoolbox example-env
ktoolbox version
ktoolbox site-version
```

The editor needs the `urwid` optional dependency. `example-env` renders all configuration fields from the current model.
