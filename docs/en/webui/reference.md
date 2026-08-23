# WebUI deployment reference

Use this reference when operating or backing up a WebUI instance after the initial secure setup.

## About

The About page gathers package and runtime information with safe links to documentation, source, and issue reporting. URLs and listener addresses are displayed in inline code styling, and external links open in a new tab with isolation attributes.

![About page on a narrow dark screen](../../assets/webui/32-about-mobile-dark.png)

## WebUI environment reference

| Variable | Default | Meaning |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | Listen interface. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | Listen port, 1–65535. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | Open the local URL after startup. |
| `KTOOLBOX_WEBUI__USERNAME` | empty → `admin` at startup | Optional single-account username. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | empty | Preferred stable Argon2id hash. |
| `KTOOLBOX_WEBUI__PASSWORD` | empty → random per startup | Plaintext fallback; ignored when a hash exists. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | Concurrent top-level tasks, 1–16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | Session lifetime since last use. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | Maximum session lifetime since login. |

Back up `ktoolbox.toml`, local dotenv files, and `.ktoolbox/webui.sqlite3` together when task history matters. Do not copy the database while the WebUI is running.

## Multilingual browser verification

The seven locale catalogs are exercised on desktop and mobile in light and dark themes. Representative verified states are shown below; user content and filesystem paths remain in their original form.

![French configuration on mobile](../../assets/webui/24-configuration-mobile-fr.png)

![Russian remote path picker on mobile](../../assets/webui/25-path-picker-mobile-ru.png)

## Related WebUI guides

- [Installation and security overview](../webui.md)
- [Project workflows](project-workflows.md)
- [Tasks and live updates](tasks.md)
- [Deployment reference](reference.md)
