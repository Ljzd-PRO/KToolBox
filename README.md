<p align="center" style="text-decoration:none">
  <img align="center" src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 align="center">
  KToolBox
</h1>

<p align="center">
  KToolBox is a useful CLI tool for downloading posts content in
  <a href="https://kemono.su/">Kemono.party / Kemono.su</a>
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

<img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-1.png" alt="Preview">

## Features

- You can download all files from a specific post from Kemono
- Or download **all post** from a specific creator / artist from Kemono
- **Sync** the downloaded creator / artist directory to latest, \
  download the posts that recently updated or published only
- Search creator and post, then dump the results
- Concurrently download the files
- Support all platform

## Dev Plan

- [ ] Add a Fluent Design style GUI
- [x] Add uvloop support for Unix platform

## Tutorial

See [documentation](https://ktoolbox.readthedocs.io/) for more details.

### Installation

- Normal
  ```bash
  pip3 install ktoolbox
  ```

- For [a-Shell](https://github.com/holzschu/a-shell)
  ```bash
  pip3 install ktoolbox-pure-py
  ```

### Command

For more information, use the help command or goto [Command](https://ktoolbox.readthedocs.io/latest/commands/) page.
  
#### ❓ Get general help
```bash
ktoolbox -h
```
  
#### ❓ Get help of a command
```bash
ktoolbox download-post -h
```

#### ⬇️🖼️ Download a specific post
```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```

If some files failed to download, you can try to execute the command line again, 
the downloaded files will be **skipped**.
  
#### ⬇️🖌️ Download all posts from a creator
```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/9016
```

> By default, you will get a `creator-indices.ktoolbox` file in the creator directory, 
> you can use it to update the directory anytime.
  

#### 🔄️ Update a downloaded creator directory
```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --update-with=./xxx/creator-indices.ktoolbox
```

The `creator-indices.ktoolbox` file contains the information and filepath of posts inside the directory.

### iOS Shortcuts

Goto [Shortcuts for iOS](https://ktoolbox.readthedocs.io/latest/shortcut/) page for more details.

### Configuration

Goto [Configuration-Guide](https://ktoolbox.readthedocs.io/latest/configuration/guide/) page for more details.

## Other Branches

- Pure Python branch: [🔗pure-py](https://github.com/Ljzd-PRO/KToolBox/tree/pure-py)
  - Use pydantic v1 so that cargo is not needed for installation
  - For example, you can use it on iOS terminal App [a-Shell](https://github.com/holzschu/a-shell)
  - 🔗[PyPI](https://pypi.org/project/ktoolbox-pure-py/)
- Development branch: [🔗devel](https://github.com/Ljzd-PRO/KToolBox/tree/devel)

## About Kemono

Description from https://kemono.su :

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

## Code Coverage

![codecov.io](https://codecov.io/gh/Ljzd-PRO/KToolBox/graphs/sunburst.svg?token=5XK9CYQHQN)

## License

KToolBox is licensed under MIT.

Copyright © 2023 by Ljzd-PRO.
