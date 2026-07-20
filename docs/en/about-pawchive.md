# About Pawchive

[Pawchive](https://pawchive.pw/) is the only backend supported by KToolBox v1. KToolBox uses its public API to discover creators and posts, then downloads files from the dedicated Pawchive file host.

## Default endpoints

| Purpose | Default |
| --- | --- |
| Public API | `https://pawchive.pw/api/v1` |
| Creator icons and banners | `https://pawchive.pw` |
| Post files | `https://file.pawchive.pw/data/...` |

API requests never carry an account session. `downloader.session_key`, when configured, is sent only as the `session` cookie to file-download requests.

## Supported API scope

KToolBox implements all 14 operations in the published OpenAPI document that do not require `cookieAuth`: creator and post discovery, profiles, announcements, fancards, links, post details, file-hash search, post flag status and submission, revisions, comments, and application version.

The five account-favorites operations require a signed-in Pawchive account and are intentionally excluded.

## Responsible use

Respect applicable laws, platform terms, creator rights, and storage limits. Use bounded synchronization (`--length`) and file-size limits when first testing a creator.

