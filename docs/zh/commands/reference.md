# 命令参考

运行 `ktoolbox 命令 --help` 查看权威 Cyclopts 帮助。命令与选项使用连字符；隐藏兼容命令仍可解析旧下划线拼写。

## 全局选项

| 选项 | 含义 |
| --- | --- |
| `-h`、`--help` | 直接打印帮助，不启动分页器。 |
| `--version` | 打印已安装的 KToolBox 版本。 |
| `--install-completion` | 为检测到的 Shell 安装补全。 |
| `--config 路径` | 选择项目文件。优先级为此选项、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml`。 |
| `--verbose` | 包含诊断日志。 |
| `--quiet` | 隐藏进度与普通日志。 |
| `--plain` | 强制稳定逐行进度；非 TTY 和 `NO_COLOR` 会自动使用。 |
| `--no-color` | 禁用 ANSI 颜色。 |

不带参数运行 `ktoolbox` 会打印根帮助并成功退出。

## 命令树

| 命令 | 用途 |
| --- | --- |
| `download` | 下载一篇投稿或指定修订。 |
| `sync [目标 ...]` | 同步显式作者；无目标时同步清单中全部已启用作者。 |
| `creator list/add/remove/enable/disable/search` | 管理作者清单或搜索 Pawchive 作者。 |
| `post show/search` | 查看投稿或搜索作者投稿。 |
| `config edit/example/validate/path` | 编辑或查看环境与项目配置。 |
| `site-version` | 打印 Pawchive 应用版本。 |

## `download`

提供 Pawchive 投稿 URL，或同时提供 `--service`、`--creator-id`、`--post-id`。

| 参数或选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `POST` | 字符串 | 省略 | Pawchive 投稿或修订 URL。 |
| `--service` | 字符串 | 省略 | 作者服务。 |
| `--creator-id` | 字符串 | 省略 | 作者 ID。 |
| `--post-id` | 字符串 | 省略 | 投稿 ID。 |
| `--revision-id` | 字符串 | 省略 | 从修订列表选择此 ID。 |
| `-o`、`--output`、`--path` | 路径 | `.` | 输出根目录。 |
| `--dump-post-data` / `--no-dump-post-data` | 布尔值 | 启用 | 将已校验元数据保存到 `post.json`。 |

`download` 有意不应用作者清单屏蔽器。

## `sync`

每个 `目标` 可以是 Pawchive 作者 URL、`service:id` 或清单别名。显式目标即使在清单中已禁用也会运行；无目标时运行全部已启用作者。

| 参数或选项 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `目标 ...` | 多个字符串 | 已启用清单 | 零个或多个作者。 |
| `--service` + `--creator-id` | 字符串 | 省略 | 添加一个显式作者；二者必须同时使用。 |
| `-o`、`--output`、`--path` | 路径 | `.` | 输出根目录。 |
| `--save-creator-indices` | 布尔值 | 禁用 | 作者生产成功后原子保存索引。 |
| `--mix-posts` / `--no-mix-posts` | 布尔值 | 环境配置 | 覆盖 `job.mix_posts`。 |
| `--start-time`、`--start` | 日期 | 省略 | 包含边界的发布日期下限，`YYYY-MM-DD`。 |
| `--end-time`、`--end` | 日期 | 省略 | 包含边界的发布日期上限，`YYYY-MM-DD`。 |
| `--offset` | 整数 | `0` | 起始投稿索引。 |
| `--length` | 整数 | 全部 | 每位作者最多接受的投稿数。 |
| `--keywords` | 重复字符串 | 环境配置 | 包含标题含任一值的投稿。 |
| `--keywords-exclude` | 重复字符串 | 环境配置 | 弃用的标题排除兼容输入。 |

`job.creator_concurrency` 限制作者生产并发，`job.count` 限制共享文件工作器。

## `creator`

| 命令 | 参数与选项 | 含义 |
| --- | --- | --- |
| `creator list` | `--json` | 以 Rich 表格或 JSON 列出清单。 |
| `creator add TARGET` | `--alias 名称`、`--disabled` | 添加 URL 或 `service:id`。 |
| `creator remove TARGET` | | 按别名、URL 或身份删除。 |
| `creator enable TARGET` | | 启用已保存作者。 |
| `creator disable TARGET` | | 禁用已保存作者。 |
| `creator search` | `--name`、`--creator-id`/`--id`、`--service`、`--dump`、`--json` | 筛选公开作者列表。 |

## `post`

| 命令 | 参数与选项 | 含义 |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`、`--name`、`--service`、`-q`/`--query`、`-o`/`--offset`、`--dump`、`--json` | 搜索所选作者投稿。直接 API 查询至少 3 个字符，API 偏移量必须是 50 的倍数。 |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`、`--json` | 查看当前投稿元数据或一个指定修订。 |

未使用 `--json` 时，终端表格会有意省略投稿正文。

## `config`

| 命令 | 含义 |
| --- | --- |
| `config path` | 不换行地打印已解析项目路径。 |
| `config validate` | 校验 Schema 版本、作者唯一性、屏蔽器类型、作用域、条件与正则表达式。 |
| `config example` | 根据配置模型 docstring 渲染全部 dotenv 设置。 |
| `config edit` | 打开可选 Urwid 编辑器并在保存前校验。 |

## 兼容别名

以下别名会从帮助中隐藏，并在每次调用时提示一次弃用：

| 旧命令 | 替代命令 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## 退出码与输出流

| 状态码 | 含义 |
| --- | --- |
| `0` | 成功。 |
| `1` | 远程、作者或下载失败，包括多作者部分成功。 |
| `2` | 参数或配置无效。 |
| `130` | 用户中断。 |

表格与 JSON 写入 stdout；日志、进度、警告和错误写入 stderr。
