## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.21.0/total)

### ✨ Features

- Improved **download progress display**, providing a more **elegant and intuitive** progress bar
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
- Automatically check for updates at program startup and notify the user if a new version is available
    ```log
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Update available: 0.21.0 (current: 0.20.0)

    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Release URL: https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.21.0
    ```

### 🪲 Fixes

- Fixed the issue where the `download-post` command would **still not generate the text content file** (`content.txt`) 
and external links file (`external_links.txt`) even when the `job.extract_content` and `job.extract_external_links` options were enabled - #332

- - -

### ✨ 新特性

- 改进了**下载进度显示**，提供更加**优美和直观**的进度条显示
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
- 程序启动时自动检查更新，并在有新版本时提示用户
    ```log
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Update available: 0.21.0 (current: 0.20.0)
    
    2025-08-19 13:41:23 | INFO     | ktoolbox.utils - Release URL: https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.21.0
    ```

### 🪲 修复

- 修复即使启用了 `job.extract_content` 和 `job.extract_external_links` 配置项，`download-post` 命令
仍然**不会生成文本内容文件**（`content.txt`）和外部链接文件（`external_links.txt`）的问题 - #332

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.20.0...v0.21.0