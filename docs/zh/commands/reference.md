# 命令参考

运行 `ktoolbox 命令 -h` 可查看 Fire 生成的帮助。下表记录稳定的 v1 命令面；连字符形式会映射到括号中的 Python 参数名。

## 通用命令

| 命令 | 用途 |
| --- | --- |
| `version` | 显示已安装的 KToolBox 版本，并执行可选的版本检查。 |
| `site-version` | 显示 Pawchive 应用版本。 |
| `config-editor` | 打开可选的终端配置编辑器。 |
| `example-env` | 渲染完整的 dotenv 配置参考。 |

## `search-creator`

在公开作者列表中进行本地筛选。建议至少提供一个筛选条件。

| 选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `--name` | 字符串 | `None` | 不区分大小写的作者名称筛选。 |
| `--id` | 字符串 | `None` | 精确作者 ID。 |
| `--service` | 字符串 | `None` | 精确服务名。 |
| `--dump` | 路径 | `None` | 将匹配模型写入 JSON。 |

## `search-creator-post`

列出按 ID、名称或服务选中的作者投稿。

| 选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `--id` | 字符串 | `None` | 作者 ID；与 `--service` 一起使用可直接查询。 |
| `--name` | 字符串 | `None` | 从公开作者列表中选择名称匹配的作者。 |
| `--service` | 字符串 | `None` | 作者服务。 |
| `--q` | 字符串 | `None` | Pawchive 搜索词，至少 3 个字符。 |
| `--o` | 整数 | `None` | API 偏移量，非负且能被 50 整除。 |
| `--dump` | 路径 | `None` | 将匹配投稿模型写入 JSON。 |

## `get-post`

| 参数或选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `service` | 字符串 | 必填 | 作者服务。 |
| `creator-id` (`creator_id`) | 字符串 | 必填 | 作者 ID。 |
| `post-id` (`post_id`) | 字符串 | 必填 | 投稿 ID。 |
| `--revision-id` | 字符串 | `None` | 从投稿修订列表中选择该 ID。 |
| `--dump` | 路径 | `None` | 将校验后的模型写入 JSON。 |

## `download-post`

提供 `url`，或同时提供 `service`、`creator-id` 和 `post-id`。

| 参数或选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `url` | 字符串 | `None` | Pawchive 投稿或修订 URL。 |
| `--service` | 字符串 | `None` | 作者服务。 |
| `--creator-id` | 字符串 | `None` | 作者 ID。 |
| `--post-id` | 字符串 | `None` | 投稿 ID。 |
| `--revision-id` | 字符串 | `None` | 下载一个指定修订。 |
| `--path` | 路径 | `.` | 输出根目录。 |
| `--dump-post-data` | 布尔值 | `True` | 将校验后的元数据保存为 `post.json`。 |

## `sync-creator`

提供 `url`，或同时提供 `service` 和 `creator-id`。

| 参数或选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `url` | 字符串 | `None` | Pawchive 作者 URL。 |
| `--service` | 字符串 | `None` | 作者服务。 |
| `--creator-id` | 字符串 | `None` | 作者 ID。 |
| `--path` | 路径 | `.` | 输出根目录。 |
| `--save-creator-indices` | 布尔值 | `False` | 保存 `creator-indices.ktoolbox`。 |
| `--mix-posts` | 布尔值 | 配置值 | 覆盖 `job.mix_posts`。 |
| `--start-time` | 日期 | `None` | 包含边界的最早发布日期，格式 `%Y-%m-%d`。 |
| `--end-time` | 日期 | `None` | 包含边界的最晚发布日期，格式 `%Y-%m-%d`。 |
| `--offset` | 整数 | `0` | CLI 边界上的首篇投稿序号。 |
| `--length` | 整数 | `None` | 投稿数量；`None` 会获取全部页面。 |
| `--keywords` | 字符串/元组 | 配置值 | 保留标题包含任一值的投稿。 |
| `--keywords-exclude` | 字符串/元组 | 配置值 | 排除标题包含任一值的投稿。 |

面向用户的 API、校验和任务生成错误会转换为可读消息。下载工作器继续采用当前配置中的重试和进度行为。
