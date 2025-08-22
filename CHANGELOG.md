## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.22.0/total)

### ✨ Features

- Added `job.download_file` and `job.download_attachments` configuration options to control **whether to download files and attachments in posts**
  - Related configuration options:
    - `job.download_file` (default: `True`): Whether to download the file corresponding to the `file` field of the post (usually the cover image)
    - `job.download_attachments` (default: `True`): Whether to download files corresponding to the `attachments` field of the post (usually original images, compressed packages, etc.)
  - These options are enabled by default to maintain the same behavior as previous versions
  - You can edit these options via `ktoolbox config-editor` (`Job -> ...`)
  - Or manually edit them in the `.env` file or environment variables:
    ```dotenv
    # Whether to download the file corresponding to the `file` field of the post (usually the cover image)
    # Download enabled by default
    KTOOLBOX_JOB__DOWNLOAD_FILE=False

    # Whether to download files corresponding to the `attachments` field of the post (usually original images, compressed packages, etc.)
    # Download enabled by default
    KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
    ```
  - 📖 More information: [Configuration Reference - JobConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.JobConfiguration)

[//]: # (### 🪲 Fixes)

- - -

### ✨ 新特性

- 新增 `job.download_file` 和 `job.download_attachments` 配置项，控制**是否下载帖子中的文件和附件**
  - 相关配置项：
    - `job.download_file`（默认值：`True`）：是否下载帖子的 `file` 字段对应的文件（通常是帖子封面图）
    - `job.download_attachments`（默认值：`True`）：是否下载帖子的 `attachments` 字段对应的文件（通常是帖子中的正式原图、压缩包等附件）
  - 该配置项默认均为开启状态，保持与之前版本一致的行为
  - 可通过运行 `ktoolbox config-editor` 编辑这些配置（`Job -> ...`）
  - 或手动在 `.env` 文件或环境变量中编辑：
    ```dotenv
    # 是否下载帖子的 `file` 字段对应的文件（通常是帖子封面图）
    # 默认开启下载
    KTOOLBOX_JOB__DOWNLOAD_FILE=False
    
    # 是否下载帖子的 `attachments` 字段对应的文件（通常是帖子中的正式原图、压缩包等附件）
    # 默认开启下载
    KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.JobConfiguration)

[//]: # (### 🪲 修复)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.21.1...v0.22.0