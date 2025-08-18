## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.20.0/total)

### ✨ Features

- Added options to control whether to extract `content` and `external_links` for greater flexibility - #317
  - Related configuration items:
    - `job.extract_content`: Whether to extract post text content as a separate file, default is disabled (`False`)
    - `job.extract_external_links`: Whether to extract external links in post text content as a separate file, default is disabled (`False`)
  - You can edit these settings via `ktoolbox config-editor` (`Job -> ...`)
  - Or manually edit them in the `.env` file or environment variables
    ```dotenv
    # Whether to extract post text content as a separate file
    KTOOLBOX_JOB__EXTRACT_CONTENT=True
    # Whether to extract external links in post text content as a separate file
    KTOOLBOX_JOB__EXTRACT_EXTERNAL_LINKS=True

    # Change the default file names for content.txt and external_links.txt
    KTOOLBOX_JOB__POST_STRUCTURE__CONTENT="content.html"
    KTOOLBOX_JOB__POST_STRUCTURE__EXTERNAL_LINKS="link.txt"
    ```
  - 📖 More info: [Configuration Reference - JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
- Support controlling whether to preserve the metadata (such as modification date) of downloaded files - #321
  - If you usually browse images by download date, or want to use post images as Windows folder preview covers, you can disable this option
  - Related configuration item:
    - `downloader.keep_metadata`: Whether to preserve the metadata (such as modification date) of downloaded files, enabled by default (`True`)
  - You can edit this setting via `ktoolbox config-editor` (`Downloader -> keep_metadata`)
  - Or manually edit it in the `.env` file or environment variables
    ```dotenv
    # Whether to preserve the metadata (such as modification date) of downloaded files
    KTOOLBOX_DOWNLOADER__KEEP_METADATA=False
    ```
  - 📖 More info: [Configuration Reference - DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

### 🪲 Fixes

- Due to changes in the Kemono API, extraction of **post text content and external links** (content and external_links) can now only be performed one by one.
Therefore, **only when** the default-disabled `job.extract_content` and `job.extract_external_links` are set to `True` (as mentioned above),
and the post **actually contains text content**, **will** post text content and external links be extracted, to avoid frequent API calls that may trigger **server DDoS protection**.
- Output `SUCCESS` level logs to help users better understand download status

- - -

### ✨ 新特性

- 支持控制是否提取 content 和 external_links，灵活性提升 - #317
  - 相关配置项：
    - `job.extract_content`：是否提取帖子文本内容为独立的文件，默认关闭（`False`）
    - `job.extract_external_links`：是否提取帖子文本内容中的外部链接为独立的文件，默认关闭（`False`）
  - 可通过运行 `ktoolbox config-editor` 编辑这些配置（`Job -> ...`）
  - 或手动在 `.env` 文件或环境变量中编辑
    ```dotenv
    # 是否提取帖子文本内容为独立的文件
    KTOOLBOX_JOB__EXTRACT_CONTENT=True
    # 是否提取帖子文本内容中的外部链接为独立的文件
    KTOOLBOX_JOB__EXTRACT_EXTERNAL_LINKS=True
  
    # 修改默认的 content.txt 和 external_links.txt 文件名
    KTOOLBOX_JOB__POST_STRUCTURE__CONTENT="content.html"
    KTOOLBOX_JOB__POST_STRUCTURE__EXTERNAL_LINKS="link.txt"
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.JobConfiguration)
- 支持控制是否保留下载的文件的元数据（修改日期等） - #321
  - 如果你平时是按照下载日期排序浏览图片的，或者需要将帖子图片作为 Windows 文件夹预览封面，可以关闭此配置
  - 相关配置项：
    - `downloader.keep_metadata`：是否保留下载的文件的元数据（修改日期等），默认开启（`True`）
    - 可通过运行 `ktoolbox config-editor` 编辑这些配置（`Downloader -> keep_metadata`）
    - 或手动在 `.env` 文件或环境变量中编辑
    ```dotenv
    # 是否保留下载的文件的元数据（修改日期等）
    KTOOLBOX_DOWNLOADER__KEEP_METADATA=False
    ```
  - 📖更多信息：[配置参考-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/zh/configuration/reference/#ktoolbox._configuration_zh.DownloaderConfiguration)

### 🪲 修复

- 由于 Kemono API 变更，帖子的**文本内容和外部链接**（content 和 external_links）的提取只能单独地一个个获取，
因此仅当将**默认关闭**的 `job.extract_content` 和 `job.extract_external_links` 设置为 `True` 时（上文新特性提到），
以及帖子**真正存在文本内容**时，**才会提取帖子文本内容和外部链接**，避免 API 频繁调用导致**被服务器 DDoS 防御机制阻拦**
- 输出 `SUCCESS` 级别日志，以便用户更清晰地了解下载状态

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.19.2...v0.20.0