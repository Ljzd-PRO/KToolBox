# WebUI project workflows

Use these workflows after the WebUI is installed and bound to a project. They cover project data and settings; task execution and deployment details have their own focused guides.

## Project workflows

The interface follows the browser language on first use and supports persistent selection of Simplified Chinese, Traditional Chinese, English, Japanese, Korean, French, or Russian. Changing language also updates React Aria dates, number formatting, natural sorting, configuration metadata, validation, and known server errors. Theme follows the operating system until light or dark mode is selected. Blue, emerald, violet, rose, and amber accent palettes are available; form switches stay blue when enabled so their state remains consistent across palettes. Desktop uses a compact sidebar; narrow screens use a Drawer.

![Seven-language selector](../../assets/webui/23-language-menu-seven-locales.png)

![Light configuration editor](../../assets/webui/09-configuration-light.png)

Editable areas use a muted secondary surface with distinct field backgrounds. Field icons aid scanning, while form switches and checkboxes remain left-aligned with their labels instead of resembling centered action buttons. Switches use a gray track when off and a blue track when on; checkboxes render their indicator only when selected or indeterminate. Editable modal content and its fixed action bar share one continuous surface.

The main areas are:

- **Overview:** project path, queue health, active transfer totals, and recent tasks. Each statistic is a keyboard-accessible link to the corresponding filtered task or creator view.
- **Tasks:** create, edit, pause, resume, stop, rerun, delete, and inspect synchronization or single-work downloads. Select multiple rows for compatible bulk actions; only the readable target link opens details, so controls never trigger navigation.
- **Automatic sync:** create multiple recurring creator plans, inspect recent update counts and run history, pause schedules, or run a plan immediately.
- **Creators:** search Pawchive and add, annotate, enable, disable, or remove roster entries, including bulk enable, disable, and removal.
- **Posts:** search works, inspect revisions, and create a download task. Image previews appear only after explicitly enabling NSFW mode; body text remains collapsed by default.
- **Blockers:** order and scope `field-match` blockers and compose nested `any`/`all`, contains, equals, regular expression, and existence conditions.
- **Global configuration:** edit `.env`, `prod.env`, and `ktoolbox.toml` through typed forms or advanced text views.
- **System:** inspect the project and application versions and download an example environment file.
- **About:** inspect the KToolBox version, license, runtime, author, documentation, repository, and issue tracker without exposing author email addresses.

![Task editor on a narrow screen](../../assets/webui/19-task-form-mobile-light-zh.png)

![Pawchive creator roster](../../assets/webui/41-creators-showcase-desktop-light.png)

Task creation uses two fixed tabs without overflow controls. Synchronization dates remain one official HeroUI range field in `year/month/day - year/month/day` form, while “No start date” and “No end date” independently clear either boundary. The post offset control advances in steps of 50. Title filters use removable HeroUI Chips created with a comma or Enter. Single-work downloads and new roster entries use independent HeroUI fields separated by code-styled Pawchive path fragments such as `/platform/user/creator/post/post`; the separators are never simulated inputs.

Platform fields use a HeroUI ComboBox with Patreon, Pixiv, and Fanbox suggestions while still accepting any custom platform value. Compact enumerations use icon-enhanced HeroUI options; semantic colors are reserved for actual status, warning, and danger meanings.

Creator rows lead with the profile name returned by Pawchive. Names are cached for 24 hours, stale values remain available when refresh fails, and the creator ID is the fallback when no profile has ever loaded. The optional roster note remains independent and empty by default. When editing an existing creator, its platform and creator ID remain visible but read-only because they identify the stored roster entry.

Overview recent tasks, task queues, creator rosters, and post results support controlled HeroUI column sorting. Text uses locale-aware natural ordering, while counts, progress, speeds, states, and timestamps use their real values. Mobile cards expose the same sort field and direction. Task sorting changes presentation only and never changes scheduler order.

## Optional sensitive-media previews

NSFW mode is off in every new browser. While it is off, creator and work pages remain text-only and do not create image requests or reserve empty media space. Enabling it requires confirmation each time; the enabled preference then stays in that browser until it is switched off and is synchronized across tabs.

Media is fetched through the authenticated same-origin WebUI proxy, never directly by the browser from Pawchive hosts. The proxy verifies the decoded bitmap, rejects redirects, SVG, non-images, damaged files, resources over 32 MiB or 50 MP, and creates bounded thumbnails. Creator avatars and banners, work covers, image attachments, and supported content images can be shown. Galleries load 12 entries at a time, and the viewer supports arrow keys and Escape. Videos, archives, and other attachments remain text-only.

![Creator avatars with NSFW mode enabled](../../assets/webui/46-creators-nsfw-preview-light.png)

![Work cover and paginated media gallery](../../assets/webui/47-post-media-gallery-light.png)

## Automatic synchronization

The **Automatic sync** page supports multiple plans, selected creators, five-field Cron schedules, and anchored intervals of at least 15 minutes. Each plan has an IANA time zone, a first-run boundary, output options, and a preview of its next three runs. A manual run uses the same task queue and advances successful creator checkpoints without shifting an interval schedule.

Automatic checks prefer Pawchive's UTC-like `added` time, overlap the previous successful checkpoint by 24 hours, and deduplicate works across all plans in the project. A first unlimited run establishes a baseline instead of reporting the entire archive as new. Missed runs while KToolBox is stopped are skipped, and an active run for the same plan prevents a duplicate trigger. See the [automatic synchronization guide](../automatic-sync.md) for scheduling, checkpoint, and recovery details.

## Project naming

Naming and the default output are stored in the project's `ktoolbox.toml` and shared by CLI, WebUI, MCP, work downloads, and automatic synchronization. The **Naming format** page saves directory structure and templates independently. Its reusable legacy converter accepts multiple saved layouts or pasted legacy `.env`/TOML, always uses the current project format as its read-only target, and never persists the pasted source. It scans explicitly selected old locations without contacting Pawchive, shows per-creator statistics, and supports pause, continuation, or rollback. Old locations are never future download destinations. See the [naming guide](../naming.md) for inheritance, guided legacy migration, and recovery.

## Configuration editing

Form labels and descriptions are explicit localized text, not Python identifiers. English configuration-class `:ivar field:` docstrings remain the semantic field source; checked locale catalogs provide complete labels and explanations for all seven languages, while Pydantic supplies types, defaults, ranges, and secret metadata.

Fixed choices such as log level use icon-enhanced HeroUI Select controls. Fields with useful presets but valid custom values use ComboBox controls. Internal names such as `attachments`, `content.txt`, and `external_links.txt` remain ordinary text fields; only real filesystem locations expose the remote path picker.

The `.env` and `prod.env` tabs show each final effective value and a source Chip. Values overridden by the process environment are read-only. Secret values are masked by default. Advanced text editing displays an additional warning because it can expose secrets.

Filesystem-backed fields retain manual editing and add a browse button. The dialog shows the remote computer running KToolBox rather than the browser device, with localized quick locations, breadcrumbs, search, a labelled hidden-item control, pagination, an explicit new-folder dialog, and confirmed empty-folder deletion. Project-relative configuration values remain relative after selection; absolute task and post output paths remain absolute. Environment-sourced read-only values cannot open the picker.

Before a save, the server parses and validates the proposed file and returns a semantic diff. Saving uses an ETag to reject stale edits and atomically replaces the file. The TOML editor uses the existing TomlKit/Pydantic store so comments survive structured roster and blocker changes.

![Dark configuration editor](../../assets/webui/20-configuration-1024-dark-zh.png)

![Global configuration log-level choices](../../assets/webui/30-global-configuration-log-level-light.png)

![Scoped blocker editor](../../assets/webui/17-blocker-form-1024-light-zh.png)

## Related WebUI guides

- [Installation and security overview](../webui.md)
- [Project workflows](project-workflows.md)
- [Tasks and live updates](tasks.md)
- [Deployment reference](reference.md)
