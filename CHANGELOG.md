## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.14.0/total)

### 💡 Feature

- Add support for setting **session key** (can be found in cookies after a successful login) for download - (#247)
  - This configuration is **optional**. If you frequently encounter **403** errors during downloads, you can try setting this option
  - Run `ktoolbox config-editor` to edit the configuration (`API -> session_key`)
  - Or manually edit `KTOOLBOX_API__SESSION_KEY` in `.env` file or environment variables to set this option
    ```dotenv
    KTOOLBOX_API__SESSION_KEY="xxxxxxx"
    ```
  - 📖More information: [Configuration-Reference-APIConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.APIConfiguration)

### 🪲 Fix

- Fixed the issue of frequent **403 errors** during downloads (resolved by trying alternative download servers) - (#247)
  - You will see `Download failed, trying alternative subdomains` in the log, indicating the program is attempting other download servers
- Improved connection pool management for asynchronous requests

- - -

### 💡 新特性

- 增加支持设置下载所用的 **session key** （登录成功后可在 Cookies 中查看） - (#247)
  - 这项配置是**可选的**，当下载频繁出现 **403** 错误时可尝试设置该配置
  - 执行 `ktoolbox config-editor` 来编辑这项配置 (`API -> session_key`)
  - 或手动编辑 `.env` 文件中的 `KTOOLBOX_API__SESSION_KEY` 或环境变量来设置这项配置
    ```dotenv
    KTOOLBOX_API__SESSION_KEY="xxxxxxx"
    ```
  - 📖更多信息：[Configuration-Reference-APIConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.APIConfiguration)
### 🪲 修复

- 修复下载时**频繁出现 403 错误**的问题（通过尝试其他下载服务器解决） - (#247)
  - 你将会在日志中看到 `Download failed, trying alternative subdomains`，这表明程序正在尝试其他下载服务器
- 改进异步请求的连接池管理

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.13.0...v0.14.0