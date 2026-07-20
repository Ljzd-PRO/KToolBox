# Command Guide

KToolBox uses Cyclopts commands with conventional hyphenated options and Rich help. Help is printed directly and never opens a pager.

```bash
ktoolbox --help
ktoolbox sync --help
```

![KToolBox command overview](../../assets/cli-overview.png)

Global options may appear before or after a command:

```bash
ktoolbox --config ./ktoolbox.toml --plain sync
ktoolbox creator list --json --config ./ktoolbox.toml
```

Use `--verbose` for diagnostic logs, `--quiet` to suppress progress and ordinary logs, `--plain` for stable line-oriented progress, and `--no-color` to retain the interactive layout without ANSI color.

## Download one post

Pass either a Pawchive page URL or the three identity values:

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download \
  --service fanbox \
  --creator-id 6570768 \
  --post-id 1836570 \
  --output downloads
```

Use `--revision-id` to select one revision. KToolBox fetches the revision list and matches that ID because Pawchive has no single-revision detail endpoint. Set `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` to include all revisions when downloading the current post.

Rerun the same command after an interruption. Complete files are skipped and compatible temporary files resume through HTTP Range requests. Explicit `download` does not apply synchronization blockers.

## Synchronize creators

`sync` accepts any number of creator URLs, `service:id` identities, or aliases saved in the project roster:

```bash
# One bounded creator sync.
ktoolbox sync fanbox:123 --length 1

# Multiple creators share one concurrent download pool.
ktoolbox sync fanbox:123 patreon:456 studio-c --length 10
```

Omitting `--length` follows every available page. `--offset` is a post index at the CLI boundary; KToolBox translates it to Pawchive's 50-item page offsets.

```bash
ktoolbox sync fanbox:123 --offset 10 --length 5
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

Each creator is stored as `Creator name [service-creator_id]`. Creator producers run up to `job.creator_concurrency` at once. Their bounded queues feed one fair round-robin scheduler, while `job.count` controls file-transfer concurrency. Downloads begin as soon as the first jobs exist instead of waiting for all creators.

One creator failure does not discard completed work from other creators. Failed creators keep their previous index, and the final command exits with status `1` after printing a summary.

## Maintain a roster

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add https://pawchive.pw/patreon/user/456 --alias studio-b
ktoolbox creator disable studio-b
ktoolbox creator list
ktoolbox creator enable studio-b
ktoolbox creator remove studio-b
```

Run `ktoolbox sync` without targets to synchronize every enabled roster entry. An explicitly named disabled creator still runs. `service:id` identities are unique, aliases are optional and unique, and configuration writes preserve comments.

## Exclude non-work posts

Define ordered field blockers in `ktoolbox.toml`. They can apply globally or only to selected `service:id` creators and can inspect titles, content, tags, file names, IDs, and nested list paths. The first matching blocker excludes the post before detail, revision, metadata, directory, or download work is created.

See the [configuration guide](../configuration/guide.md#post-blockers) for complete examples. `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` remains a deprecated global title blocker for migration only.

## Inspect public data

```bash
ktoolbox creator search --name example --service fanbox
ktoolbox post search --creator-id 6570768 --service fanbox --query preview --offset 0
ktoolbox post show fanbox 6570768 1836570
```

Query commands use compact Rich tables by default. Add `--json` for machine-readable stdout; logs and progress remain on stderr. `--dump path.json` additionally writes validated models to a file.

## Configuration utilities

```bash
ktoolbox config path
ktoolbox config validate
ktoolbox config example
ktoolbox config edit
ktoolbox site-version
```

The editor needs the `urwid` optional dependency. It edits both dotenv settings and the roster/blocker project document, then validates before saving.

## Exit status

| Code | Meaning |
| --- | --- |
| `0` | Command completed successfully. |
| `1` | A remote operation, creator, or file download failed; partial files are retained. |
| `2` | Arguments or configuration are invalid. |
| `130` | The user interrupted the command. |

Expected failures are printed without a Python traceback.
