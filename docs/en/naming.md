# Naming format

Naming is project-specific in KToolBox v1. The CLI and WebUI read the same `[naming]` section from `ktoolbox.toml`; naming fields are no longer edited as global dotenv settings.

## Configure the layout

Open **Naming format** in the WebUI to configure:

- one or more download roots;
- creator, work, revision, year, and month directory templates;
- primary-file and attachment-file templates;
- attachment, revision, content, and external-link names inside each work;
- year/month grouping, mixed-work layout, and sequential attachment names.

Template fields accept only the variable chips shown beside them, such as `{creator_name}`, `{creator_id}`, `{service}`, `{title}`, `{post_id}`, `{revision_id}`, `{year}`, and `{month}`. Path separators, parent traversal, unknown variables, and unsafe names are rejected before scanning.

![Naming templates in the dark theme](../assets/webui/34-naming-templates-desktop-dark.png)

## Preview existing downloads

**Scan and review** scans the actual download roots. It does not depend on task history and does not contact Pawchive. KToolBox identifies content from creator directory identities, `creator-indices.ktoolbox`, and `post.json`, without following symbolic links outside the roots.

The preview shows each creator's old and new path, work and file counts, total size, skipped items, and conflicts. **Convert downloaded creators** is enabled by default. Every safely convertible creator starts selected, and you can exclude individual creators before applying the change.

![Naming conversion review on mobile](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox never overwrites or merges a target. A stale scan, changed configuration, active related task, duplicate target, or filesystem change requires a new preview.

## Apply and recover

With conversion enabled, KToolBox persists a pending configuration snapshot and runs the move as a background conversion. The new format becomes active only after every selected operation succeeds. Cancellation, write failure, or an interrupted process rolls completed moves back in reverse order and leaves the previous configuration active.

Conversion progress and history are stored in `.ktoolbox/webui.sqlite3`. Successful temporary move logs are removed; completed history remains until you delete its record. A successful conversion removes empty source directories, but it never deletes unrelated files.

If conversion is disabled, only the new format is saved. Existing downloads stay where they are, and future CLI or WebUI downloads use the new project format.

## First-start migration

On the first WebUI startup, KToolBox migrates legacy naming keys from `.env` and `prod.env` before creating a default project configuration. It:

1. writes the effective values to `ktoolbox.toml`;
2. backs up the dotenv files under `.ktoolbox/migrations/project-naming-v2/`;
3. removes the migrated legacy keys;
4. prints a terminal summary; and
5. shows a one-time WebUI notice after login.

![One-time naming migration notice](../assets/webui/36-naming-migration-notice-light.png)

The CLI uses the project naming configuration too. When a legacy project still needs migration, start its WebUI once to complete the backed-up, atomic conversion.
