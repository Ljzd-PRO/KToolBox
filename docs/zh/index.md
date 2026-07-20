# KToolBox

KToolBox 是面向 [Pawchive](https://pawchive.pw/) 公开数据的异步命令行下载器和类型化 Python 客户端。v1 仅支持 Pawchive，需要 Python 3.10 至 3.14。

## 功能

- 下载单篇投稿、指定修订，或同步作者投稿。
- 续传未完成的文件，并跳过已经存在的文件。
- 按日期、标题、文件名模式和文件大小筛选。
- 分别控制封面、附件、正文图片、元数据和外部链接输出。
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

## 快速开始

```bash
# 查看命令和选项。
ktoolbox -h
ktoolbox download-post -h

# 下载单篇投稿。
ktoolbox download-post https://pawchive.pw/fanbox/user/6570768/post/1836570

# 首次同步先限制为一篇投稿，再按需扩大范围。
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --length=1
```

重复运行时会跳过现有文件。若文件服务器支持字节范围请求，带有临时后缀的未完成文件会继续下载。

## 继续阅读

- [命令向导](commands/guide.md)
- [配置向导](configuration/guide.md)
- [Python API](api.md)
- [迁移至 v1](migration-v1.md)
- [常见问题](faq.md)
