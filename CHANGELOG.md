## Changes

### 💡 Feature

- Add support for customizing filename:
  - Edit `KTOOLBOX_JOB__FILENAME_FORMAT` in `prod.env` or environment variables to set this option (#116)
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
      KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

      # `{}`: Basic filename
      # Can be used with the configuration option above.
      # Rename attachments to `[2024-1-1]_1.png`, `[2024-1-1]_2.png`, ...
      KTOOLBOX_JOB__FILENAME_FORMAT="[{published}]_{}"
      ```
- Change default post text content filename `index.html` to `content.txt`

[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- 支持自定义下载的文件名格式：
  - 在 `prod.env` 或环境变量中编辑 `KTOOLBOX_JOB__FILENAME_FORMAT` 以设置该选项 (#116)
  - 📖更多信息: [配置-参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
      ```dotenv
      # 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
      KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

      # `{}`：基本文件名
      # 可以和上面的配置选项搭配使用
      # 附件将被重命名为 `[2024-1-1]_1.png`, `[2024-1-1]_2.png`, ...
      KTOOLBOX_JOB__FILENAME_FORMAT="[{published}]_{}"
      ```
- 更改默认的作品文本内容文件名 `index.html` 为 `content.txt`

[//]: # (### 🪲 修复)

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.6.0...v0.7.0