# Command Reference

Run `ktoolbox COMMAND --help` for the authoritative Cyclopts help. Command and option names use hyphens; legacy underscore spellings are still parsed for hidden compatibility commands.

## Global options

| Option | Meaning |
| --- | --- |
| `-h`, `--help` | Print help directly without a pager. |
| `--version` | Print the installed KToolBox version. |
| `--install-completion` | Install completion for the detected shell. |
| `--config PATH` | Select a project file. Resolution order is this option, `KTOOLBOX_PROJECT_CONFIG`, then `./ktoolbox.toml`. |
| `--verbose` | Include diagnostic logs. |
| `--quiet` | Suppress progress and ordinary logs. |
| `--plain` | Force stable line-oriented progress. Non-TTY output and `NO_COLOR` use this automatically. |
| `--no-color` | Disable ANSI colors. |

Running `ktoolbox` without arguments prints root help and exits successfully.

## Command tree

| Command | Purpose |
| --- | --- |
| `download` | Download one post or selected revision. |
| `sync [TARGET ...]` | Synchronize explicit creators, or all enabled roster creators when no target is given. |
| `creator list/add/remove/enable/disable/search` | Manage the roster or search Pawchive creators. |
| `post show/search` | Inspect a post or search creator posts. |
| `config edit/example/validate/path` | Edit or inspect environment and project configuration. |
| `site-version` | Print the Pawchive application version. |
| `webui [PROJECT_DIR]` | Run the optional HeroUI panel for one project. |

## `download`

Provide a Pawchive post URL, or all of `--service`, `--creator-id`, and `--post-id`.

| Argument or option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `POST` | string | omitted | Pawchive post or revision URL. |
| `--service` | string | omitted | Creator service. |
| `--creator-id` | string | omitted | Creator ID. |
| `--post-id` | string | omitted | Post ID. |
| `--revision-id` | string | omitted | Select this revision from the revision list. |
| `-o`, `--output`, `--path` | path | `.` | Output root. |
| `--dump-post-data` / `--no-dump-post-data` | boolean | enabled | Save validated metadata to `post.json`. |

`download` intentionally does not apply roster blockers.

## `sync`

Each `TARGET` may be a Pawchive creator URL, `service:id`, or roster alias. Explicit targets run even when disabled in the roster. With no targets, every enabled roster creator runs.

| Argument or option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `TARGET ...` | strings | enabled roster | Zero or more creators. |
| `--service` + `--creator-id` | strings | omitted | Add one explicit creator; both are required together. |
| `-o`, `--output`, `--path` | path | `.` | Output root. |
| `--save-creator-indices` | boolean | disabled | Atomically save the creator index after successful production. |
| `--mix-posts` / `--no-mix-posts` | boolean | environment config | Override `job.mix_posts`. |
| `--start-time`, `--start` | date | omitted | Inclusive publication lower bound, `YYYY-MM-DD`. |
| `--end-time`, `--end` | date | omitted | Inclusive publication upper bound, `YYYY-MM-DD`. |
| `--offset` | integer | `0` | First post index. |
| `--length` | integer | all | Maximum accepted posts per creator. |
| `--keywords` | repeated string | environment config | Include titles containing any value. |
| `--keywords-exclude` | repeated string | environment config | Deprecated title exclusion compatibility input. |

`job.creator_concurrency` limits creator production, while `job.count` limits shared file workers.

## `creator`

| Command | Arguments and options | Meaning |
| --- | --- | --- |
| `creator list` | `--json` | List roster entries as a Rich table or JSON. |
| `creator add TARGET` | `--alias NAME`, `--disabled` | Add a URL or `service:id`. |
| `creator remove TARGET` | | Remove by alias, URL, or identity. |
| `creator enable TARGET` | | Enable a saved creator. |
| `creator disable TARGET` | | Disable a saved creator. |
| `creator search` | `--name`, `--creator-id`/`--id`, `--service`, `--dump`, `--json` | Filter the public creator list. |

## `post`

| Command | Arguments and options | Meaning |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`, `--name`, `--service`, `-q`/`--query`, `-o`/`--offset`, `--dump`, `--json` | Search posts for selected creators. A direct API query is at least 3 characters and an API offset is divisible by 50. |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`, `--json` | Show current post metadata or one selected revision. |

Without `--json`, query commands deliberately omit post body text from terminal tables.

## `config`

| Command | Meaning |
| --- | --- |
| `config path` | Print the resolved project path without line wrapping. |
| `config validate` | Validate schema version, creator uniqueness, blocker types, scopes, conditions, and regular expressions. |
| `config example` | Render all dotenv settings from configuration model docstrings. |
| `config edit` | Open the optional Urwid editor and validate before saving. |

## `webui`

Install `ktoolbox[webui]` before using these commands. The default command requires a directory containing `ktoolbox.toml` and valid single-account credentials in project configuration.

| Argument or option | Default | Meaning |
| --- | --- | --- |
| `PROJECT_DIR` | `.` | Fixed synchronization project served by this process. |
| `--host` | `webui.host` | Override the listen interface. |
| `--port` | `webui.port` | Override the TCP port. |
| `--no-open` | disabled | Do not open the local URL in the default browser. |
| `webui hash-password` | | Prompt twice through hidden terminal input and print an Argon2id hash. |

The built-in server prints an HTTP security warning. See the [WebUI guide](../webui.md) before exposing it beyond localhost.

## Compatibility aliases

These aliases are hidden from help and emit one deprecation warning per invocation:

| Legacy | Replacement |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## Exit codes and streams

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Remote, creator, or download failure, including partial multi-creator success. |
| `2` | Invalid arguments or configuration. |
| `130` | User interruption. |

Tables and JSON use stdout. Logs, progress, warnings, and errors use stderr.
