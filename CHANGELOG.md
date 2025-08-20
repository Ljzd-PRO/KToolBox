## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.21.1/total)

### ✨ Features

- Improved **download progress display**, providing a more **elegant and intuitive** progress bar (v0.21.0)
    ```log
    2025-08-19 13:42:07 | INFO     | ktoolbox.cli - Got creator information - name: Ljzd-PRO, id: 12345678

    2025-08-19 13:42:07 | INFO     | ktoolbox.action.job - Start fetching posts from creator 12345678

    2025-08-19 13:42:07 | INFO     | ktoolbox.action.job - Get 9 posts after filtering, start creating jobs

    🔄 Jobs: 3/9 completed (33.3%), 3 running, 3 waiting

    ⠴ D00l7aSMMRHaF8NG6febzu...    |███████████████░░░░░░░░░░░░░░░| 3.7MB/7.0MB  53.0% ⚡ 997.7KB/s
    ⠋ iUnb6IuVOWfUYglzQS0rBC...    |████████████████████████░░░░░░| 6.1MB/7.6MB  80.2% ⚡ 16MB/s
    ⠋ 10366655_a25KA8mAZuNHZ...    |█████████████░░░░░░░░░░░░░░░░░| 95.0KB/208.0KB  45.7% ⚡ 1.9MB/s

    2025-08-19 13:44:01 | SUCCESS  | ktoolbox.job.runner - All jobs in queue finished
    ```
- Automatically check for updates at program startup and notify the user if a new version is available (v0.21.0)
    ```log
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Update available: 0.21.0 (current: 0.20.0)

    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Release URL: https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.21.0
    ```

### 🪲 Fixes

- Fixed the issue where the feature "**support downloading images embedded in the post HTML content**" added in [v0.17.0](https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.17.0) did not actually exist - #332
  - This is indeed a serious issue. It seems that the relevant branch was not merged into the main branch, resulting in the feature **not being implemented in v0.17.0**.
  - Related configuration:
    - `job.extract_content_images`: Whether to parse and download images embedded in the post HTML content, disabled by default (`False`)
  - This feature is disabled by default because when using the `sync-creator` command to download all posts from a creator, the content of each post must be fetched individually, which can easily trigger DDoS protection and get blocked.
  - You can edit this configuration via `ktoolbox config-editor` (`Job -> extract_content_images`)
  - Or manually edit it in the `.env` file or environment variables:
    ```dotenv
    # Enable parsing and downloading images embedded in the post HTML content
    KTOOLBOX_JOB__EXTRACT_CONTENT_IMAGES=True
    ```
  - 📖 More info: [Configuration Reference - JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
- Fixed the issue where the `download-post` command would **still not generate the text content file** (`content.txt`) 
and external links file (`external_links.txt`) even when the `job.extract_content` and `job.extract_external_links` options were enabled - #332 (v0.21.0)

- - -

### ✨ 新特性

- 改进了**下载进度显示**，提供更加**优美和直观**的进度条显示 (v0.21.0)
    ```log
    2025-08-19 13:42:07 | INFO     | ktoolbox.cli - Got creator information - name: Ljzd-PRO, id: 12345678
    
    2025-08-19 13:42:07 | INFO     | ktoolbox.action.job - Start fetching posts from creator 12345678
    
    2025-08-19 13:42:07 | INFO     | ktoolbox.action.job - Get 9 posts after filtering, start creating jobs
    
    🔄 Jobs: 3/9 completed (33.3%), 3 running, 3 waiting
    
    ⠴ D00l7aSMMRHaF8NG6febzu...    |███████████████░░░░░░░░░░░░░░░| 3.7MB/7.0MB  53.0% ⚡ 997.7KB/s
    ⠋ iUnb6IuVOWfUYglzQS0rBC...    |████████████████████████░░░░░░| 6.1MB/7.6MB  80.2% ⚡ 16MB/s
    ⠋ 10366655_a25KA8mAZuNHZ...    |█████████████░░░░░░░░░░░░░░░░░| 95.0KB/208.0KB  45.7% ⚡ 1.9MB/s
    
    2025-08-19 13:44:01 | SUCCESS  | ktoolbox.job.runner - All jobs in queue finished
    ```
- 程序启动时自动检查更新，并在有新版本时提示用户 (v0.21.0)
    ```log
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Update available: 0.21.0 (current: 0.20.0)
    
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Release URL: https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.21.0
    ```

### 🪲 修复

- 修复了 [v0.17.0](https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.17.0) 新增的“**支持下载帖子 HTML 内容中嵌入的图片**”实际上并不存在的问题 - #332
  - 这确实是个严重的问题，似乎相关分支没有被合并到主分支，导致该功能**在 v0.17.0 版本中并未实现**
  - 相关配置项：
    - `job.extract_content_images`：是否解析并下载帖子 HTML 内容中嵌入的图片，默认关闭（`False`）
  - 该功能默认关闭，因为当使用 `sync-creator` 命令下载作者全部帖子时，只能逐个获取帖子内容（content），这容易导致触发 DDoS 防御机制而被阻断
  - 可通过运行 `ktoolbox config-editor` 编辑这些配置（`Job -> extract_content_images`）
  - 或手动在 `.env` 文件或环境变量中编辑：
    ```dotenv
    # 开启解析并下载帖子 HTML 内容中嵌入的图片
    KTOOLBOX_JOB__EXTRACT_CONTENT_IMAGES=True
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.JobConfiguration)
- 修复即使启用了 `job.extract_content` 和 `job.extract_external_links` 配置项，`download-post` 命令
仍然**不会生成文本内容文件**（`content.txt`）和外部链接文件（`external_links.txt`）的问题 - #332 (v0.21.0)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.21.0...v0.21.1