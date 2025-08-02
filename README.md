<p align="center" style="text-decoration:none">
  <img align="center" src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
</p>

<h1 align="center">
  KToolBox
</h1>

<p align="center">
  KToolBox is a useful CLI tool for downloading posts content in
  <a href="https://kemono.cr/">Kemono.cr / Kemono.su / Kemono.party</a>
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

## Features

- Supports concurrent downloads  
- Automatically retries API calls and downloads after failures  
- Allows downloading individual posts or **all posts** of a specified artist  
- Can **update downloaded** artist directories to the latest state  
- Supports customizable **file and directory naming formats** and **directory structures** for downloaded posts/artists  
- Enables excluding **specified file formats** or downloading only specified formats  
- Allows searching for artists and posts, with options to export results  
- Compatible with all platforms, with iOS shortcuts provided  
- For support related to _Coomer.st / Coomer.su / Coomer.party_, please refer to the documentation: [Coomer](https://ktoolbox.readthedocs.io/latest/coomer/)

## Dev Plan

- [ ] GUI
- [ ] Discord support

## Tutorial

See [documentation](https://ktoolbox.readthedocs.io/) for more details.

### Installation

You can use executables from [releases](https://github.com/Ljzd-PRO/KToolBox/releases) page

Manually install:

- Recommend
  ```bash
  pip3 install pipx
  
  # Windows
  pipx install ktoolbox[urwid,winloop]
  # Linux / macOS
  pipx install ktoolbox[urwid,uvloop]
  ```

- For [a-Shell](https://github.com/holzschu/a-shell) or [pyodide](https://pyodide.org/en/stable/), 
  or if you can only use pure Python and you cannot compile [pydantic](https://docs.pydantic.dev/latest/) v2.x.x
  ```bash
  pip3 install ktoolbox-pure-py
  ```

### Command

For more information, use the help command or goto [Command](https://ktoolbox.readthedocs.io/latest/commands/guide) page.
  
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
  
#### ⬇️🖌️ Download posts from a creator
```bash
# Download all posts of the creator/artist
ktoolbox sync-creator https://kemono.su/fanbox/user/9016

# Download latest 10 posts of the creator/artist
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --length=10

# Download latest No.11-No.15 posts of the creator/artist
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --offset=10 --length=5

# Download posts from the creator/artist from 2024-1-1 to 2024-3-1
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --start-time=2024-1-1 --end-time=2024-3-1
```

### iOS Shortcuts

Goto [Shortcuts for iOS](https://ktoolbox.readthedocs.io/latest/shortcut/) page for more details.

### Configuration

- Download 10 files at the same time
- Rename attachments in numerical order
- Prefix the post directory name with its release/publish date
- ...

Goto [Configuration-Guide](https://ktoolbox.readthedocs.io/latest/configuration/guide/) page for more details.

![KToolBox Configuration Editor](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-2.png)
![KToolBox Configuration Editor](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-3.png)

## Other Branches

- Pure Python branch: [🔗pure-py](https://github.com/Ljzd-PRO/KToolBox/tree/pure-py)
  - Use pydantic v1 so that cargo is not needed for installation
  - For example, you can use it on iOS terminal App [a-Shell](https://github.com/holzschu/a-shell)
  - 🔗[PyPI](https://pypi.org/project/ktoolbox-pure-py/)
- Development branch: [🔗devel](https://github.com/Ljzd-PRO/KToolBox/tree/devel)

## Code Coverage

![codecov.io](https://codecov.io/gh/Ljzd-PRO/KToolBox/graphs/sunburst.svg?token=5XK9CYQHQN)

## License

KToolBox is licensed under BSD 3-Clause.

Copyright © 2023 by Ljzd-PRO.
