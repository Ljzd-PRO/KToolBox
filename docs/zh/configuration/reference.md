# 配置参考

环境变量名称以 `KTOOLBOX_` 开头，嵌套模型字段使用 `__` 连接。表中标为路径、集合或列表的类型由 Pydantic 解析；dotenv 文件中的集合应使用 JSON 数组。

## 根配置

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `ssl_verify` | 布尔值 | `True` | 为 API 和下载请求校验 TLS 证书。 |
| `json_dump_indent` | 整数 | `4` | JSON 输出的缩进。 |
| `use_uvloop` | 布尔值 | `True` | 已安装时，在 Unix 使用 uvloop，在 Windows 使用 winloop。 |

## `api`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | API URL 协议。 |
| `netloc` | 字符串 | `pawchive.pw` | API 主机。 |
| `statics_netloc` | 字符串 | `pawchive.pw` | 作者静态资源主机。 |
| `path` | 字符串 | `/api/v1` | API 根路径。 |
| `timeout` | 浮点数 | `5.0` | 单次请求超时秒数。 |
| `retry_times` | 整数 | `3` | 传输错误、`429` 和 `5xx` 的额外尝试次数。 |
| `retry_interval` | 浮点数 | `2.0` | API 尝试间隔秒数。 |

API 配置组有意不包含会话密钥。

## `downloader`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | 文件 URL 协议。 |
| `files_netloc` | 字符串 | `file.pawchive.pw` | Pawchive 文件主机。 |
| `file_path_prefix` | 字符串 | `/data` | 添加到 API 文件路径前的前缀。 |
| `session_key` | 字符串 | 空 | 只发送给文件请求的可选 Cookie。 |
| `timeout` | 浮点数 | `30.0` | 文件请求超时秒数。 |
| `encoding` | 字符串 | `utf-8` | 名称和提取文本的编码。 |
| `buffer_size` | 整数 | `20480` | 文件 I/O 缓冲区字节数。 |
| `chunk_size` | 整数 | `1024` | 数据流分块字节数。 |
| `temp_suffix` | 字符串 | `tmp` | 未完成下载的后缀。 |
| `retry_times` | 整数 | `10` | 下载的额外尝试次数。 |
| `retry_stop_never` | 布尔值 | `False` | 永久重试并忽略 `retry_times`。 |
| `retry_interval` | 浮点数 | `3.0` | 下载尝试间隔秒数。 |
| `tps_limit` | 浮点数 | `5.0` | 每秒新建连接上限。 |
| `use_bucket` | 布尔值 | `False` | 启用按内容寻址的本地硬链接存储。 |
| `bucket_path` | 路径 | `.ktoolbox/bucket_storage` | 本地存储桶目录。 |
| `reverse_proxy` | 字符串 | `{}` | 下载 URL 模板；`{}` 替换为源 URL。 |
| `keep_metadata` | 布尔值 | `True` | 可用时保留远端修改时间等元数据。 |

目标文件系统无法创建硬链接时，存储桶模式会自动禁用。

## `job.post_structure`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `attachments` | 路径 | `attachments` | 附件子目录；使用 `./` 表示投稿根目录。 |
| `content` | 路径 | `content.txt` | 提取的正文文件。 |
| `external_links` | 路径 | `external_links.txt` | 提取的外部链接文件。 |
| `file` | 字符串 | `{id}_{}` | 封面文件命名模板。 |
| `revisions` | 路径 | `revisions` | 修订子目录。 |

## `job`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `count` | 整数 | `4` | 并发下载工作器数量。 |
| `creator_concurrency` | 整数 | `4` | 向共享文件工作器提供任务的并发作者生产者数量。 |
| `include_revisions` | 布尔值 | `False` | 为当前投稿包含所有已知修订。 |
| `post_dirname_format` | 字符串 | `{title}` | 每篇投稿的目录模板。 |
| `mix_posts` | 布尔值 | `False` | 不建投稿目录，将作者文件存放在一起。 |
| `sequential_filename` | 布尔值 | `False` | 按数字顺序重命名附件。 |
| `sequential_filename_excludes` | 集合 | 空 | 保留原名的扩展名。 |
| `filename_format` | 字符串 | `{}` | 附件文件名模板。 |
| `allow_list` | 集合 | 空 | 允许的 Unix shell 文件名模式。 |
| `block_list` | 集合 | 空 | 排除的 Unix shell 文件名模式。 |
| `extract_content` | 布尔值 | `False` | 单独保存投稿正文。 |
| `extract_content_images` | 布尔值 | `False` | 下载正文引用的图片。 |
| `extract_external_links` | 布尔值 | `False` | 保存正文中匹配的外部链接。 |
| `external_link_patterns` | 列表 | 内置 | 提取外部链接使用的正则表达式。 |
| `group_by_year` | 布尔值 | `False` | 按发布日期年份分组投稿目录。 |
| `group_by_month` | 布尔值 | `False` | 按月份分组，需要启用年份分组。 |
| `year_dirname_format` | 字符串 | `{year}` | 年份目录模板。 |
| `month_dirname_format` | 字符串 | `{year}-{month:02d}` | 月份目录模板。 |
| `keywords` | 集合 | 空 | 标题需包含的不区分大小写词语。 |
| `keywords_exclude` | 集合 | 空 | 弃用的标题排除项，会转换为隐式全局屏蔽器。 |
| `download_file` | 布尔值 | `True` | 下载投稿主文件，通常为封面。 |
| `download_attachments` | 布尔值 | `True` | 下载附件。 |
| `min_file_size` | 整数 / 省略 | 省略 | 跳过小于该字节数的文件。 |
| `max_file_size` | 整数 / 省略 | 省略 | 跳过大于该字节数的文件。 |

命名模板接受 `id`、`user`、`service`、`title`、`added`、`published` 和 `edited`。年份与月份模板接受 `year` 和 `month`。

## 项目 `ktoolbox.toml`

项目文档独立于环境配置。路径依次从全局 `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml` 解析。

### 根字段

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | 字面量 `1` | `1` | 项目 Schema 版本，其他值会被拒绝。 |
| `creators` | 表数组 | 空 | 已保存作者清单。 |
| `blockers` | 表数组 | 空 | 有序屏蔽器定义。 |

### 作者项

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `service` | 非空字符串 | 必填 | Pawchive 服务。 |
| `creator_id` | 非空字符串 | 必填 | Pawchive 作者 ID。 |
| `alias` | 字符串 / 省略 | 省略 | 唯一 CLI 目标，禁止 `:`。 |
| `enabled` | 布尔值 | `True` | 是否包含在无目标 `sync` 中。 |

### 屏蔽器项

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `id` | 标识符 | 必填 | 唯一 ID，只允许字母、数字、`.`、`_`、`-`。 |
| `type` | 字符串 | `field-match` | 已注册屏蔽器实现，未知类型会被拒绝。 |
| `enabled` | 布尔值 | `True` | 是否参与求值。 |
| `scope.mode` | `global` / `creators` | `global` | 全局应用或仅作用于所选身份。 |
| `scope.creators` | `service:id` 列表 | 空 | 作者作用域必须非空；全局作用域禁止填写。 |
| `options.rule` | 条件组 | `field-match` 必填 | 根递归规则。 |

条件组使用 `kind = "group"`、`mode = "any"` 或 `"all"`、非空 `conditions` 列表及可选 `negate`。字段条件使用 `kind = "field"`、安全点路径 `field`、`contains`、`equals`、`regex`、`exists` 之一，以及可选 `case_sensitive`、`negate` 或 `expected`。非 `exists` 操作符要求非空 `values`；`exists` 禁止 `values`。

## `webui`

仅在安装 `ktoolbox[webui]` 后需要这些配置。项目没有默认凭据，缺少用户名或两种密码配置时，服务会拒绝启动。

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `host` | 字符串 | `0.0.0.0` | HTTP 监听接口；可信局域网以外建议使用 `127.0.0.1`。 |
| `port` | 整数 | `8789` | HTTP 监听端口，范围 1–65535。 |
| `open_browser` | 布尔值 | `True` | 启动后打开本机面板 URL。 |
| `username` | 字符串 | 空 | 单账户必填用户名。 |
| `password_hash` | 秘密字符串 | 空 | 推荐的 Argon2id 密码哈希。 |
| `password` | 秘密字符串 | 空 | 明文后备值；设置 `password_hash` 后忽略。 |
| `max_active_tasks` | 整数 | `2` | 顶层并发任务数，范围 1–16。 |
| `session_idle_hours` | 整数 | `24` | 从最后一次使用开始计算的会话期限。 |
| `session_absolute_hours` | 整数 | `168` | 从登录时间开始计算的会话最长期限。 |

环境变量仍使用常规前缀，例如 `KTOOLBOX_WEBUI__PASSWORD_HASH`。请用 `ktoolbox webui hash-password` 生成哈希；Argon2 哈希包含 `$`，写入 dotenv 时应加引号。命令行 `--host`、`--port`、`--no-open` 只覆盖一次启动。

## `logger`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `path` | 路径 / 省略 | 省略 | 日志文件路径；省略时禁用文件日志。 |
| `level` | 字符串 / 整数 | `DEBUG` | 最低日志级别。 |
| `rotation` | 字符串 / 整数 / 时间 | `1 week` | Loguru 轮换条件。 |
