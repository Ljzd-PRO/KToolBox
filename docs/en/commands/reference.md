# Command Reference

Run `ktoolbox COMMAND -h` for Fire's generated help. The table below records the stable v1 command surface; hyphenated names map to the Python parameter names shown in parentheses.

## General commands

| Command | Purpose |
| --- | --- |
| `version` | Show the installed KToolBox version and perform the optional release check. |
| `site-version` | Show the Pawchive application version. |
| `config-editor` | Open the optional terminal configuration editor. |
| `example-env` | Render a complete dotenv configuration reference. |

## `search-creator`

Filters the public creator list locally. At least one filter is recommended.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `--name` | string | `None` | Case-insensitive creator-name filter. |
| `--id` | string | `None` | Exact creator ID filter. |
| `--service` | string | `None` | Exact service filter. |
| `--dump` | path | `None` | Write matching models as JSON. |

## `search-creator-post`

Lists posts for creators selected by ID, name, or service.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `--id` | string | `None` | Creator ID. Use with `--service` for a direct lookup. |
| `--name` | string | `None` | Select matching creators from the public list. |
| `--service` | string | `None` | Creator service. |
| `--q` | string | `None` | Pawchive search query, at least 3 characters. |
| `--o` | integer | `None` | API offset; non-negative and divisible by 50. |
| `--dump` | path | `None` | Write matching post models as JSON. |

## `get-post`

| Argument or option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `service` | string | required | Creator service. |
| `creator-id` (`creator_id`) | string | required | Creator ID. |
| `post-id` (`post_id`) | string | required | Post ID. |
| `--revision-id` | string | `None` | Select this ID from the post revision list. |
| `--dump` | path | `None` | Write the validated model as JSON. |

## `download-post`

Provide either `url` or all of `service`, `creator-id`, and `post-id`.

| Argument or option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `url` | string | `None` | Pawchive post or revision URL. |
| `--service` | string | `None` | Creator service. |
| `--creator-id` | string | `None` | Creator ID. |
| `--post-id` | string | `None` | Post ID. |
| `--revision-id` | string | `None` | Download one selected revision. |
| `--path` | path | `.` | Output root. |
| `--dump-post-data` | boolean | `True` | Save validated metadata to `post.json`. |

## `sync-creator`

Provide either `url` or both `service` and `creator-id`.

| Argument or option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `url` | string | `None` | Pawchive creator URL. |
| `--service` | string | `None` | Creator service. |
| `--creator-id` | string | `None` | Creator ID. |
| `--path` | path | `.` | Output root. |
| `--save-creator-indices` | boolean | `False` | Save `creator-indices.ktoolbox`. |
| `--mix-posts` | boolean | configuration | Override `job.mix_posts`. |
| `--start-time` | date | `None` | Inclusive lower publication date, `%Y-%m-%d`. |
| `--end-time` | date | `None` | Inclusive upper publication date, `%Y-%m-%d`. |
| `--offset` | integer | `0` | First post index at the CLI boundary. |
| `--length` | integer | `None` | Number of posts; `None` fetches all pages. |
| `--keywords` | string/tuple | configuration | Include titles containing any value. |
| `--keywords-exclude` | string/tuple | configuration | Exclude titles containing any value. |

Exit-facing API, validation, and task-generation failures are returned as readable messages. Download workers retain their retry and progress behavior from the active configuration.
