## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.23.0/total)

### ✨ Features

- Added configuration options to support **filtering** downloads by **file size** - #343
  - You can set the minimum and maximum file size (in bytes) via `job.min_file_size` and `job.max_file_size`
  - Both options can be set together to define a file size range
  - Configure these options using the graphical config editor, or set them in the dotenv file `.env` or via system environment variables:
    ```dotenv
    # Skip files smaller than 1 MB (to avoid downloading thumbnails)
    KTOOLBOX_JOB__MIN_FILE_SIZE=1048576

    # Skip files larger than 50 MB (to save disk space)
    KTOOLBOX_JOB__MAX_FILE_SIZE=52428800
    ```
  - 📖 More info: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
- Improved progress bar output - #345
  - Fixed the issue of the download file progress bar **constantly reordering**
  - Added **visual overall progress bar**
  - Added display of **total download speed**
  - Enhanced the **color rendering** of the progress bar
    ```
    🔄   [==>---------------------------] 9% | Jobs: 173/1870 | 3 running | 1694 waiting | 5.7MB/s
    
    ⠹ 0bh1EKTGt5Zg9nNaDAi25P...    |███████████████████████████░░░| 3.7MB/4.0MB  92.5% ⚡ 1.9MB/s  
    ⠹ YV30J8ftUbE9dUkkJVCqvN...    |███░░░░░░░░░░░░░░░░░░░░░░░░░░░| 527.0KB/4.1MB  12.5% ⚡ 1.9MB/s  
    ⠹ KvKMSpwB4rRknTPKhEiXle...    |░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░| 95.0KB/3.8MB   2.5% ⚡ 1.9MB/s  
    ```

### 🪲 Fixes

- **Increased** the default **tps limit** (maximum number of connections established per second)
  - This setting is optional. To **improve download efficiency** in general cases, the default value has been increased from `1.0` to `5.0`
  - If you frequently encounter **403** errors during downloads, try setting this value lower, such as `1.0`
  - Run `ktoolbox config-editor` to edit this setting (`Downloader -> tps_limit`)
  - Or manually edit the `KTOOLBOX_DOWNLOADER__TPS_LIMIT` in the `.env` file or set it via environment variables
    ```dotenv
    KTOOLBOX_DOWNLOADER__TPS_LIMIT=1.0
    ```
  - 📖 More info: [Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

- - -

### ✨ 新特性

- 增加配置项以支持**按文件大小过滤**下载 - #343
  - 通过配置 `job.min_file_size` 和 `job.max_file_size` 来设置最小和最大文件大小（单位：字节）
  - 你可以同时设置这两个选项来定义一个文件大小范围
  - 通过图形化配置编辑器或在 dotenv 文件 `.env` 或系统环境变量中设置这些配置：
    ```dotenv
    # 跳过小于 1 MB 的文件 （避免下载到缩略图）
    KTOOLBOX_JOB__MIN_FILE_SIZE=1048576
    
    # 跳过大于 50 MB 的文件 （节省磁盘空间）
    KTOOLBOX_JOB__MAX_FILE_SIZE=52428800
    ```
  - 📖 更多信息：[Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.JobConfiguration)
- 改进进度条输出 - #345
  - 修复了下载文件进度条**不断重新排序**的问题
  - 增加了**可视化的总进度条**
  - 增加了下载**总速度**显示
  - 增加了进度条的**颜色渲染**
  ```
  🔄   [==>---------------------------] 9% | Jobs: 173/1870 | 3 running | 1694 waiting | 5.7MB/s

  ⠹ 0bh1EKTGt5Zg9nNaDAi25P...    |███████████████████████████░░░| 3.7MB/4.0MB  92.5% ⚡ 1.9MB/s
  ⠹ YV30J8ftUbE9dUkkJVCqvN...    |███░░░░░░░░░░░░░░░░░░░░░░░░░░░| 527.0KB/4.1MB  12.5% ⚡ 1.9MB/s
  ⠹ KvKMSpwB4rRknTPKhEiXle...    |░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░| 95.0KB/3.8MB   2.5% ⚡ 1.9MB/s
  ```

### 🪲 修复

- **提高**了默认的 **tps limit** （每秒最多建立的连接数）
  - 这项配置是可选的，为了**提高一般情况下的下载效率**，现在的默认值从 `1.0` 提升到了 `5.0`
  - 当下载频繁出现 **403** 错误时，可尝试将此设置改为较低值，如 `1.0`
  - 执行 `ktoolbox config-editor` 来编辑这项配置 (`Downloader -> tps_limit`)
  - 或手动编辑 `.env` 文件中的 `KTOOLBOX_DOWNLOADER__TPS_LIMIT` 或环境变量来设置这项配置
    ```dotenv
    KTOOLBOX_DOWNLOADER__TPS_LIMIT=1.0
    ```
  - 📖更多信息：[Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.DownloaderConfiguration)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.22.0...v0.23.0