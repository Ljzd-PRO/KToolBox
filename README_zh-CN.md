<div align="center">

# KToolBox

用于从 [Pawchive](https://pawchive.pw/) 下载公开投稿的异步命令行工具与 Python 客户端。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/)

[English](README.md) | [中文](README_zh-CN.md)

</div>

KToolBox v1 仅支持 Pawchive 后端。项目对 Pawchive OpenAPI 文档中的全部公开操作提供类型化访问，并明确排除需要账号登录的收藏操作。

## 功能

- 下载单篇投稿，或在一条命令中同步任意数量的作者。
- 在项目级 `ktoolbox.toml` 中维护可复用、可启停的作者清单。
- 使用有序的全局或作者级字段屏蔽器排除非作品投稿。
- 在多个操作间复用同一个类型化异步 `PawchiveClient`。
- 使用 HTTP Range 续传未完成文件，并跳过已经存在的文件。
- 按文件大小、扩展名、标题关键词和发布日期过滤，可分别控制封面与附件。
- 自定义目录结构、投稿目录名、文件名、顺序命名和年月分组。
- 保存投稿元数据、创作者索引、正文、正文图片及匹配的外部链接。
- 将并发作者生产的任务流式送入公平下载池，并使用稳定的 Rich 进度显示。
- 默认测试完全离线，基于 MockTransport，并禁止意外联网。

## 运行要求

- Python 3.10 至 3.14
- Windows、macOS 或 Linux

## 安装

推荐使用 `pipx`：

```bash
pipx install ktoolbox
```

可选的事件循环优化与终端配置编辑器依赖：

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

## 快速开始

查看命令帮助：

```bash
ktoolbox -h
ktoolbox download -h
```

![KToolBox 命令概览](docs/assets/cli-overview.png)

下载一篇投稿：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

首次同步创作者时先限制为一篇投稿：

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

使用偏移量、日期范围或标题过滤：

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

保存常用作者后，不带目标运行 `sync` 即可同步全部已启用作者：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

再次运行时会跳过已经下载的文件；文件主机支持 Range 时，未完成的临时文件会继续下载。

## 配置

KToolBox 从当前工作目录依次读取 `.env` 和 `prod.env`。嵌套字段使用 `__`：

```dotenv
# Pawchive 默认值，通常不需要覆盖。
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# 下载控制。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

配置 `KTOOLBOX_DOWNLOADER__SESSION_KEY` 后，它只会发送给文件下载请求；API 客户端永远不会发送账号会话。

`.env` 控制运行时与传输行为；项目级 `ktoolbox.toml` 保存作者清单与屏蔽器：

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["进度分享"] }] } }
```

生成配置参考、校验项目文件或启动可选终端编辑器：

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

详见[配置文档](https://ktoolbox.readthedocs.io/latest/zh/configuration/guide/)与 [`example.env`](example.env)。

## Python API

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

成功调用返回 Pydantic v2 模型；传输、HTTP 状态、认证、未找到、冲突和响应校验失败分别使用不同异常。详见 [API 文档](https://ktoolbox.readthedocs.io/latest/zh/api/)。

## 从 v0 迁移

v1 删除 Kemono/Coomer 兼容层，以及旧 `BaseAPI`、模块级 `get_*`、`APIRet` 和包装响应接口。Fire 命令已替换为 Cyclopts，请使用 `download`、`sync`、`creator`、`post` 和 `config`；隐藏旧别名暂时保留并提示弃用。请将 `KTOOLBOX_API__SESSION_KEY` 移至 `KTOOLBOX_DOWNLOADER__SESSION_KEY`，并阅读 [v1 迁移指南](https://ktoolbox.readthedocs.io/latest/zh/migration-v1/)。

仓库仍保留历史 `kemono_openapi.json`，但它只作为资料，不再是运行时支持的契约。

## 开发

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check .
poetry run mypy ktoolbox
poetry run mkdocs build --strict
```

默认测试必须保持离线，不得访问 Pawchive 或其他远程服务。

## 许可证

KToolBox 使用 [BSD 3-Clause License](LICENSE)。
