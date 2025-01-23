## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.13.0/total)

### 💡 Feature

- Add support for customizing the `Post.file` filename format (not `Post.attachments`)
  - Run `ktoolbox config-editor` to edit the configuration (`Job -> post_structure -> file`)
  - Or manually edit `KTOOLBOX_JOB__POST_STRUCTURE__FILE` in `.env` file or environment variables to set this option
    ```dotenv
    # Example
    # Result filename: [2023-01-01]_TheTitle_12345_UxTleZ3zP6LHA7BPNxlEWDzX.jpg
    KTOOLBOX_JOB__POST_STRUCTURE__FILE=[{published}]_{title}_{id}_{}
    ```
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)

- Add support for customizing reverse proxy for download URLs - (#216)
  - Run `ktoolbox config-editor` to edit the configuration (`Downloader -> reverse_proxy`)
  - Or manually edit `KTOOLBOX_DOWNLOADER__REVERSE_PROXY` in `.env` file or environment variables to set this option
    ```dotenv
    # Example
    # Result download URL: https://example.com/https://n1.kemono.su/data/66/83/xxxx.jpg
    KTOOLBOX_DOWNLOADER__REVERSE_PROXY="https://example.com/{}"
    ```
  - 📖More information: [Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

- Rename `PostStructure.content_filepath` to `PostStructure.content`, the old configuration is still available, but it will be removed in the future. If you use this option, you will receive a warning message.
  - 📖More information: [Configuration-Reference-PostStructureConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.PostStructureConfiguration)

[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- 增加支持自定义 `Post.file` 的文件名格式（并非 `Post.attachments`）
  - 执行 `ktoolbox config-editor` 来编辑这项配置 (`Job -> post_structure -> file`)
  - 或手动编辑 `.env` 文件中的 `KTOOLBOX_JOB__POST_STRUCTURE__FILE` 或环境变量来设置这项配置
    ```dotenv
    # 示例
    # 文件名：[2023-01-01]_TheTitle_12345_UxTleZ3zP6LHA7BPNxlEWDzX.jpg
    KTOOLBOX_JOB__POST_STRUCTURE__FILE=[{published}]_{title}_{id}_{}
    ```
  - 📖更多信息：[Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)

- 增加支持自定义下载 URL 的反向代理 - (#216)
  - 执行 `ktoolbox config-editor` 来编辑这项配置 (`Downloader -> reverse_proxy`)
  - 或手动编辑 `.env` 文件中的 `KTOOLBOX_DOWNLOADER__REVERSE_PROXY` 或环境变量来设置这项配置
    ```dotenv
    # 示例
    # 下载 URL：https://example.com/https://n1.kemono.su/data/66/83/xxxx.jpg
    KTOOLBOX_DOWNLOADER__REVERSE_PROXY="https://example.com/{}"
    ```
  - 📖更多信息：[Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

- `PostStructure.content_filepath` 更名为 `PostStructure.content`，原先的配置仍可继续使用，但未来将会被移除。如果您使用了这项配置，将会收到警告信息。
  - 📖更多信息：[Configuration-Reference-PostStructureConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.PostStructureConfiguration)

[//]: # (### 🪲 修复)

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.12.0...v0.13.0