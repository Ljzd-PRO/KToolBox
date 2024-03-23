## Changes

### 🐍 Fix

- Fixed download failure when server returns an invalid filename (`Attachment.name`) (#73)

### 💡 Feature

- Add support for local storage bucket mode (#74) (@Nacosia)
  - Edit `KTOOLBOX_DOWNLOADER__USE_BUCKET`, `KTOOLBOX_DOWNLOADER_BUCKET_PATH` in `prod.env` or environment variables to set this option
  - 📖More information: [Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

- Add support for customizing the post directory name format (#45, #46)
  - Edit `KTOOLBOX_JOB__POST_DIRNAME_FORMAT` in `prod.env` or environment variables to set this option
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
   ```dotenv
   # It will create directories like `[2024-1-1]HelloWorld`
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{published}{title}"
   ```
   ```dotenv
   # It will create directories like `[2024-1-1]_12345_112233`
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{published}_{user}_{id}"
   ```
   ```dotenv
   # Default value. It will create directories like `HelloWorld`
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{title}"
   ```

- Marked `JobConfiguration.post_id_as_path` as deprecated, use `JobConfiguration.post_dirname_format` instead

- - -

### 🐍 修复

- 修复当服务器返回的文件名不合法时下载出错的问题 (`Attachment.name`) (#73)

### 💡 新特性

- 增加本地存储桶模式的存储支持 (#74) (@Nacosia)
  - 在 `prod.env` 或环境变量中编辑 `KTOOLBOX_DOWNLOADER__USE_BUCKET`, `KTOOLBOX_DOWNLOADER_BUCKET_PATH` 以设置该选项
  - 📖更多信息: [Configuration-Reference-DownloaderConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.DownloaderConfiguration)

- 增加支持自定义作品目录名格式 (#45, #46)
  - 在 `prod.env` 或环境变量中编辑 `KTOOLBOX_JOB__POST_DIRNAME_FORMAT` 以设置该选项
  - 📖更多信息: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
   ```dotenv
   # 将会创建例如 `[2024-1-1]HelloWorld` 的目录名
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{published}{title}"
   ```
   ```dotenv
   # 将会创建例如 `[2024-1-1]_12345_112233` 的目录名
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{published}_{user}_{id}"
   ```
   ```dotenv
   # 默认值。 将会创建例如 `HelloWorld` 的目录名
   KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{title}"
   ```

- 将 `JobConfiguration.post_id_as_path` 标记为已弃用, 请用 `JobConfiguration.post_dirname_format` 取代

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.4.0...v0.5.0