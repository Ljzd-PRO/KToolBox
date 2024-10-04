## Changes

### 💡 Feature

- Stop using binary prefix (IEEE 1541-2002) in download speed unit (use `KB`, `MB`, ... instead of `KiB`, `MiB`, ...)
- Stop downloading when failing to retrieve the creator's name, instead of using the creator ID as the directory name to continue downloading
- In addition to the `prod.env` file, KToolBox also reads configurations from the **`.env`** file
- When KToolBox starts, it will output the configuration details for user inspection

### 🪲 Fix

- Fix the issue where the log output interrupts the download progress bar
- Fix the `job.filename_format` configuration, where `{}` is simply replaced with the filename and extension without considering its position
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
      KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

      # `{}`: Basic filename
      # Rename attachments to `1_[2024-1-1].png`, `2_[2024-1-1].png`, ...
      KTOOLBOX_JOB__FILENAME_FORMAT="{}_[{published}]"
      ```

- - -

### 💡 新特性

- 停止在下载速度单位中使用二进制前缀（IEEE 1541-2002）（使用 `KB`, `MB`, ... 而不是 `KiB`, `MiB`, ...）
- 获取作者名称失败时停止下载，而不是采用作者ID作为目录名继续下载
- 除了 `prod.env` 文件以外，KToolBox 也会从 **`.env`** 文件读取配置
- KToolBox 启动时将会输出配置详情，以便用户检查

### 🪲 修复

- 修复下载进度条被输出的日志打断的问题
- 修复 job.filename_format 文件名格式配置中的 {} 被简单地替换成文件名和后缀，而没有考虑其所在位置的问题
  - 📖更多信息: [配置-参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
      KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

      # `{}`：基本文件名
      # 附件将被重命名为 `1_[2024-1-1].png`, `2_[2024-1-1].png`, ...
      KTOOLBOX_JOB__FILENAME_FORMAT="{}_[{published}]"
      ```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.7.0...v0.8.0