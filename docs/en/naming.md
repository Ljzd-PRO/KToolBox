# Naming format

Naming is project-specific in KToolBox v1. The CLI and WebUI read the same `[naming]` section from `ktoolbox.toml`; naming fields are no longer edited as global dotenv settings.

## Configure the layout

Open **Naming format** in the WebUI to configure:

- creator, work, revision, year, and month directory templates;
- primary-file and attachment-file templates;
- attachment, revision, content, and external-link names inside each work;
- year/month grouping, mixed-work layout, and sequential attachment names.

Template fields accept only the variable chips shown beside them, such as `{creator_name}`, `{creator_id}`, `{service}`, `{title}`, `{post_id}`, `{revision_id}`, `{year}`, and `{month}`. Path separators, parent traversal, unknown variables, and unsafe names are rejected before scanning.

**Directory structure** and **Naming templates** have separate save buttons. Saving changes future downloads immediately. Old files are never moved merely because a naming setting was saved.

![Naming templates in the dark theme](../assets/webui/34-naming-templates-desktop-dark.png)

## Convert old download locations

Open the dedicated **Legacy download conversion** tab only when previously downloaded content needs to follow the saved naming format. Add one or more old locations, then choose **Scan old locations**. These locations are scan inputs, not destinations for future tasks.

The scan reads the filesystem rather than relying only on task history, and it does not contact Pawchive. KToolBox identifies content from creator directory identities, `creator-indices.ktoolbox`, and `post.json`, without following symbolic links outside the selected locations.

The preview shows each creator's old and new path, work and file counts, total size, skipped items, and conflicts. Every safely convertible creator starts selected, and you can exclude individual creators before applying the change.

![Naming conversion review on mobile](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox never overwrites or merges a target. A stale scan, changed configuration, active related task, duplicate target, or filesystem change requires a new preview.

## Convert and recover

KToolBox runs selected moves as a persistent background conversion. Cancellation, write failure, or an interrupted process rolls completed moves back in reverse order. The already saved naming format remains active for future downloads.

Conversion progress and history are stored in `.ktoolbox/webui.sqlite3`. Successful temporary move logs are removed; completed history remains until you delete its record. A successful conversion removes empty source directories, but it never deletes unrelated files.

## First-start migration

On the first WebUI startup, KToolBox migrates legacy naming keys from `.env` and `prod.env` before creating a default project configuration. It:

1. writes the effective values to `ktoolbox.toml`;
2. backs up the dotenv files under `.ktoolbox/migrations/project-naming-v2/`;
3. removes the migrated legacy keys;
4. prints a terminal summary; and
5. asks after login whether to ignore old content permanently or review a conversion.

![One-time naming migration notice](../assets/webui/36-naming-migration-notice-light.png)

The decision dialog cannot be dismissed without choosing. Refreshing continues to show it until **Ignore** or **Review conversion** is selected. **Review conversion** opens the legacy conversion tab; known old locations are scanned automatically, otherwise the page asks you to add one. It never moves files before the preview is confirmed.

The CLI uses the project naming configuration too. When a legacy project still needs migration, start its WebUI once to complete the backed-up, atomic configuration migration.
