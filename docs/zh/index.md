<p style="text-decoration:none">
  <img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 style="text-align: center">
  KToolBox
</h1>

<p style="text-align: center">
  KToolBox 是一个用于下载
  <a href="https://kemono.su/">Kemono.su / Kemono.party</a>
  中帖子内容的实用命令行工具
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

<p style="text-align: center">
  <a href='https://ko-fi.com/N4N51J14RW'>
    <img src='https://ko-fi.com/img/githubbutton_sm.svg' alt='ko-fi' />
  </a>
</p>

## 功能

- 支持多文件并发下载
- API 调用和下载失败后 **自动重试**
- 支持下载单个帖子以及指定的画师的 **全部帖子**
- 可 **更新已下载** 的画师目录至最新状态
- 支持自定义下载的帖子/画师的 **文件和目录名格式**、**目录结构**
  - 例如帖子目录可设置为 `[2025-01-02]_TheTitle` 的格式，图片文件设置为按顺序的 `1.jpg`、`2.jpg` 等
  - 当你希望将某作者的所有帖子图片统一存放至一个目录下，以便预览，可以使用 `job.mix_posts` 配置项搭配自定义文件名格式，你将得到几百上千张图片的目录
    - 如 `[2025-01-02]_TheTitle_1.jpg`、`[2025-01-02]_TheTitle_2.jpg`、`[2025-01-02]_TheTitle_3.jpg` 等
- 支持排除 **指定格式** 的文件或仅下载指定格式的文件
  - 例如当你不想下载庞大重复的 PSD 和压缩包文件时，可以在配置中排除 `.psd` 和 `.zip` 文件
- 支持按**文件大小**过滤下载
  - 例如，如果你想在磁盘空间不足时避免下载大型视频文件，可以在配置中设置最大文件大小限制
  - 你也可以设置最小文件大小，以跳过下载缩略图或预览图片
- 支持按帖子**标题关键词**过滤下载
  - 例如你只想下载标题中包含“表情、効果音差分”的帖子，可以使用 `sync-creator` 命令的 `--keywords` 选项
  - 如果你想排除标题中包含指定关键词的帖子，可以使用 `--keywords-exclude` 选项
- 支持按帖子发布日期**时间范围**过滤下载
- 能够解析帖子页面 HTML 多信息文本中包含的图片并下载
  - 这类帖子特征为：浏览器页面刚进入时图片可能没有加载出来，且没有预览图
- 能够收集帖子页面中列出的**网盘链接**并保存至文本文件
- 可搜索画师和帖子，并导出结果
  - 如果你希望自己处理画师和帖子数据，可以使用该功能导出 JSON 数据
- 支持全平台，并提供 iOS 快捷指令
  - 纯 Python 分支可在 iOS 的 a-Shell 或浏览器的 Pyodide 上运行
- 对于 _Coomer.st / Coomer.su / Coomer.party_ 的支持，请查看文档 [Coomer](https://ktoolbox.readthedocs.io/latest/zh/coomer/)

## 使用方法

### 安装

你可以从 [releases](https://github.com/Ljzd-PRO/KToolBox/releases) 页面下载可执行文件使用

=== "一般情况"
   推荐使用 pipx
   ```bash
   pip3 install pipx
   # Windows
   pipx install ktoolbox[urwid,winloop]
   # Linux / macOS
   pipx install ktoolbox[urwid,uvloop]
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

#### ⬇️🖼️ 下载指定的帖子
```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```
??? info "如果部分文件下载失败"
    如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被 **跳过**。
  
#### ⬇️🖌️ 下载作者的所有帖子
```bash
# 下载作者/画师的所有帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016

# 下载作者/画师最新的 10 个帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --length=10

# 下载作者/画师最新的第 11 至 15 个帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --offset=10 --length=5

# 下载作者/画师从 2024-1-1 到 2024-3-1 的帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --start-time=2024-1-1 --end-time=2024-3-1

# 下载作者/画师标题中包含“表情”的帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --keywords "表情"

# 下载作者/画师标题中包含“表情、効果音差分”的帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --keywords "表情,効果音差分"
```

### 配置

- 同时下载10个文件
- 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
- 将发布日期作为帖子目录名的开头，例如 `[2024-1-1]HelloWorld`
- 将帖子标题作为文件名的开头，例如 `HelloWorld_1.png`, `HelloWorld_2.png`, ...
- 下载帖子修订版本
- 排除下载 `.psd` 和 `.zip` 文件
- 从帖子中提取云盘链接并保存到文本文件
- ...

前往 [配置-向导](https://ktoolbox.readthedocs.io/latest/zh/configuration/guide/) 页面查看更多详情。
