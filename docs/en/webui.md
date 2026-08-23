# WebUI

KToolBox WebUI is a project-bound management panel built with React and HeroUI. It edits the same configuration and calls the same Python services as the CLI; it does not launch or parse CLI subprocesses. Tasks, attempts, logs, and ownership records are persisted in `.ktoolbox/webui.sqlite3` inside the selected project.

## Continue by task

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **Manage project data**

    Work with creators, works, naming, configuration, and optional media in [Project workflows](webui/project-workflows.md).

-   :material-arrow-right-circle-outline: **Monitor downloads**

    Create, diagnose, pause, resume, rerun, and safely remove work in [Tasks and live updates](webui/tasks.md).

-   :material-arrow-right-circle-outline: **Deploy and maintain**

    Review environment variables, backups, runtime information, and locale coverage in the [Deployment reference](webui/reference.md).

</div>

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
