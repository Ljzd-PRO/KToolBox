# WebUI

KToolBox WebUI is a project-bound management panel built with React and HeroUI. It edits the same configuration and calls the same Python services as the CLI; it does not launch or parse CLI subprocesses. Tasks, attempts, logs, and ownership records are persisted in `.ktoolbox/webui.sqlite3` inside the selected project.

## Install and start

Install the optional runtime and create a project directory:

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

Credentials are optional at startup. When they are absent, the terminal prints the `admin` username and a new random password valid for that process run. To configure stable credentials, generate an Argon2id password hash using hidden terminal input:

```bash
ktoolbox webui hash-password
```

Store the account in the project's `.env`. Quote the hash so the shell-style `$` characters remain literal:

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

Start the panel for that project:

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

The default is `0.0.0.0:8789` and the local browser opens automatically. `--host`, `--port`, and `--no-open` override environment configuration for that process. If `ktoolbox.toml` is missing, startup prints a warning and atomically creates a minimal valid project document. Missing credentials no longer block startup: an empty username becomes `admin`, and empty password settings produce a new terminal-printed password for that run.

## Security model

KToolBox has one local WebUI account. Explicit configuration takes precedence; `KTOOLBOX_WEBUI__PASSWORD_HASH` takes precedence over the plaintext compatibility setting `KTOOLBOX_WEBUI__PASSWORD`. If neither password form is configured, KToolBox generates an in-memory password for every launch and prints it with the effective username only in that terminal. Prefer a configured hash for stable deployments and keep both dotenv files out of version control.

Sessions use random opaque tokens. SQLite stores only token hashes; the browser cookie is `HttpOnly` and `SameSite=Strict`, and it becomes `Secure` on HTTPS requests. Mutating requests require a per-session CSRF token and same-origin checks. Login attempts are rate-limited, API responses are not cached, and the application sends restrictive content, frame, referrer, and browser-permission headers.

The built-in server speaks HTTP. Its default LAN listener is appropriate only on a trusted network because passwords, cookies, paths, logs, and configuration are otherwise visible in transit. For a single machine, use `--host 127.0.0.1`. For remote access, terminate HTTPS at a trusted reverse proxy and restrict network access. The login page and application shell retain an HTTP warning while the page is not secure.

Only one scheduler may open a project at a time. A project lock prevents two WebUI processes from racing over its queue and outputs.

The remote path picker runs with the filesystem permissions of the KToolBox process. Project-scoped task, post, and download-structure fields cannot leave the bound project, including through symbolic links. The storage-bucket and log-directory fields are explicitly host-scoped and may reveal names and metadata anywhere that account can traverse. The picker APIs list metadata, create directories, and remove explicitly confirmed empty directories. Deletion uses a non-recursive operation: files, symbolic links, project roots, home roots, and directories containing any item are never removed. The picker does not read file contents, upload, download, rename, or delete files. Entering a new filename selects a path and does not create an empty file. Treat WebUI access as sensitive host access and do not expose it to untrusted users.

## Project workflows

The interface follows the browser language on first use and supports persistent selection of Simplified Chinese, Traditional Chinese, English, Japanese, Korean, French, or Russian. Changing language also updates React Aria dates, number formatting, natural sorting, configuration metadata, validation, and known server errors. Theme follows the operating system until light or dark mode is selected. Blue, emerald, violet, rose, and amber accent palettes are available; form switches stay blue when enabled so their state remains consistent across palettes. Desktop uses a compact sidebar; narrow screens use a Drawer.

![Seven-language selector](../assets/webui/23-language-menu-seven-locales.png)

![Light configuration editor](../assets/webui/09-configuration-light.png)

Editable areas use a muted secondary surface with distinct field backgrounds. Field icons aid scanning, while form switches and checkboxes remain left-aligned with their labels instead of resembling centered action buttons. Switches use a gray track when off and a blue track when on; checkboxes render their indicator only when selected or indeterminate. Editable modal content and its fixed action bar share one continuous surface.

The main areas are:

- **Overview:** project path, queue health, active transfer totals, and recent tasks. Each statistic is a keyboard-accessible link to the corresponding filtered task or creator view.
- **Tasks:** create, edit, pause, resume, stop, rerun, delete, and inspect synchronization or single-work downloads. Select multiple rows for compatible bulk actions; clicking a row opens its details.
- **Creators:** search Pawchive and add, annotate, enable, disable, or remove roster entries, including bulk enable, disable, and removal.
- **Posts:** search without rendering remote media or expanded body text, inspect revisions, and create a download task.
- **Blockers:** order and scope `field-match` blockers and compose nested `any`/`all`, contains, equals, regular expression, and existence conditions.
- **Configuration:** edit `.env`, `prod.env`, and `ktoolbox.toml` through typed forms or advanced text views.
- **System:** inspect the project and application versions and download an example environment file.

![Task editor on a narrow screen](../assets/webui/19-task-form-mobile-light-zh.png)

![Creator roster on a narrow screen](../assets/webui/12-creators-mobile-light-zh.png)

Task creation uses two fixed tabs without overflow controls. Synchronization dates remain one official HeroUI range field in `year/month/day - year/month/day` form, while “No start date” and “No end date” independently clear either boundary. The post offset control advances in steps of 50. Title filters use removable HeroUI Chips created with a comma or Enter. Single-work downloads and new roster entries use independent HeroUI fields separated by code-styled Pawchive path fragments such as `/platform/user/creator/post/post`; the separators are never simulated inputs.

Platform fields use a HeroUI ComboBox with Patreon, Pixiv, and Fanbox suggestions while still accepting any custom platform value. Compact enumerations use icon-enhanced HeroUI options; semantic colors are reserved for actual status, warning, and danger meanings.

Creator rows lead with the profile name returned by Pawchive. Names are cached for 24 hours, stale values remain available when refresh fails, and the creator ID is the fallback when no profile has ever loaded. The optional roster note remains independent and empty by default. When editing an existing creator, its platform and creator ID remain visible but read-only because they identify the stored roster entry.

Overview recent tasks, task queues, creator rosters, and post results support controlled HeroUI column sorting. Text uses locale-aware natural ordering, while counts, progress, speeds, states, and timestamps use their real values. Mobile cards expose the same sort field and direction. Task sorting changes presentation only and never changes scheduler order.

## Configuration editing

Form labels and descriptions are explicit localized text, not Python identifiers. English configuration-class `:ivar field:` docstrings remain the semantic field source; checked locale catalogs provide complete labels and explanations for all seven languages, while Pydantic supplies types, defaults, ranges, and secret metadata.

The `.env` and `prod.env` tabs show each final effective value and a source Chip. Values overridden by the process environment are read-only. Secret values are masked by default. Advanced text editing displays an additional warning because it can expose secrets.

Filesystem-backed fields retain manual editing and add a browse button. The dialog shows the remote computer running KToolBox rather than the browser device, with localized quick locations, breadcrumbs, search, a labelled hidden-item control, pagination, an explicit new-folder dialog, and confirmed empty-folder deletion. Project-relative configuration values remain relative after selection; absolute task and post output paths remain absolute. Environment-sourced read-only values cannot open the picker.

Before a save, the server parses and validates the proposed file and returns a semantic diff. Saving uses an ETag to reject stale edits and atomically replaces the file. The TOML editor uses the existing TomlKit/Pydantic store so comments survive structured roster and blocker changes.

![Dark configuration editor](../assets/webui/20-configuration-1024-dark-zh.png)

![Scoped blocker editor](../assets/webui/17-blocker-form-1024-light-zh.png)

## Task lifecycle

`sync` and `download` tasks preserve the complete corresponding CLI inputs. A targetless synchronization resolves the currently enabled roster when the task is created. Each attempt then receives an immutable, redacted configuration snapshot; later configuration edits affect only future attempts.

Each task also stores a presentation-only snapshot with its normalized target key and optional post title and creator name. It remains readable offline and never affects execution, deduplication, or resource locking. Queue rows lead with that target instead of an output path, and details, pause/resume, stop, edit, ordering, and delete controls remain directly visible.

![Desktop task queue with readable targets](../assets/webui/21-task-queue-1440-dark-zh.png)

![Mobile task queue with direct actions](../assets/webui/22-task-queue-mobile-light-zh.png)

![Dark task editor](../assets/webui/18-task-form-1024-dark-zh.png)

The top-level queue runs two tasks by default (`KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS`) while each task retains its configured creator and file concurrency. Identical active tasks resolve to the existing task. Tasks with overlapping normalized outputs, creators, or posts wait in `blocked` until the resource lock is released.

Live events use SSE with reconnect support. REST task state remains authoritative. The detail view reports prepared creators, files, bytes, overall progress, aggregate and per-file speeds, ETA, skipped/failed counts, active items, and structured logs.

Failed attempts persist a bounded, redacted diagnostic report instead of only a failure count. The task row shows the first useful cause; details group failures by creator and file and identify the stage, retryability, safe field paths, and a suggested recovery action. Upstream response bodies, post titles, cookies, and complete download URLs are never stored in this report. On narrow screens, the 64px workbar, 12px page spacing, and compact appearance Popover expose more useful content without shrinking form text below 16px. The MCP tool catalog uses collapsible HeroUI groups and automatically expands matching groups during search or permission filtering.

![Structured task failure explanation](../assets/webui/26-task-failure-1440-light-zh.png)

![Compact mobile appearance controls](../assets/webui/27-appearance-mobile-dark-zh.png)

![Live task progress](../assets/webui/14-task-running-1024-dark-zh.png)

Pause is cooperative: active network streams close, completed files and resumable temporary files remain, and resume creates a new attempt. Stop keeps the task definition so it can be edited and rerun. A process restart marks formerly running work as `interrupted`; recovery is always explicit.

Deleting a task normally removes only its queue record, attempts, and logs. “Delete outputs” first produces a file and byte-count preview. Confirmation removes only unchanged, regular files recorded as created by that task; symbolic links, pre-existing files, modified files, and shared files are never followed or removed.

## Automatic refresh

One authenticated SSE connection keeps tasks, creators, ignore rules, configuration, MCP tokens, and open remote-directory views synchronized across browser tabs. Structural changes normally appear within one second, while task progress updates the local query cache directly instead of repeatedly downloading the complete task list.

If the live connection is unavailable for more than five seconds, the WebUI shows a compact warning and refreshes local project queries every 10 seconds. It stops fallback polling and refreshes once as soon as SSE recovers. Pawchive searches, work details, and version checks remain on demand and are never requested by the fallback loop.

The System page reports the current update method and last signal time and provides explicit refresh and reconnect actions. When another tab or MCP client changes data while a form contains unsaved edits, KToolBox preserves the draft and asks whether to reload the new data or continue editing; the normal ETag and state-conflict checks still apply when saving.

## WebUI environment reference

| Variable | Default | Meaning |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | Listen interface. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | Listen port, 1–65535. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | Open the local URL after startup. |
| `KTOOLBOX_WEBUI__USERNAME` | empty → `admin` at startup | Optional single-account username. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | empty | Preferred stable Argon2id hash. |
| `KTOOLBOX_WEBUI__PASSWORD` | empty → random per startup | Plaintext fallback; ignored when a hash exists. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | Concurrent top-level tasks, 1–16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | Session lifetime since last use. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | Maximum session lifetime since login. |

Back up `ktoolbox.toml`, local dotenv files, and `.ktoolbox/webui.sqlite3` together when task history matters. Do not copy the database while the WebUI is running.

## Multilingual browser verification

The seven locale catalogs are exercised on desktop and mobile in light and dark themes. Representative verified states are shown below; user content and filesystem paths remain in their original form.

![French configuration on mobile](../assets/webui/24-configuration-mobile-fr.png)

![Russian remote path picker on mobile](../assets/webui/25-path-picker-mobile-ru.png)
