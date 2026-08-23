# WebUI tasks and live updates

The persistent queue keeps task definitions, attempts, progress, diagnostics, and ownership records together. This page explains execution controls and live synchronization.

## Task lifecycle

`sync` and `download` tasks preserve the complete corresponding CLI inputs. A targetless synchronization resolves the currently enabled roster when the task is created. Each attempt then receives an immutable, redacted configuration snapshot; later configuration edits affect only future attempts.

Each task also stores a presentation-only snapshot with its normalized target key and optional post title and creator name. It remains readable offline and never affects execution, deduplication, or resource locking. Queue rows lead with that target instead of an output path, and details, pause/resume, stop, edit, ordering, and delete controls remain directly visible.

![Desktop task queue with readable targets](../../assets/webui/43-task-queue-showcase-desktop-light.png)

![Mobile task queue with direct actions](../../assets/webui/22-task-queue-mobile-light-zh.png)

![Dark task editor](../../assets/webui/18-task-form-1024-dark-zh.png)

The top-level queue runs two tasks by default (`KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS`) while each task retains its configured creator and file concurrency. Identical active tasks resolve to the existing task. Tasks with overlapping normalized outputs, creators, or posts wait in `blocked` until the resource lock is released.

Live events use SSE with reconnect support. REST task state remains authoritative, and only a `task.status` event can change it; a completed file never marks its parent task complete. Aggregate download speed uses a five-second rolling window with a short hand-off grace period, so switching between files does not flash to zero. The overview and task page both show the speed summed across genuinely running tasks.

![Overview with aggregate download speed](../../assets/webui/40-overview-showcase-desktop-light.png)

The detail view reports prepared creators, files, bytes, overall progress, aggregate and per-file speeds, ETA, skipped/failed counts, active creators, active downloads, waiting retries, and structured logs. Active downloads, retries, and transfer events use the final name produced by the project's naming format, not an opaque Pawchive storage identifier. The three live panels have stable heights and their own scroll areas, so changing concurrency does not move the log or the page. The default activity view omits byte-level progress and ordinary queue noise; transfer and complete diagnostic views remain available when needed.

![Stable live task panels](../../assets/webui/44-task-live-showcase-desktop-dark.png)

Failed attempts persist a bounded, redacted diagnostic report instead of only a failure count. The task row shows the first useful cause; details group failures by creator and file and identify the stage, retryability, safe field paths, and a suggested recovery action. Upstream response bodies, post titles, cookies, and complete download URLs are never stored in this report. On narrow screens, the 64px workbar, 12px page spacing, and compact appearance Popover expose more useful content without shrinking form text below 16px. The MCP tool catalog uses collapsible HeroUI groups and automatically expands matching groups during search or permission filtering.

![Structured task failure explanation](../../assets/webui/26-task-failure-1440-light-zh.png)

![Compact mobile appearance controls](../../assets/webui/27-appearance-mobile-dark-zh.png)

![Live task progress on a mobile screen](../../assets/webui/45-task-live-showcase-mobile-dark.png)

Pause is cooperative: active network streams close, completed files and resumable temporary files remain, and resume creates a new attempt. Stop keeps the task definition so it can be edited and rerun. Resume is available only for paused, stopped, failed, or interrupted work. A completed synchronization instead offers **Rerun**, which reuses the task record and creates a new attempt; a completed single-work download does not. A process restart marks formerly running work as `interrupted`, clears stale live progress, and requires explicit recovery.

Deleting a task normally removes only its queue record, attempts, and logs. “Delete outputs” first shows the readable target, output directory, file and byte totals, and an expandable relative-path preview; internal task UUIDs are not displayed. Confirmation removes only unchanged, regular files recorded as created by that task; symbolic links, pre-existing files, modified files, and shared files are never followed or removed.

![Readable task cleanup preview](../../assets/webui/31-task-delete-preview-light.png)

![Completed synchronization with rerun](../../assets/webui/33-task-rerun-light.png)

## Automatic refresh

One authenticated SSE connection keeps tasks, creators, ignore rules, configuration, MCP tokens, and open remote-directory views synchronized across browser tabs. Structural changes normally appear within one second, while task progress updates the local query cache directly instead of repeatedly downloading the complete task list.

If the live connection is unavailable for more than five seconds, the WebUI shows a compact warning and refreshes local project queries every 10 seconds. It stops fallback polling and refreshes once as soon as SSE recovers. Pawchive searches, work details, and version checks remain on demand and are never requested by the fallback loop.

The System page reports the current update method and last signal time and provides explicit refresh and reconnect actions. When another tab or MCP client changes data while a form contains unsaved edits, KToolBox preserves the draft and asks whether to reload the new data or continue editing; the normal ETag and state-conflict checks still apply when saving.

## Related WebUI guides

- [Installation and security overview](../webui.md)
- [Project workflows](project-workflows.md)
- [Tasks and live updates](tasks.md)
- [Deployment reference](reference.md)
