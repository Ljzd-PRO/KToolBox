<p style="text-decoration:none">
  <img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 style="text-align: center">
  KToolBox
</h1>

<p style="text-align: center">
  KToolBox 是一个用于下载
  <a href="https://kemono.su/">Kemono.su / Kemono.party</a>
  中作品内容的实用命令行工具
</p>

<p style="text-align: center">
  <a href="https://pypi.org/project/ktoolbox" target="_blank">
    <img src="https://img.shields.io/github/v/release/Ljzd-PRO/KToolBox?logo=python" alt="Version">
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

## 使用方法

### 安装

你可以从 [releases](https://github.com/Ljzd-PRO/KToolBox/releases) 页面下载可执行文件使用

=== "一般情况"
   推荐使用 pipx
   ```bash
   pip3 install pipx
   pipx install ktoolbox
   ```

=== "纯 Python"
   如果你在使用 [pyodide](https://pyodide.org/en/stable/)，或者如果你只能使用纯Python，无法编译 [pydantic](https://docs.pydantic.dev/latest/) v2.x.x
   ```bash
   pip3 install pipx
   pipx install ktoolbox
   ```

=== "对于 iOS a-Shell"
    ```bash
    pip3 install ktoolbox-pure-py
    ```
    !!! info "关于 a-Shell"
        [a-Shell](https://github.com/holzschu/a-shell) 是一个 iOS 终端 App，它只能运行纯 Python 脚本

### 命令

使用帮助命令或前往 [命令](commands/guide.md) 页面查看更多帮助。
  
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
??? info "如果部分文件下载失败"
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

### 配置

- 同时下载10个文件
- 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
- 将发布日期作为作品目录名的开头，例如 `[2024-1-1]HelloWorld`
- ...

前往 [配置-向导](https://ktoolbox.readthedocs.io/latest/zh/configuration/guide/) 页面查看更多详情。
