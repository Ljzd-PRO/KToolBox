<p style="text-decoration:none">
  <img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/repository-open-graph-2.svg" alt="logo">
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

<img src="https://cdn.jsdelivr.net/gh/Ljzd-PRO/KToolBox@latest/static/preview-1.png" alt="Preview">

## Features

- Support for **multi-thread** downloads (technically, coroutine)
- **Retry** after download failed
- Ability to download individual post as well as **all post** by a specified creator/artist
- **Update downloaded** creator/artist directories to the latest status
- Customize the **structure** of downloaded post/creator **directories**
- Search for creators/artists and posts, and **export the results**
- **Cross-platform** support & **iOS shortcuts** available

## Tutorial

### Installation

=== "Normal"
    ```bash
    pip3 install ktoolbox
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
  
#### ⬇️🖌️ Download all posts from a creator
```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/9016
```
??? info "Output"
    By default, you will get a `creator-indices.ktoolbox` file in the creator directory, 
    you can use it to update the directory anytime.
  

#### 🔄️ Update a downloaded creator directory
```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --update-with=./xxx/creator-indices.ktoolbox
```
??? info "About `creator-indices.ktoolbox` file"
    The `creator-indices.ktoolbox` file contains the information and filepath of posts inside the directory.
