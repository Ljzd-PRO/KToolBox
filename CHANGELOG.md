## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.17.0/total)

### 💡 Feature

- Support download **images embedded in post HTML content** - #218
- Add external links extraction feature for **cloud storage URLs** - #232 (@xxkzn)
  - New configurations:
    - `job.extract_external_links`: Whether to extract external file sharing links from post content and save to separate file
    - `job.external_link_patterns`: Regex patterns for extracting external links
  - These configuration are **optional**, with the feature enabled by default. The regular expression includes the following services:
    - Google Drive
    - MEGA
    - Dropbox
    - OneDrive
    - MediaFire
    - And other common file hosting services
  - Run `ktoolbox config-editor` to edit these configurations (`Job -> extract_external_links`, `Job -> external_link_patterns`)
  - Or manually edit them `.env` file or environment variables
    ```dotenv
    # This feature is enabled by default
    KTOOLBOX_JOB__EXTRACT_EXTERNAL_LINKS=True
    # Setting up lists and regular expressions in dotenv is relatively complex and cumbersome. It is recommended to use the aforementioned graphical configuration editor for these settings.
    KTOOLBOX_JOB__EXTERNAL_LINK_PATTERNS='["https?://drive\\.google\\.com/[^\\s]+", "https?://docs\\.google\\.com/[^\\s]+", "https?://mega\\.nz/[^\\s]+", "https?://mega\\.co\\.nz/[^\\s]+", "https?://(?:www\\.)?dropbox\\.com/[^\\s]+", "https?://db\\.tt/[^\\s]+", "https?://onedrive\\.live\\.com/[^\\s]+", "https?://1drv\\.ms/[^\\s]+", "https?://(?:www\\.)?mediafire\\.com/[^\\s]+", "https?://(?:www\\.)?wetransfer\\.com/[^\\s]+", "https?://we\\.tl/[^\\s]+", "https?://(?:www\\.)?sendspace\\.com/[^\\s]+", "https?://(?:www\\.)?4shared\\.com/[^\\s]+", "https?://(?:www\\.)?zippyshare\\.com/[^\\s]+", "https?://(?:www\\.)?uploadfiles\\.io/[^\\s]+", "https?://(?:www\\.)?box\\.com/[^\\s]+", "https?://(?:www\\.)?pcloud\\.com/[^\\s]+", "https?://disk\\.yandex\\.[a-z]+/[^\\s]+", "https?://[^\\s]*(?:file|upload|share|download|drive|storage)[^\\s]*\\.[a-z]{2,4}/[^\\s]+"]'
    ```
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)

### 🪲 Fix

- Removed the deprecated configuration `job.post_structure.content_filepath`, use `job.post_structure.content` instead

- - -

### 💡 新特性

- 支持下载**帖子 HTML 内容中嵌入的图片** - #218
- 新增**云存储 URL 外链提取**功能 - #232 (@xxkzn)
  - 新增配置项：
    - `job.extract_external_links`：是否从帖子内容中提取外部文件分享链接并保存到单独文件
    - `job.external_link_patterns`：用于提取外链的正则表达式模式
  - 这些配置项为**可选**，该功能默认启用。正则表达式已包含以下服务：
    - Google Drive
    - MEGA
    - Dropbox
    - OneDrive
    - MediaFire
    - 及其他常见文件托管服务
  - 可运行 `ktoolbox config-editor` 编辑这些配置（`Job -> extract_external_links`，`Job -> external_link_patterns`）
  - 或手动编辑 `.env` 文件或环境变量
    ```dotenv
    # 此功能默认启用
    KTOOLBOX_JOB__EXTRACT_EXTERNAL_LINKS=True
    # 在 dotenv 中设置列表和正则表达式较为复杂，推荐使用上述图形化配置编辑器进行设置。
    KTOOLBOX_JOB__EXTERNAL_LINK_PATTERNS='["https?://drive\\.google\\.com/[^\\s]+", "https?://docs\\.google\\.com/[^\\s]+", "https?://mega\\.nz/[^\\s]+", "https?://mega\\.co\\.nz/[^\\s]+", "https?://(?:www\\.)?dropbox\\.com/[^\\s]+", "https?://db\\.tt/[^\\s]+", "https?://onedrive\\.live\\.com/[^\\s]+", "https?://1drv\\.ms/[^\\s]+", "https?://(?:www\\.)?mediafire\\.com/[^\\s]+", "https?://(?:www\\.)?wetransfer\\.com/[^\\s]+", "https?://we\\.tl/[^\\s]+", "https?://(?:www\\.)?sendspace\\.com/[^\\s]+", "https?://(?:www\\.)?4shared\\.com/[^\\s]+", "https?://(?:www\\.)?zippyshare\\.com/[^\\s]+", "https?://(?:www\\.)?uploadfiles\\.io/[^\\s]+", "https?://(?:www\\.)?box\\.com/[^\\s]+", "https?://(?:www\\.)?pcloud\\.com/[^\\s]+", "https?://disk\\.yandex\\.[a-z]+/[^\\s]+", "https?://[^\\s]*(?:file|upload|share|download|drive|storage)[^\\s]*\\.[a-z]{2,4}/[^\\s]+"]'
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
    
### 🪲 修复

- 移除了过时的配置 `job.post_structure.content_filepath`，请用 `job.post_structure.content` 代替

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.16.0...v0.17.0