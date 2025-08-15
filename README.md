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

<p align="center">
  <a href='https://ko-fi.com/N4N51J14RW'>
    <img src='https://ko-fi.com/img/githubbutton_sm.svg' alt='ko-fi' />
  </a>
</p>

## Features

- Support concurrent downloading of multiple files
- Automatically retry on API call or download failure
- Support downloading a single post or **all posts** of a specified artist
- Can **update downloaded** artist directories to the latest state
- Support customizing the **file and directory name format** and **directory structure** for downloaded posts/artists
  - For example, the post directory can be set to the format `[2025-01-02]_TheTitle`, and image files can be named sequentially as `1.jpg`, `2.jpg`, etc.
  - If you want to store all images from an artist's posts in a single directory for preview, you can use the `job.mix_posts` config option with a custom filename format to get a directory with hundreds or thousands of images
    - Such as `[2025-01-02]_TheTitle_1.jpg`, `[2025-01-02]_TheTitle_2.jpg`, `[2025-01-02]_TheTitle_3.jpg`, etc.
- Support excluding **specified file formats** or downloading only specified formats
  - For example, if you don't want to download large and duplicate PSD or archive files, you can exclude `.psd` and `.zip` files in the config
- Support filtering downloads by post **title keywords**
  - For example, if you only want to download posts whose titles contain "表情" or "効果音差分", you can use the `sync-creator` command with the `--keywords` option
  - You can also exclude posts with specific keywords in the title using the `--keywords-exclude` option
- Support filtering downloads by post **publish date range**
- Can parse and download images contained in the multi-info text of the post page HTML
  - These posts are characterized by images not loading immediately when the browser enters the page, and no preview images
- Can collect **cloud drive links** listed on the post page and save them to a text file
- Can search for artists and posts, and export results
  - If you want to process artist and post data yourself, you can use this feature to export JSON data
- Cross-platform support, with iOS shortcuts provided
  - The pure Python branch can run on iOS a-Shell or in the browser via Pyodide
- For _Coomer.st / Coomer.su / Coomer.party_ support, please refer to the documentation [Coomer](https://ktoolbox.readthedocs.io/latest/zh/coomer/)

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

# Download posts from the creator/artist whose title contains "表情"
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --keywords "表情"

# Download posts from the creator/artist whose title contains "表情" or "効果音差分"
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --keywords "表情,効果音差分"
```

### Configuration

- Download 10 files at the same time
- Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
- Prefix the post directory name with its release/publish date, e.g. `[2024-1-1]HelloWorld`
- Use the post title as the prefix for file names, e.g. `HelloWorld_1.png`, `HelloWorld_2.png`, ...
- Download revisions of posts
- Exclude `.psd` and `.zip` files
- Extract cloud drive links from posts and save them to a text file
- ...

Goto [Configuration-Guide](https://ktoolbox.readthedocs.io/latest/configuration/guide/) page for more details.

![KToolBox Configuration Editor](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-2.png)
![KToolBox Configuration Editor](https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-3.png)

### iOS Shortcuts

Goto [Shortcuts for iOS](https://ktoolbox.readthedocs.io/latest/shortcut/) page for more details.

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
