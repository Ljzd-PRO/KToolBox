## Changes

### 💡 Feature

- Add support for filename allow-list/block-list to filter downloaded files.
  - Use Unix shell-style wildcards
  - Edit `KTOOLBOX_JOB__ALLOW_LIST`, `KTOOLBOX_JOB__BLOCK_LIST` in `prod.env` or environment variables to set this option
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # Only download files that match these pattern
      KTOOLBOX_JOB__ALLOW_LIST=["*.jpg","*.jpeg","*.png"]

      # Not to download files that match these pattern
      KTOOLBOX_JOB__BLOCK_LIST=["*.psd"]
      ```
- Default not to save `creator-indices.ktoolbox` (because it's useless now :(

### 🪲 Fix

- Fix missing `Post.file.name` may cause download file (`Post.file`) named to `None`

- - -

### 💡 新特性

- 增加文件名白名单/黑名单支持以进行下载文件的过滤
  - 使用 Unix 风格通配符
  - 在 `prod.env` 或环境变量中编辑 `KTOOLBOX_JOB__POST_DIRNAME_FORMAT` 以设置该选项
  - 📖更多信息: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # 只下载匹配这些模式的文件
      KTOOLBOX_JOB__ALLOW_LIST=["*.jpg","*.jpeg","*.png"]

      # 不下载匹配这些模式的文件
      KTOOLBOX_JOB__BLOCK_LIST=["*.psd"]
      ```
- 默认不保存 `creator-indices.ktoolbox` （因为它现在已经没什么用了 :(

### 🪲 修复

- 修复缺失 `Post.file.name` 可能导致下载文件（`Post.file`）被命名为 `None`

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.5.2...v0.6.0