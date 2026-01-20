<p style="text-decoration:none">
  <img src="https://socialify.git.ci/Ljzd-PRO/KToolBox/image?description=1&font=Source+Code+Pro&forks=1&issues=1&language=1&name=1&owner=1&pattern=Diagonal+Stripes&pulls=1&stargazers=1&theme=Auto" alt="KToolBox"/>
</p>

<h1 style="text-align: center">
  KToolBox
</h1>

<p style="text-align: center">
  KToolBox is a useful CLI tool for downloading posts content in
  <a href="https://kemono.su/">Kemono.party / Kemono.su</a>
</p>

<p style="text-align: center">
  <a href="https://pypi.org/project/ktoolbox" target="_blank">
    <img src="https://img.shields.io/github/v/release/Ljzd-PRO/KToolBox?logo=python" alt="Version">
  </a>

  <a href="https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE">
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
- Support filtering downloads by **file size**
  - For example, if you want to avoid downloading large video files when running out of disk space, you can set a maximum file size limit in the config
  - You can also set a minimum file size to skip downloading thumbnail or preview images
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

## Tutorial

### Installation

You can use executables from [releases](https://github.com/Ljzd-PRO/KToolBox/releases) page

=== "Normal"
    Recommend to use pipx
    ```bash
    pip3 install pipx
    # Windows
    pipx install ktoolbox[urwid,winloop]
    # Linux / macOS
    pipx install ktoolbox[urwid,uvloop]
    ```

=== "Pure Python"
    If you are using pyodide, or you can only use pure Python and you cannot compile [pydantic](https://docs.pydantic.dev/latest/) v2.x.x
    ```bash
    pip3 install pipx
    pipx install ktoolbox-pure-py
    ```

=== "For iOS a-Shell"
    ```bash
    pip3 install ktoolbox-pure-py
    ```
    !!! info "About a-Shell"
        [a-Shell](https://github.com/holzschu/a-shell) is an iOS terminal App, 
        it can only run pure python scripts.

### Command

For more information, use the help command or goto [Commands](commands/guide.md) page.
  
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
??? info "If some files failed to download"
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
