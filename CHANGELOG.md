## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.16.0/total)

### 💡 Feature

- Add auto-managed cookies to bypass **DDoS Guard** - #269 (@CanglanXYA)
- Add comprehensive **revision post** support with enhanced API and configuration - #240, #241
  - For posts like: `https://kemono.cr/{service}/user/{user_id}/post/{post_id}/revision/{revision_id}`
  - This feature is disabled by default
  - Run `ktoolbox config-editor` to edit this configurations (`Job -> include_revisions`)
  - Or manually edit it in `.env` file or environment variables
    ```dotenv
    # Set this to `True` to enable revisions download
    KTOOLBOX_JOB__INCLUDE_REVISIONS=True
    ```

[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- 新增自动管理 Cookie 功能以绕过 **DDoS Guard** - #269 (@CanglanXYA)
- 新增全面的**修订作品**支持，增强 API 和配置功能 - #240, #241
  - 适用于如下作品：`https://kemono.cr/{service}/user/{user_id}/post/{post_id}/revision/{revision_id}`
  - 此功能默认关闭
  - 运行 `ktoolbox config-editor` 可编辑此配置项（`Job -> include_revisions`）
  - 或在 `.env` 文件或环境变量中手动编辑
    ```dotenv
    # 设置为 `True` 以启用修订下载
    KTOOLBOX_JOB__INCLUDE_REVISIONS=True
    ```
    
[//]: # (### 🪲 修复)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.15.1...v0.16.0