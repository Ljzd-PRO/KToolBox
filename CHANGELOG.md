## Changes

### 💡 Feature

- Show the download job status each 30s (waiting, running, completed%)
- Shortened the log length
  - E.g. `2024-10-05 20:12:37 | WARNING  | ktoolbox.job.runner - Download file already exists, skipping ...`

### 🪲 Fix

- Fix error when attempting to download files which posses too long names (invalid names) (#150)
  - For example the wrong filename like this: `https://www.patreon.com/media-u/Z0FBQUFBQm........=#12345678_` \
    KToolBox can get the correct filename: `6edd5bdae......0e7f913.png`

- - -

### 💡 新特性

- 每隔 30 秒显示下载任务状态（等待中、运行中、已完成%）
- 缩短了日志长度
  - 例如 `2024-10-05 20:12:37 | WARNING  | ktoolbox.job.runner - Download file already exists, skipping ...`

### 🪲 修复

- 修复下载过长文件名（非法文件名）的文件时报错的问题 (#150)
  - 例如这样的错误文件名：`https://www.patreon.com/media-u/Z0FBQUFBQm........=#12345678_` \
    KToolBox 可以获取到正确的文件名：`6edd5bdae......0e7f913.png`

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.8.0...v0.9.0