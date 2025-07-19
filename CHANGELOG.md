## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.15.0/total)

### 💡 Feature

- Add support for setting **tps limit** (maximum connections established per second)
  - This configuration is **optional**, default to `1`, If you frequently encounter **403** errors during downloads, \
    try setting this to a lower value, or set it to a higher value for better efficiency
  - Run `ktoolbox config-editor` to edit the configuration (`Downloader -> tps_limit`)
  - Or manually edit `KTOOLBOX_DOWNLOADER__TPS_LIMIT` in `.env` file or environment variables to set this option
    ```dotenv
    KTOOLBOX_DOWNLOADER__TPS_LIMIT=1
    ```
  - 📖More information: [Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

### 🪲 Fix

- **Improved the retry mechanism** for downloading by traversing server subdomains when a **403 error** occurs, \
  using index fallback to prevent the subdomain index from increasing indefinitely and causing downloads to **never complete**.

- - -

### 💡 新特性

- 增加支持设置下载所用的 **tps limit** （每秒最多建立的连接数）
  - 这项配置是**可选的**，默认为 `1`，当下载频繁出现 **403** 错误时可尝试将此设置改为较低值，如果想提高效率可设为较高值
  - 执行 `ktoolbox config-editor` 来编辑这项配置 (`Downloader -> tps_limit`)
  - 或手动编辑 `.env` 文件中的 `KTOOLBOX_DOWNLOADER__TPS_LIMIT` 或环境变量来设置这项配置
    ```dotenv
    KTOOLBOX_DOWNLOADER__TPS_LIMIT=1
    ```
  - 📖更多信息：[Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

### 🪲 修复

- 采用索引回退的方式**改进 403 错误时的重试下载的服务器子域名遍历机制**，防止子域名编号无限增大导致**永远无法完成下载**的问题

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.14.0...v0.15.0