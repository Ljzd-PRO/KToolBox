# KToolBox

KToolBox 是面向 [Pawchive](https://pawchive.pw/) 公开数据的异步命令行下载器、HeroUI 项目面板和类型化 Python 客户端。v1 仅支持 Pawchive，需要 Python 3.10 至 3.14。

!!! warning "v1 是全新大版本"
    这一发布线尚未经过充分的真实使用验证。请先进行有范围限制的下载，备份已有配置，并报告异常行为。由于 Kemono 已不可用，KToolBox 默认使用 Pawchive 镜像站。

## 选择你的使用路径

<div class="grid cards" markdown>

-   :material-console-line: **从命令行开始**

    安装 KToolBox，先执行一次有范围限制的下载，再阅读[命令指南](commands/guide.md)。

-   :material-view-dashboard-outline: **在浏览器中管理项目**

    安装可选面板，并根据 [WebUI 指南](webui.md)完成登录、安全设置、任务和项目配置。

-   :material-update: **从 v0 升级**

    先备份旧 dotenv 文件，再按照[迁移至 v1](migration-v1.md)处理已有下载。

-   :material-calendar-sync: **持续更新作者内容**

    先建立作者清单，再通过[自动同步](automatic-sync.md)安排周期检查。

</div>

## 功能

- 下载单篇作品，或并发同步作者清单。
- 在创建下载任务前应用有序的全局或作者级忽略规则。
- 续传未完成的文件，并跳过已经存在的文件。
- 按日期、标题、文件名模式和文件大小筛选。
- 分别控制封面、附件、正文图片、元数据和外部链接输出。
- 提供支持七种语言的持久化 WebUI，用于管理项目配置、作者清单、忽略规则、Pawchive 查询与任务生命周期。
- 通过经过验证的 Pydantic 模型提供 Pawchive OpenAPI 的全部 14 个公开操作。

需要账号认证的收藏操作明确不予实现。下载器会话密钥即使配置，也只会发送到文件主机。

## 安装

推荐使用 `pipx` 隔离安装：

```bash
pipx install ktoolbox
```

安装可选的终端配置编辑器和事件循环优化：

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

按需单独安装浏览器面板：

```bash
pipx install "ktoolbox[webui]" --force
```

## 快速开始

```bash
# 查看命令和选项。
ktoolbox -h
ktoolbox download -h

# 下载单篇作品。
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# 首次同步先限制为一篇作品，再按需扩大范围。
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![KToolBox 命令概览](../assets/cli-overview.png)

保存多个作者并同步全部已启用项：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

重复运行时会跳过现有文件。若文件服务器支持字节范围请求，带有临时后缀的未完成文件会继续下载。

未指定 `--output` 时，下载使用项目默认目录；未修改配置时就是项目目录下的 `downloads`。

## 文档地图

| 目标 | 阅读 |
| --- | --- |
| 学习日常命令 | [命令指南](commands/guide.md)和[命令参考](commands/reference.md) |
| 运行浏览器面板 | [WebUI 指南](webui.md) |
| 安排周期检查 | [自动同步](automatic-sync.md) |
| 控制目录和文件名 | [命名格式](naming.md) |
| 理解所有配置 | [配置指南](configuration/guide.md)和[配置参考](configuration/reference.md) |
| 连接其他应用 | [MCP](mcp.md)或 [Python API](api.md) |
| 升级或排查问题 | [迁移至 v1](migration-v1.md)和[常见问题](faq.md) |
