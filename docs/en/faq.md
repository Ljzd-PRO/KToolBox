# FAQ

## Why are account favorites unavailable?

KToolBox v1 implements the 14 Pawchive operations that do not require login. The five OpenAPI operations protected by `cookieAuth` are deliberately excluded, so the API client never accepts or sends an account session.

Post flagging is a separate public operation and is implemented. Call it intentionally: a successful flag changes server state and an already flagged post may return `PawchiveConflictError`.

## What should I do when an API call fails?

The CLI reports typed Pawchive failures rather than returning a partially parsed response. Common classes are transport, HTTP, authentication, not-found, conflict, and response-validation errors.

- Check that the URL or `service`, creator ID, and post ID are correct.
- Increase `KTOOLBOX_API__TIMEOUT` for a slow connection.
- Adjust `KTOOLBOX_API__RETRY_TIMES` and `KTOOLBOX_API__RETRY_INTERVAL` for transient transport, `429`, or `5xx` failures.
- Do not add an account cookie to API settings; API requests do not use one.

Redirects, ordinary `4xx` responses, conflicts, and invalid response data are not retried.

## Why do file downloads return 403?

If the file host requires a session for a specific asset, set the downloader-only key:

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

The cookie is scoped to file download requests and is not sent to Pawchive API requests. Treat `.env` and `prod.env` as secret-bearing local files and do not commit them.

## How do I resume an interrupted download?

Run the same command again. KToolBox skips complete destination files. If an incomplete file with `downloader.temp_suffix` exists and the server supports ranges, the downloader requests the remaining bytes and validates the combined size.

## How do I disable covers or attachments?

```dotenv
# Attachments only.
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# Covers only.
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file` means the main post file, usually the cover. Both options default to `True`.

## Can attachments be stored directly in the post directory?

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## How do I avoid long filenames?

Use sequential names or a format precision limit:

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## How do I configure a proxy?

HTTPX reads standard proxy environment variables:

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

On PowerShell:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## Why does the configuration editor not open?

Install the optional terminal UI dependency:

```bash
pip install "ktoolbox[urwid]"
# or
pipx install "ktoolbox[urwid]" --force
```

## How do I synchronize many creators regularly?

Add each creator to the project roster, optionally assign a short alias, then run targetless `sync`:

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Use `creator disable` to keep an entry without including it in targetless runs. You can still explicitly sync a disabled alias. Creator preparation and file transfer have separate concurrency limits, so a large creator does not monopolize every ready download.

## How do I exclude different topics for different creators?

Add separate `[[blockers]]` entries to `ktoolbox.toml`. Set `scope.mode = "global"` for rules shared by everyone, or `scope.mode = "creators"` with exact `service:id` values. Blocks are evaluated in file order and stop at the first match.

Validate regular expressions and scopes before a long run:

```bash
ktoolbox config validate
```

## Why does progress look different in a redirected log?

Rich live progress is used only on an interactive terminal. It shows each active file's speed and ETA, plus the aggregate speed of all active downloads on the `Files` row. Pipes, CI, `NO_COLOR`, and `--plain` use stable line output so log messages cannot corrupt an ANSI live region. Use `--no-color` when you want the interactive layout without color, or `--quiet` to suppress progress and ordinary logs.

## Is uvloop or winloop required?

No. They are optional event-loop optimizations. Use `ktoolbox[uvloop]` on Linux/macOS or `ktoolbox[winloop]` on Windows. If neither is installed, KToolBox continues with Python's standard asyncio loop.

## Why might an antivirus flag a packaged executable?

Some heuristic scanners flag PyInstaller bundles or download managers. Releases are built through the repository's public automation; you can also install with `pipx` or audit and build the source locally.
