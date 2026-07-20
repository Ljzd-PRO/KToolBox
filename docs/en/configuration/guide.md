# Configuration Guide

KToolBox has two configuration layers:

- `.env`, `prod.env`, and process variables control API, transfer, naming, and global download behavior.
- `ktoolbox.toml` stores a project creator roster and ordered post blockers.

KToolBox reads `.env`, then `prod.env`, from the current working directory. Values from `prod.env` override matching values from `.env`, while process environment variables have the highest priority.

Nested fields use a double underscore. For example, `KTOOLBOX_API__TIMEOUT` maps to `config.api.timeout`.

```dotenv
# Pawchive API requests.
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# File transfers.
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# Download jobs.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

All settings are optional. See the [configuration reference](reference.md) for defaults.

## Generate or edit configuration

Generate every available dotenv key from the current model:

```bash
ktoolbox config example
```

The optional terminal editor can inspect field descriptions parsed from the configuration model docstrings:

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

Inspect or validate the project file without opening the editor:

```bash
ktoolbox config path
ktoolbox config validate
```

The project path resolves in this order: global `--config`, `KTOOLBOX_PROJECT_CONFIG`, then `./ktoolbox.toml`. Writes use a same-directory temporary file and atomic replacement; TomlKit preserves comments.

## Creator roster

Every project document starts with `schema_version = 1`. Creators are unique by case-insensitive `service:id`; optional aliases are also unique.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

Use `creator add`, `remove`, `enable`, and `disable` instead of editing simple roster entries by hand. `sync` without targets uses all enabled entries; explicit aliases or identities run regardless of `enabled`.

## Post blockers {#post-blockers}

Blockers run in TOML order, and the first match excludes the post. A global blocker applies to every synchronized creator; a creator scope lists exact `service:id` values. Disabled blockers remain configured but do not run.

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` supports recursive `any`/`all` groups and `negate` on either a group or condition. Conditions support:

| Operator | Behavior |
| --- | --- |
| `contains` | Any selected scalar contains one configured value. |
| `equals` | Any selected scalar equals one configured value. |
| `regex` | Any selected scalar matches one regular expression. Patterns compile during configuration validation. |
| `exists` | The selected path exists and is not null; set `expected = false` to invert that expectation. |

Comparisons are case-insensitive unless `case_sensitive = true`. Safe dotted paths may include `[*]` list selectors, for example `tags[*]`, `file.name`, and `attachments[*].name`. Missing paths do not match. Python expressions and arbitrary code are never evaluated.

Blockers evaluate the list response before detail, revision, directory, metadata, or download work. Excluded posts and revisions do not enter the creator index, and matching text is not printed. The asynchronous `PostBlocker` interface and registry allow future blocker types without changing the synchronization coordinator.

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` remains accepted as a deprecated implicit global title-contains blocker. KToolBox does not rewrite it automatically; migrate it into `ktoolbox.toml`.

## Pawchive endpoints

The v1 defaults normally require no override:

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` is optional and is attached only to requests made by the file downloader. It is never sent by `PawchiveClient`, which has no account-session support.

## Collections and paths

Use JSON arrays for sets and lists in dotenv files:

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

Relative output and bucket paths are resolved from the working directory. Set the attachments path to `./` to place attachments directly in each post directory:

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## Naming templates

Post and file templates can use `id`, `user`, `service`, `title`, `added`, `published`, and `edited`. The empty `{}` in a file template represents the original or sequential base filename.

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

Python format-spec precision, such as `{title:.60}`, is useful for filesystem length limits.

## Limit downloads

Size limits are bytes and apply before a file is queued. Omit either variable to disable that boundary.

```dotenv
# 1 KiB minimum and 1 MiB maximum.
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# Fetch only the post cover, not attachments.
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` controls concurrent creator producers. `KTOOLBOX_JOB__COUNT` separately controls file workers shared by all creators.
