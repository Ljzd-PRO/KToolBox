<p align="center" style="text-decoration:none">
  <img align="center" src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 align="center">
  KToolBox
</h1>

<p align="center">
  KToolBox 是一个用于下载
  <a href="https://kemono.su/">Kemono.su / Kemono.party</a>
  中作品内容的实用命令行工具
</p>

<p align="center">
  <a href="https://pypi.org/project/ktoolbox" target="_blank">
    <img src="https://img.shields.io/github/v/release/Ljzd-PRO/KToolBox?logo=python" alt="Version">
  </a>

<a href="https://pypi.org/project/ktoolbox" target="_blank">
    <img src="https://img.shields.io/pypi/dm/ktoolbox?label=pypi-downloads" alt="PyPI Downloads">
  </a>

  <a href="https://github.com/Ljzd-PRO/KToolBox/releases" target="_blank">
    <img src="https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/total?label=github-downloads" alt="GitHub Release Downloads">
  </a>

  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/Ljzd-PRO/KToolBox" alt="BSD 3-Clause"/>
  </a>

  <a href="https://github.com/Ljzd-PRO/KToolBox/activity">
    <img src="https://img.shields.io/github/last-commit/Ljzd-PRO/KToolBox/devel" alt="Last Commit"/>
  </a>

  <a href="https://codecov.io/gh/Ljzd-PRO/KToolBox" target="_blank">
      <img src="https://codecov.io/gh/Ljzd-PRO/KToolBox/branch/master/graph/badge.svg?token=5XK9CYQHQN" alt="codecov"/>
  </a>

  <a href='https://ktoolbox.readthedocs.io/'>
    <img src='https://readthedocs.org/projects/ktoolbox/badge/?version=latest' alt='Documentation Status' />
  </a>

  <a style="text-decoration:none">
    <img src="https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-blue" alt="Platform Win | Linux | macOS"/>
  </a>
</p>

<p align="center">
    <a href="./README.md">English</a> | <a href="./README_zh-CN.md">中文</a>
</p>

## 功能

- 支持并发下载
- API 调用和下载失败后 **自动重试**
- 支持下载单个作品以及指定的画师的 **所有作品**
- 可 **更新已下载** 的画师目录至最新状态
- 支持自定义下载的作品/画师 **文件和目录名格式**、**目录结构**
- 支持排除 **指定格式** 的文件或仅下载指定格式的文件
- 可搜索画师和作品，并导出结果
- 支持全平台，并提供 iOS 快捷指令
- 对于 Coomer.su / Coomer.party 的支持，请查看文档 [Coomer](https://ktoolbox.readthedocs.io/latest/zh/coomer/)

## 开发计划

- [ ] GUI
- [ ] Discord 下载支持

## 使用方法

前往 [文档](https://ktoolbox.readthedocs.io/latest/zh/) 查看更多详情。

### 安装

你可以从 [releases](https://github.com/Ljzd-PRO/KToolBox/releases) 页面下载可执行文件使用

手动安装：

- 推荐
  ```bash
  pip3 install pipx
  pipx install ktoolbox
  ```

- 对于 iOS [a-Shell](https://github.com/holzschu/a-shell)
  ```bash
  pip3 install ktoolbox-pure-py
  ```

### 命令

使用帮助命令或前往 [命令](https://ktoolbox.readthedocs.io/latest/zh/commands/guide/) 页面查看更多帮助。
  
#### ❓ 获取帮助总览
```bash
ktoolbox -h
```
  
#### ❓ 获取某个命令的帮助信息
```bash
ktoolbox download-post -h
```

#### ⬇️🖼️ 下载指定的作品
```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```

如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被 **跳过**。
  
#### ⬇️🖌️ 下载作者的所有作品
```bash
# 下载作者/画师的所有作品
ktoolbox sync-creator https://kemono.su/fanbox/user/9016

# 下载作者/画师最新的 10 个作品
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --length=10

# 下载作者/画师最新的第 11 至 15 个作品
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --offset=10 --length=5

# 下载作者/画师从 2024-1-1 到 2024-3-1 的作品
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --start-time=2024-1-1 --end-time=2024-3-1
```

### iOS 快捷指令

前往 [iOS 快捷指令](https://ktoolbox.readthedocs.io/latest/zh/shortcut/) 页面查看更多详情。

### 配置

- 同时下载10个文件
- 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
- 将发布日期作为作品目录名的开头，例如 `[2024-1-1]HelloWorld`
- ...

前往 [配置-向导](https://ktoolbox.readthedocs.io/latest/zh/configuration/guide/) 页面查看更多详情。

![KToolBox 配置编辑器](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-2.png)
![KToolBox 配置编辑器](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-3.png)

## 其他分支

- 纯 Python 分支：[🔗pure-py](https://github.com/Ljzd-PRO/KToolBox/tree/pure-py)
  - 使用 pydantic v1 因此安装时不需要 cargo
  - 例如你可以在 iOS 的终端 App [a-Shell](https://github.com/holzschu/a-shell) 运行
  - 🔗[PyPI](https://pypi.org/project/ktoolbox-pure-py/)
- 开发版分支：[🔗devel](https://github.com/Ljzd-PRO/KToolBox/tree/devel)

## 代码覆盖率

![codecov.io](https://codecov.io/gh/Ljzd-PRO/KToolBox/graphs/sunburst.svg?token=5XK9CYQHQN)

## 许可证

KToolBox 使用 BSD 3-Clause 许可证.

Copyright © 2023 by Ljzd-PRO.
