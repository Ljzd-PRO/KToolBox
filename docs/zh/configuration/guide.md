# 配置向导

KToolBox 使用两层配置：

- `.env`、`prod.env` 与进程变量控制 API、传输、命名及全局下载行为。
- `ktoolbox.toml` 保存项目作者清单与有序投稿屏蔽器。

KToolBox 会从当前工作目录先读取 `.env`，再读取 `prod.env`。`prod.env` 中的同名值会覆盖 `.env`，进程环境变量优先级最高。

嵌套字段使用双下划线。例如，`KTOOLBOX_API__TIMEOUT` 对应 `config.api.timeout`。

```dotenv
# Pawchive API 请求。
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# 文件传输。
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# 下载任务。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

所有配置均为可选项。默认值见[配置参考](reference.md)。

## 生成或编辑配置

根据当前模型生成全部 dotenv 配置键：

```bash
ktoolbox config example
```

可选的终端编辑器能够展示从配置模型 docstring 正确解析的字段说明：

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

可选 [WebUI](../webui.md) 会在类型化控件中显示同一套双语 docstring 说明，并提供最终值来源、秘密遮蔽、dotenv/TOML 原文编辑、校验、差异预览和 ETag 冲突保护。

无需打开编辑器即可查看或校验项目文件：

```bash
ktoolbox config path
ktoolbox config validate
```

项目路径优先级为全局 `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml`。写入时使用同目录临时文件和原子替换，TomlKit 会保留注释。

## 作者清单

每份项目文档都以 `schema_version = 1` 开始。作者按不区分大小写的 `service:id` 唯一，可选别名也必须唯一。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

简单清单项建议通过 `creator add`、`remove`、`enable`、`disable` 管理。无目标 `sync` 使用全部已启用项；显式别名或身份无论 `enabled` 状态都会运行。

## 投稿屏蔽器 {#post-blockers}

屏蔽器按 TOML 顺序执行，第一个命中项会排除投稿。全局作用域应用于每位同步作者；作者作用域列出精确 `service:id`。禁用屏蔽器会保留配置但不运行。

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["生活分享", "日常记录"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["进度|练习"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` 支持递归 `any`/`all` 条件组，组与条件都可设置 `negate`。条件操作符如下：

| 操作符 | 行为 |
| --- | --- |
| `contains` | 任一所选标量包含任一配置值。 |
| `equals` | 任一所选标量等于任一配置值。 |
| `regex` | 任一所选标量匹配任一正则；配置校验时预编译。 |
| `exists` | 所选路径存在且非空；设置 `expected = false` 可反转预期。 |

比较默认不区分大小写，设置 `case_sensitive = true` 后区分。安全点路径可带 `[*]` 列表选择器，例如 `tags[*]`、`file.name`、`attachments[*].name`。缺失路径不匹配，永远不会执行 Python 表达式或任意代码。

屏蔽器在列表响应阶段执行，早于详情、修订、目录、元数据和下载任务。被排除投稿及其修订不会进入作者索引，也不会打印匹配文本。异步 `PostBlocker` 接口与注册表允许未来新增屏蔽器类型而无需修改同步协调器。

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 仍作为弃用的隐式全局标题包含屏蔽器接受。KToolBox 不会自动改写，请手动迁移到 `ktoolbox.toml`。

## Pawchive 端点

v1 默认值通常不需要覆盖：

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` 为可选配置，只会附加到文件下载器发出的请求。它绝不会由不提供账号会话能力的 `PawchiveClient` 发送。

## 集合与路径

dotenv 文件中的集合和列表使用 JSON 数组：

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

相对输出路径和存储桶路径基于当前工作目录解析。将附件路径设为 `./`，可把附件直接放入投稿目录：

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 命名模板

投稿和文件模板可使用 `id`、`user`、`service`、`title`、`added`、`published` 和 `edited`。文件模板中的空 `{}` 代表原始或按顺序生成的基础文件名。

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

使用 `{title:.60}` 这样的 Python 格式精度可规避文件系统长度限制。

## 限制下载

大小限制以字节为单位，在文件加入队列前生效。省略对应变量即可禁用该边界。

```dotenv
# 最小 1 KiB，最大 1 MiB。
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# 只下载投稿封面，不下载附件。
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` 控制并发作者生产者；`KTOOLBOX_JOB__COUNT` 独立控制全部作者共享的文件工作器。
