# WebUI

The WebUI is the recommended way to use KToolBox. It keeps one synchronization project, its settings, tasks, progress, and history together in a browser interface.

## First run

Install the WebUI package, create a project directory, and start KToolBox:

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

The browser opens automatically. Sign in with the `admin` username and random password printed in the terminal. If `ktoolbox.toml` is missing, KToolBox creates it; new tasks use the project's `downloads` directory by default.

![KToolBox WebUI overview](../assets/webui/40-overview-showcase-desktop-light.png)

## Your first synchronization

1. Open **Creators** and select **Add creator**.
2. Paste a Pawchive creator URL, or enter its platform and ID.
3. Open **Tasks**, select **Create task**, then choose **Synchronize creators**.
4. Keep the initial limit small while checking a new creator and naming layout.
5. Open the task to watch downloads, speed, retries, and useful activity messages.

Completed files are kept, compatible temporary files can resume, and failed creators do not remove successful downloads from the same task.

## Continue by goal

<div class="grid cards" markdown>

-   :material-folder-account-outline: **Creators, works, filters, and naming**

    Use [project workflows](webui/project-workflows.md) for everyday project management.

-   :material-progress-download: **Progress and task controls**

    Use [tasks and live updates](webui/tasks.md) for pause, stop, rerun, diagnostics, and safe cleanup.

-   :material-server-security: **Accounts and deployment**

    Use the [deployment reference](webui/reference.md) only when you need stable credentials, remote access, backup, or detailed security behavior.

-   :material-update: **Existing v0 project**

    Read the [migration guide](migration-v1.md) before converting old settings or downloads.

</div>

## Optional stable login

Generated credentials are enough for a first run. To keep the same login across restarts, create a password hash:

```bash
ktoolbox webui hash-password
```

Add the result to the project's `.env`:

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## Safe access

The built-in server uses HTTP. For use on the same computer, bind it to `127.0.0.1`:

```bash
ktoolbox webui . --host 127.0.0.1
```

Use a trusted network or an HTTPS reverse proxy for remote access. Anyone who can sign in can inspect project paths, configuration, and task logs, so do not share access with untrusted users. Only one WebUI process may manage the same project at a time.
