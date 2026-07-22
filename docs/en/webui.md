# WebUI

KToolBox WebUI is a project-bound management panel built with React and HeroUI. It edits the same configuration and calls the same Python services as the CLI; it does not launch or parse CLI subprocesses. Tasks, attempts, logs, and ownership records are persisted in `.ktoolbox/webui.sqlite3` inside the selected project.

## Install and start

Install the optional runtime and create a project directory:

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

Generate an Argon2id password hash using hidden terminal input:

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

The default is `0.0.0.0:8789` and the local browser opens automatically. `--host`, `--port`, and `--no-open` override environment configuration for that process. If `ktoolbox.toml` is missing, startup prints a warning and atomically creates a minimal valid project document. Startup still fails when the username or both password forms are missing.

## Security model

KToolBox has one local WebUI account and no default credentials. `KTOOLBOX_WEBUI__PASSWORD_HASH` takes precedence over the plaintext compatibility setting `KTOOLBOX_WEBUI__PASSWORD`. Prefer the hash and keep both dotenv files out of version control.

Sessions use random opaque tokens. SQLite stores only token hashes; the browser cookie is `HttpOnly` and `SameSite=Strict`, and it becomes `Secure` on HTTPS requests. Mutating requests require a per-session CSRF token and same-origin checks. Login attempts are rate-limited, API responses are not cached, and the application sends restrictive content, frame, referrer, and browser-permission headers.

The built-in server speaks HTTP. Its default LAN listener is appropriate only on a trusted network because passwords, cookies, paths, logs, and configuration are otherwise visible in transit. For a single machine, use `--host 127.0.0.1`. For remote access, terminate HTTPS at a trusted reverse proxy and restrict network access. The login page and application shell retain an HTTP warning while the page is not secure.

Only one scheduler may open a project at a time. A project lock prevents two WebUI processes from racing over its queue and outputs.

## Project workflows

The interface follows the browser language on first use and supports persistent English/Chinese selection. Theme follows the operating system until light or dark mode is selected. Blue, emerald, violet, rose, and amber accent palettes are available; form switches stay blue when enabled so their state remains consistent across palettes. Desktop uses a compact sidebar; narrow screens use a Drawer.

![Light configuration editor](../assets/webui/09-configuration-light.png)

Editable areas use a muted secondary surface with distinct field backgrounds. Field icons aid scanning, while form switches and checkboxes remain left-aligned with their labels instead of resembling centered action buttons. Switches use a gray track when off and a blue track when on; checkboxes render their indicator only when selected or indeterminate. Editable modal content and its fixed action bar share one continuous surface.

The main areas are:

- **Overview:** project path, queue health, active transfer totals, and recent tasks.
- **Tasks:** create, reorder, edit, pause, resume, stop, rerun, delete, and inspect synchronization or single-post downloads.
- **Creators:** search Pawchive and add, annotate, enable, disable, or remove roster entries.
- **Posts:** search without rendering remote media or expanded body text, inspect revisions, and create a download task.
- **Blockers:** order and scope `field-match` blockers and compose nested `any`/`all`, contains, equals, regular expression, and existence conditions.
- **Configuration:** edit `.env`, `prod.env`, and `ktoolbox.toml` through typed forms or advanced text views.
- **System:** inspect the project and application versions and download an example environment file.

![Task editor on a narrow screen](../assets/webui/19-task-form-mobile-light-zh.png)

![Creator roster on a narrow screen](../assets/webui/12-creators-mobile-light-zh.png)

Task creation uses two fixed tabs without overflow controls. Synchronization dates remain one official HeroUI range field in `year/month/day - year/month/day` form, while “No start date” and “No end date” independently clear either boundary. The post offset control advances in steps of 50. Title filters use removable HeroUI Chips created with a comma or Enter. Single-work downloads and new roster entries use independent HeroUI fields separated by code-styled Pawchive path fragments such as `/platform/user/creator/post/post`; the separators are never simulated inputs.

Creator IDs lead both desktop rows and mobile entries. The optional roster note is shown separately and never replaces the identity. When editing an existing creator, its platform and creator ID remain visible but read-only because they identify the stored roster entry.

## Configuration editing

Form labels are explicit bilingual text, not Python identifiers. Field descriptions are extracted from the English and Chinese configuration-class `:ivar field:` docstrings, while Pydantic supplies types, defaults, ranges, and secret metadata.

The `.env` and `prod.env` tabs show each final effective value and a source Chip. Values overridden by the process environment are read-only. Secret values are masked by default. Advanced text editing displays an additional warning because it can expose secrets.

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

![Live task progress](../assets/webui/14-task-running-1024-dark-zh.png)

Pause is cooperative: active network streams close, completed files and resumable temporary files remain, and resume creates a new attempt. Stop keeps the task definition so it can be edited and rerun. A process restart marks formerly running work as `interrupted`; recovery is always explicit.

Deleting a task normally removes only its queue record, attempts, and logs. “Delete outputs” first produces a file and byte-count preview. Confirmation removes only unchanged, regular files recorded as created by that task; symbolic links, pre-existing files, modified files, and shared files are never followed or removed.

## WebUI environment reference

| Variable | Default | Meaning |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | Listen interface. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | Listen port, 1–65535. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | Open the local URL after startup. |
| `KTOOLBOX_WEBUI__USERNAME` | empty | Required single-account username. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | empty | Preferred Argon2id hash. |
| `KTOOLBOX_WEBUI__PASSWORD` | empty | Plaintext fallback; ignored when a hash exists. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | Concurrent top-level tasks, 1–16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | Session lifetime since last use. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | Maximum session lifetime since login. |

Back up `ktoolbox.toml`, local dotenv files, and `.ktoolbox/webui.sqlite3` together when task history matters. Do not copy the database while the WebUI is running.
