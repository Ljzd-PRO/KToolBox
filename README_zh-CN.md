<p align="center" style="text-decoration:none">
  <img align="center" src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 align="center">
  KToolBox
</h1>

<p align="center">
  KToolBox 是一个用于下载
  <a href="https://kemono.su/">Kemono.party / Kemono.su</a>
  中作品内容的实用命令行工具
</p>

<p align="center">
  <a href="https://pypi.org/project/ktoolbox" target="_blank">
    <img src="https://img.shields.io/github/v/release/Ljzd-PRO/KToolBox?logo=python" alt="Version">
  </a>

  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT"/>
  </a>

  <a href="https://github.com/Ljzd-PRO/KToolBox/activity">
    <img src="https://img.shields.io/github/last-commit/Ljzd-PRO/KToolBox/devel" alt="Last Commit"/>
  </a>

  <a href="https://codecov.io/gh/Ljzd-PRO/KToolBox" target="_blank">
      <img src="https://codecov.io/gh/Ljzd-PRO/KToolBox/branch/master/graph/badge.svg?token=5XK9CYQHQN" alt="codecov"/>
  </a>

  <a style="text-decoration:none">
    <img src="https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-blue" alt="Platform Win | Linux | macOS"/>
  </a>
</p>

<p align="center">
    <a href="./README.md">English</a> | <a href="./README_zh-CN.md">中文</a>
</p>

<img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-1.png" alt="Preview">

## 功能

- 你可以下载 Kemono 上的作品的所有文件
- 或者下载某个作者 / 画师的所有作品
- **同步**已下载完成的作者 / 画师目录至最新, 只有近期更新和新发布的作品会被下载
- 搜索作者和作品，并导出结果
- 并发下载
- 支持全平台

## 开发计划

- [ ] 增加 Fluent Design 风格的 UI 界面
- [ ] 对 Unix 平台增加 uvloop 支持

## 使用方法

### iOS 快捷指令（可选）

- 你可以用 iOS 终端 App [a-Shell](https://github.com/holzschu/a-shell) 运行 KToolBox
- 这些快捷指令可以在 a-Shell 自动安装 KToolBox 和下载 Kemono 作品
  - 你可以通过网页共享界面触发“下载 Kemono 作品”，或直接在快捷指令 App 运行
- 访问下面的快捷指令 URL 或前往 [`shortcuts/`](./shortcuts) 下载快捷指令文件

#### 英文

- [KToolBox Manager](https://www.icloud.com/shortcuts/ed981823ea424ebfaefe90e07c146c9f)
- [Download Kemono Post](https://www.icloud.com/shortcuts/dbfef8dfb3774b92b4a8f10d5e3c963c)

#### 中文

- [KToolBox 管理器](https://www.icloud.com/shortcuts/5ebf774fa3eb4c3e98c8db46485314ec)
- [下载 Kemono 作品](https://www.icloud.com/shortcuts/8d081bc5d66448b7bde19504df885ccd)

### 命令

更多信息请参考帮助命令

> **Warning**
> 此处命令返回的文本仅作为**演示**使用，部分可能已经**过时**。

- 安装 KToolBox：
    ```bash
    pip3 install ktoolbox
    ```
  - 对于 [a-Shell](https://github.com/holzschu/a-shell):
      ```bash
      pip3 install ktoolbox-pure-py
      ```

- 获取帮助总览:
    ```bash
    ktoolbox -h
    ```
    <details>
    <summary>返回文本</summary>
      <pre>
        <code>
  INFO: Showing help with the command '__main__.py -- --help'.
  <br>
  NAME
      __main__.py
  <br>
  SYNOPSIS
      __main__.py COMMAND | -
  <br>
  COMMANDS
      COMMAND is one of the following:
  <br>
     download_post
       Download a specific post
  <br>
     ...
  <br>
     sync_creator
       Sync all posts from a creator
  <br>
     version
       Show KToolBox version
        </code>
      </pre>
    </details>

  > 前往 [`ktoolbox/cli.py`](ktoolbox/cli.py) 中的 `KToolBoxCli` 查看更多信息。

- 获取某个命令的帮助信息:
    ```bash
    ktoolbox download-post -h
    ```
    <details>
    <summary>返回文本</summary>
      <pre>
        <code>
  NAME
      __main__.py sync-creator - Sync all posts from a creator
  <br>
  SYNOPSIS
      __main__.py sync-creator &lt;flags>
  <br>
  DESCRIPTION
      You can update the directory anytime after download finished, such as to update after creator published new posts.
      * If `update_from` was provided, it should be located **inside the creator directory**.
  <br>
  FLAGS
      -u, --url=URL
          Type: Optional[str]
          Default: None
          The post URL
      ...
        </code>
      </pre>
    </details>
  

- 下载指定的作品:
    ```bash
    ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
    ```
  
  > 如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被**跳过**。

- 下载作者的所有作品:
    ```bash
    ktoolbox sync-creator https://kemono.su/fanbox/user/9016
    ```
  
  默认情况下你会在作者目录下得到一个 `creator-indices.ktoolbox` 文件，你可以用它来更新目录。

  
- 更新一个作者目录:
    ```bash
    ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --update-with=./xxx/creator-indices.ktoolbox
    ```
  
  `creator-indices.ktoolbox` 包含目录下的所有作品的信息和路径。  

### 配置

- KToolBox 读取工作目录下的 **`prod.env` 文件** 或 **环境变量** 来设定配置
- **所有配置选项** 都定义在 [`ktoolbox/configuration.py`](ktoolbox/configuration.py)
- 用 `__` 来指定子选项, 例如 `KTOOLBOX_API__SCHEME` 相当于 `api.scheme`
- 所有配置选项都是可选的

#### `prod.env` 文件示例

```dotenv
# 可同时下载10个文件
KTOOLBOX_JOB__COUNT=10

# 为每个下载任务分配 102400 字节内存作为缓冲区
KTOOLBOX_DOWNLOADER__BUFFER_SIZE=102400

# 设置作品附件目录为 `./`, 这意味着所有附件将直接保存在作品目录下
# 而不会创建一个子目录来储存
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# 为Kemono API服务器和下载服务器禁用SSL证书检查
# 在Kemono服务器的证书过期时很有用 （SSL: CERTIFICATE_VERIFY_FAILED）
KTOOLBOX_SSL_VERIFY=False
```

## 其他分支

- 纯 Python 分支：[🔗pure-py](https://github.com/Ljzd-PRO/KToolBox/tree/pure-py)
  - 使用 pydantic v1 因此安装时不需要 cargo
  - 例如你可以在 iOS 的终端 App [a-Shell](https://github.com/holzschu/a-shell) 运行
  - PyPI：https://pypi.org/project/ktoolbox-pure-py/
- 开发版分支：[🔗devel](https://github.com/Ljzd-PRO/KToolBox/tree/devel)

## 关于 Kemono

官网 https://kemono.su 的介绍:

> Kemono is a public archiver for:
>  
> - Patreon
> - Pixiv Fanbox
> - Discord
> - Fantia
> - Afdian
> - Boosty
> - DLsite
> - Gumroad
> - SubscribeStar
> 
> Contributors here upload content and share it here for easy searching and organization. \
> To get started viewing content, either search for creators on the artists page, or search for content on the posts page.

## 代码覆盖率

![codecov.io](https://codecov.io/gh/Ljzd-PRO/KToolBox/graphs/sunburst.svg?token=5XK9CYQHQN)

## 许可证

KToolBox 使用 MIT 许可证.

Copyright © 2023 by Ljzd-PRO.
