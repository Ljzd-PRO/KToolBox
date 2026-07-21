# KToolBox

KToolBox 是面向 [Pawchive](https://pawchive.pw/) 公开数据的异步命令行下载器、HeroUI 项目面板和类型化 Python 客户端。v1 仅支持 Pawchive，需要 Python 3.10 至 3.14。

## 功能

- 下载单篇作品，或并发同步作者清单。
- 在创建下载任务前应用有序的全局或作者级忽略规则。
- 续传未完成的文件，并跳过已经存在的文件。
- 按日期、标题、文件名模式和文件大小筛选。
- 分别控制封面、附件、正文图片、元数据和外部链接输出。
- 提供持久化双语 WebUI，用于管理项目配置、作者清单、忽略规则、Pawchive 查询与任务生命周期。
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

## 继续阅读

- [命令向导](commands/guide.md)
- [WebUI 指南](webui.md)
- [配置向导](configuration/guide.md)
- [Python API](api.md)
- [迁移至 v1](migration-v1.md)
- [常见问题](faq.md)
