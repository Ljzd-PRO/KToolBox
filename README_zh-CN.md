<div align="center">

# KToolBox

用于从 [Pawchive](https://pawchive.pw/) 下载公开作品的易用 WebUI、命令行工具与 Python 客户端。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/zh/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 是全新大版本，尚未经过足够广泛的实际验证，部分功能仍可能出错。遇到异常时欢迎反馈。
>
> 由于 Kemono 已不可用，KToolBox 现在默认使用镜像站 Pawchive。

## 推荐从 WebUI 开始

WebUI 是使用 KToolBox 的推荐方式。下载作品、同步作者、自动同步、命名、筛选、进度和项目配置都可在界面中完成，无需先学习命令或手动编辑配置文件。

1. 安装带 WebUI 的 KToolBox：

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. 创建项目目录并启动：

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. 浏览器会自动打开。使用终端中显示的用户名和随机密码登录。
4. 在“作者”页添加作者，再到“任务”页创建同步或下载任务。

缺少 `ktoolbox.toml` 时 KToolBox 会自动创建；默认下载到项目中的 `downloads` 目录。

![KToolBox WebUI 概览](docs/assets/webui/40-overview-showcase-desktop-light.png)

继续阅读简短的 [WebUI 指南](https://ktoolbox.readthedocs.io/latest/zh/webui/)，或从[文档首页](https://ktoolbox.readthedocs.io/latest/zh/)选择具体操作。

## WebUI 能做什么

- 下载单篇作品，并发同步多位作者。
- 管理作者清单、忽略规则、命名格式和多个自动同步计划。
- 持久保存任务历史，实时显示进度、总速度、重试，并支持暂停、停止、重新运行和安全清理。
- 通过带说明的表单管理项目配置，在需要时使用文件路径选择器。
- 支持七种界面语言、响应式布局、深浅主题和可选的 NSFW 媒体预览。
- 提供内置 MCP 服务，可连接 Codex、Claude、Cursor、VS Code 等客户端。

## 可选设置

首次运行使用自动生成的账号即可。如需固定密码，请生成哈希并写入项目 `.env`：

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

仅本机使用时可添加 `--host 127.0.0.1`。内置服务使用 HTTP；远程访问时请仅在可信网络中使用，或配置 HTTPS 反向代理。

## 进阶用法

需要脚本或终端工作流时仍可使用命令行：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

命令参数见[命令行指南](https://ktoolbox.readthedocs.io/latest/zh/commands/guide/)，AI 客户端连接见 [MCP 指南](https://ktoolbox.readthedocs.io/latest/zh/mcp/)，程序集成见 [Python API](https://ktoolbox.readthedocs.io/latest/zh/api/)。

## 从 v0 升级

升级前备份 `.env`、`prod.env` 和现有下载。WebUI 会检测旧命名设置，并引导完成配置与目录转换。请先阅读 [v1 迁移指南](https://ktoolbox.readthedocs.io/latest/zh/migration-v1/)；迁移或任务失败时可查看[问题排查](https://ktoolbox.readthedocs.io/latest/zh/faq/)。

## 开发

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

默认测试完全离线，不得访问 Pawchive 或其他远程服务。

## 许可证

KToolBox 使用 [BSD 3-Clause License](LICENSE)。
