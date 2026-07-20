# Configuration Reference

Environment names start with `KTOOLBOX_` and join nested model fields with `__`. Types shown as `path`, `set`, or `list` are parsed by Pydantic; use JSON arrays for collections in dotenv files.

## Root

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `ssl_verify` | boolean | `True` | Verify TLS certificates for API and download requests. |
| `json_dump_indent` | integer | `4` | Indentation used for JSON output. |
| `use_uvloop` | boolean | `True` | Use uvloop on Unix or winloop on Windows when installed. |

## `api`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | API URL scheme. |
| `netloc` | string | `pawchive.pw` | API host. |
| `statics_netloc` | string | `pawchive.pw` | Static creator-asset host. |
| `path` | string | `/api/v1` | API root path. |
| `timeout` | float | `5.0` | Per-request timeout in seconds. |
| `retry_times` | integer | `3` | Additional attempts for transport, `429`, and `5xx` failures. |
| `retry_interval` | float | `2.0` | Delay between API attempts in seconds. |

The API group intentionally contains no session key.

## `downloader`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | File URL scheme. |
| `files_netloc` | string | `file.pawchive.pw` | Pawchive file host. |
| `file_path_prefix` | string | `/data` | Prefix added to API file paths. |
| `session_key` | string | empty | Optional cookie sent only to file requests. |
| `timeout` | float | `30.0` | File-request timeout in seconds. |
| `encoding` | string | `utf-8` | Encoding for names and extracted text. |
| `buffer_size` | integer | `20480` | Buffered file I/O size in bytes. |
| `chunk_size` | integer | `1024` | Stream chunk size in bytes. |
| `temp_suffix` | string | `tmp` | Suffix for incomplete downloads. |
| `retry_times` | integer | `10` | Additional download attempts. |
| `retry_stop_never` | boolean | `False` | Retry forever and ignore `retry_times`. |
| `retry_interval` | float | `3.0` | Delay between download attempts in seconds. |
| `tps_limit` | float | `5.0` | Maximum new connections per second. |
| `use_bucket` | boolean | `False` | Enable content-addressed local hard-link storage. |
| `bucket_path` | path | `.ktoolbox/bucket_storage` | Local bucket directory. |
| `reverse_proxy` | string | `{}` | Download URL template; `{}` is replaced by the source URL. |
| `keep_metadata` | boolean | `True` | Preserve remote modification metadata when available. |

Bucket mode disables itself when the target filesystem cannot create hard links.

## `job.post_structure`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `attachments` | path | `attachments` | Attachment subdirectory. Use `./` for the post root. |
| `content` | path | `content.txt` | Extracted content file. |
| `external_links` | path | `external_links.txt` | Extracted external-link file. |
| `file` | string | `{id}_{}` | Cover-file naming template. |
| `revisions` | path | `revisions` | Revision subdirectory. |

## `job`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `count` | integer | `4` | Concurrent download workers. |
| `include_revisions` | boolean | `False` | Include all known revisions for a current post. |
| `post_dirname_format` | string | `{title}` | Per-post directory template. |
| `mix_posts` | boolean | `False` | Store all creator files together without post directories. |
| `sequential_filename` | boolean | `False` | Rename attachments in numeric order. |
| `sequential_filename_excludes` | set | empty | Extensions that retain original names. |
| `filename_format` | string | `{}` | Attachment filename template. |
| `allow_list` | set | empty | Unix shell filename patterns to include. |
| `block_list` | set | empty | Unix shell filename patterns to exclude. |
| `extract_content` | boolean | `False` | Save post text separately. |
| `extract_content_images` | boolean | `False` | Download images referenced in post content. |
| `extract_external_links` | boolean | `False` | Save matching external links from content. |
| `external_link_patterns` | list | built in | Regular expressions used for external-link extraction. |
| `group_by_year` | boolean | `False` | Group post directories by publication year. |
| `group_by_month` | boolean | `False` | Group by month; requires year grouping. |
| `year_dirname_format` | string | `{year}` | Year-directory template. |
| `month_dirname_format` | string | `{year}-{month:02d}` | Month-directory template. |
| `keywords` | set | empty | Case-insensitive title terms to include. |
| `keywords_exclude` | set | empty | Case-insensitive title terms to exclude. |
| `download_file` | boolean | `True` | Download the main post file, usually the cover. |
| `download_attachments` | boolean | `True` | Download attachments. |
| `min_file_size` | integer / omitted | omitted | Skip files smaller than this byte count. |
| `max_file_size` | integer / omitted | omitted | Skip files larger than this byte count. |

Naming templates accept `id`, `user`, `service`, `title`, `added`, `published`, and `edited`. Year and month templates accept `year` and `month`.

## `logger`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | path / omitted | omitted | Log-file path; omitted disables file logging. |
| `level` | string / integer | `DEBUG` | Minimum log level. |
| `rotation` | string / integer / time | `1 week` | Loguru rotation condition. |
