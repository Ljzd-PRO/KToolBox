# Configuration Guide

KToolBox reads environment variables and two optional files in the current working directory: `.env`, then `prod.env`. Values from `prod.env` override matching values from `.env`, while process environment variables have the highest priority.

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
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

All settings are optional. See the [configuration reference](reference.md) for defaults.

## Generate or edit configuration

Generate every available dotenv key from the current model:

```bash
ktoolbox example-env
```

The optional terminal editor can inspect field descriptions parsed from the configuration model docstrings:

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config-editor
```

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
