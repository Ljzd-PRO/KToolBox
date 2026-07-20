# 配置向导

KToolBox 会读取进程环境变量，以及当前工作目录中的两个可选文件：先读取 `.env`，再读取 `prod.env`。`prod.env` 中的同名值会覆盖 `.env`，进程环境变量优先级最高。

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
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

所有配置均为可选项。默认值见[配置参考](reference.md)。

## 生成或编辑配置

根据当前模型生成全部 dotenv 配置键：

```bash
ktoolbox example-env
```

可选的终端编辑器能够展示从配置模型 docstring 正确解析的字段说明：

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config-editor
```

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
