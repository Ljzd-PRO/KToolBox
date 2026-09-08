# 配置向导

!!! tip "在 WebUI 中编辑配置"
    “全局配置”和“命名格式”页面是修改设置最简单的方式。只有需要手动文件、环境变量或部署自动化时才需要本指南；普通设置请从 [WebUI 指南](../webui.md)开始。

KToolBox 使用两层配置：

- `.env`、`prod.env` 与进程变量控制 API、传输及全局下载行为。
- `ktoolbox.toml` 保存项目命名、作者清单、自动同步计划与有序作品忽略规则。

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

# 发布时间规范化。
KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=UTC
KTOOLBOX_PUBLISHED_TIME__FALLBACK_SERVICE_TIMEZONE=UTC
KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__FANBOX=Asia/Tokyo
KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__PATREON=UTC
```

所有配置均为可选项。默认值见[配置参考](reference.md)。

创建新项目时，KToolBox 会检测主机的 IANA 时区，并且只在这次创建过程中把 `KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE` 明文写入 `.env`。已有项目即使缺少此项，也不会在读取配置或启动 WebUI 时被自动修改，而是继续使用模型默认值 `UTC`。自动同步计划的时区只决定计划何时执行；这里的 Service 时区决定如何解释 Pawchive 的 `published`。

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

推荐使用的 [WebUI](../webui.md) 会在类型化控件中显示七种语言的标签与说明，并提供最终值来源、秘密遮蔽、dotenv/TOML 原文编辑、校验、差异预览和 ETag 冲突保护。英文配置 docstring 仍是字段与语义来源，其余语言目录会接受完整字段路径检查。

日志级别等固定选项显示为 Select；具有推荐值但仍允许自定义的字段显示为 ComboBox。路径选择器只用于真正的文件或目录位置，`attachments`、`external_links.txt` 等内部产物名称保持普通文本字段。

无需打开编辑器即可查看或校验项目文件：

```bash
ktoolbox config path
ktoolbox config validate
```

项目路径优先级为全局 `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml`。写入时使用同目录临时文件和原子替换，TomlKit 会保留注释。

## 作者清单

每份项目文档都以 `schema_version = 5` 开始。Schema v5 保存项目命名格式与自动同步计划；旧下载位置仅属于命名转换工具。`default_output = "downloads"` 设置项目默认下载目录，也可以填写项目外的绝对路径。详见[命名格式指南](../naming.md)。作者按不区分大小写的 `service:id` 唯一，可选别名也必须唯一。

```toml
schema_version = 5

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

## 作品忽略规则 {#post-blockers}

忽略规则按 TOML 顺序执行，第一个命中项会排除作品。全局作用域应用于每位同步作者；作者作用域列出精确 `service:id`。禁用忽略规则会保留配置但不运行。

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` 支持递归 `any`/`all` 条件组，组与条件都可设置 `negate`。条件操作符如下：

| 操作符 | 行为 |
| --- | --- |
| `contains` | 任一所选标量包含任一配置值。 |
| `equals` | 任一所选标量等于任一配置值。 |
| `regex` | 任一所选标量匹配任一正则；配置校验时预编译。 |
| `exists` | 所选路径存在且非空；设置 `expected = false` 可反转预期。 |

比较默认不区分大小写，设置 `case_sensitive = true` 后区分。安全点路径可带 `[*]` 列表选择器，例如 `tags[*]`、`file.name`、`attachments[*].name`。缺失路径不匹配，永远不会执行 Python 表达式或任意代码。

忽略规则在列表响应阶段执行，早于详情、修订、目录、元数据和下载任务。被排除作品及其修订不会进入作者索引，也不会打印匹配文本。异步 `PostBlocker` 接口与注册表允许未来新增忽略规则类型而无需修改同步协调器。

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 仍作为弃用的隐式全局标题包含忽略规则接受。KToolBox 不会自动改写，请手动迁移到 `ktoolbox.toml`。

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
```

相对输出路径和存储桶路径基于当前工作目录解析。

## 命名模板

命名模板和作品内部名称不再属于全局 dotenv 设置。请通过 WebUI“命名格式”页配置项目 `[naming]`；首次启动完成备份迁移后，旧命名键会被拒绝。变量、校验、扫描与转换详见[命名格式指南](../naming.md)。

## 限制下载

大小限制以字节为单位，在文件加入队列前生效。省略对应变量即可禁用该边界。

```dotenv
# 最小 1 KiB，最大 1 MiB。
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# 只下载作品封面，不下载附件。
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` 控制并发作者生产者；`KTOOLBOX_JOB__COUNT` 独立控制全部作者共享的文件工作器。
