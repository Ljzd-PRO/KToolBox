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

The **Default download location** belongs to the project too. Its default value is `downloads`, resolved relative to the project root. You may also enter an absolute host path outside the project. A task uses its explicit output first, then an automatic-sync plan's explicit output, and finally this project default. KToolBox stores the resolved absolute path in each created task, so later project changes do not silently relocate it.

![Directory structure and default output](../assets/webui/37-naming-structure-desktop-light.png)

## Convert old download locations

Open the dedicated **Legacy download conversion** tab only when previously downloaded content needs to follow the saved naming format. Add one or more old locations, then choose **Scan old locations**. These locations are scan inputs, not destinations for future tasks.

The scan reads the filesystem rather than relying only on task history, and it does not contact Pawchive. KToolBox identifies content from creator directory identities, `creator-indices.ktoolbox`, and `post.json`, without following symbolic links outside the selected locations.

The preview shows each creator's old and new path, work and file counts, total size, skipped items, and conflicts. Every safely convertible creator starts selected, and you can exclude individual creators before applying the change.

![Naming conversion review on mobile](../assets/webui/38-naming-conversion-mobile-dark.png)

KToolBox never overwrites or merges a target. A stale scan, changed configuration, active related task, duplicate target, or filesystem change requires a new preview.

## Convert and recover

KToolBox runs selected moves as a persistent background conversion. **Pause** waits for the current atomic file operation and keeps completed moves in place; **Continue** revalidates the configuration, filesystem fingerprint, conflicts, and free space before resuming. **Cancel** is different: it rolls completed moves back in reverse order. Write failure or an interrupted process also rolls back safely. The already saved naming format remains active for future downloads.

Conversion progress and history are stored in `.ktoolbox/webui.sqlite3`. Successful temporary move logs are removed; completed history remains until you delete its record. A successful conversion removes empty source directories, but it never deletes unrelated files.

## First-start migration

The migration guide appears only when KToolBox detects legacy naming keys in `.env` or `prod.env`. Startup performs detection and prints a warning, but does not modify any file. After login, the guided dialog:

1. shows every source, old value, and current project value;
2. selects legacy values by default while allowing individual fields to keep the project value;
3. previews the exact project and dotenv changes;
4. after confirmation, creates backups under `.ktoolbox/migrations/project-naming-v2/`, writes `ktoolbox.toml`, and removes the migrated dotenv keys atomically; and
5. then offers a separate old-directory conversion step.

![Guided legacy naming migration](../assets/webui/39-naming-migration-desktop-light.png)

Closing or choosing **Ignore** dismisses only the current dialog. As long as legacy keys remain, refreshing or signing in again shows it again. Configuration migration and directory conversion are separate: after configuration succeeds, review one or more old locations and explicitly choose **Scan old locations**. No scan or file move occurs merely by opening the conversion tool.

The CLI uses the project naming configuration too. When a legacy project still needs migration, start its WebUI and confirm the backed-up atomic migration. Legacy values supplied only through the process environment cannot be deleted; KToolBox ignores them for project naming and keeps warning until they are removed from the launching environment.
