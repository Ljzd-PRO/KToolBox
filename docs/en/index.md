# Welcome to KToolBox

KToolBox downloads public works from Pawchive. The WebUI is the recommended way to use it: common tasks are available as guided forms, and progress remains visible after you leave a page.

!!! warning "New major version"
    v1 has not yet received enough real-world validation. Some features may still fail. Back up existing settings and downloads before migrating, and report unexpected behavior.

## Start with the WebUI

1. Install the WebUI package.
2. Create one directory for your synchronization project.
3. Start KToolBox in that directory.

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

The browser opens automatically. Sign in with the `admin` username and random password printed in the terminal, add a creator, and create your first task. KToolBox creates `ktoolbox.toml` when needed and uses `downloads` as the default output directory.

![KToolBox WebUI overview](../assets/webui/40-overview-showcase-desktop-light.png)

## Choose your next step

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **Add creators and download**

    Follow the [project workflows](webui/project-workflows.md) to add creators, search works, create tasks, and adjust filters.

-   :material-progress-download: **Watch a task**

    Learn about progress, retries, pause, stop, rerun, and cleanup in [tasks and live updates](webui/tasks.md).

-   :material-calendar-sync-outline: **Run on a schedule**

    Create recurring plans with the [automatic synchronization guide](automatic-sync.md).

-   :material-folder-cog-outline: **Choose names and folders**

    Set the default output and readable layout with the [naming guide](naming.md).

</div>

## Advanced paths

You do not need these pages for a normal first run.

| Goal | Guide |
| --- | --- |
| Keep a stable login or deploy beyond one computer | [WebUI deployment reference](webui/reference.md) |
| Automate from a terminal | [CLI guide](commands/guide.md) and [command reference](commands/reference.md) |
| Inspect every setting | [Configuration guide](configuration/guide.md) and [reference](configuration/reference.md) |
| Connect an AI client or Python program | [MCP](mcp.md) and [Python API](api.md) |
| Upgrade an existing project or fix a problem | [Migration guide](migration-v1.md) and [FAQ](faq.md) |

## Safe defaults

The WebUI starts with generated credentials, sensitive-media previews disabled, and a project-local output directory. For local-only access, bind to `127.0.0.1`; use HTTPS for untrusted networks. KToolBox never implements Pawchive account or favorites operations.
