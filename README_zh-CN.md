<h1 align="center">
  KToolBox
</h1>

<p align="center">
  KToolBox 是一个用于下载
  <a href="https://kemono.su/">Kemono.party / Kemono.su</a>
  中作品内容的实用命令行工具
</p>

<p align="center">
    <a href="./README.md">English</a> | <a href="./README_zh-CN.md">中文</a>
</p>

## 功能

- 你可以下载 Kemono 上的作品的所有文件
- 或者下载某个作者 / 画师的所有作品
- **同步**已下载完成的作者 / 画师目录至最新, 只有近期更新和新发布的作品会被下载
- 搜索作者和作品，并导出结果
- 并发下载
- 支持全平台

## 开发计划

- [ ] 增加 Fluent Design 风格的 UI 界面

## 使用方法

更多信息请参考帮助命令

此处命令返回的文本仅作为**演示**使用，部分可能已经**过时**。

- 安装 KToolBox：
    ```bash
    pip3 install ktoolbox
    ```

- 获取帮助总览:
    ```bash
    python -m ktoolbox -h
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
    python -m ktoolbox download-post -h
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
    python -m ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
    ```
  
  > 如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被**跳过**。

- 下载作者的所有作品:
    ```bash
    python -m ktoolbox sync-creator https://kemono.su/fanbox/user/9016
    ```
  
  默认情况下你会在作者目录下得到一个 `creator-indices.ktoolbox` 文件，你可以用它来更新目录。

  
- 更新一个作者目录:
    ```bash
    python -m ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --update-with=./xxx/creator-indices.ktoolbox
    ```
  
  `creator-indices.ktoolbox` 包含目录下的所有作品的信息和路径。  

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


## 许可证

KToolBox 使用 GPLv3 许可证.

Copyright © 2023 by Ljzd-PRO.
