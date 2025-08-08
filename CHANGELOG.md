## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.19.0/total)

### 💡 Feature

- Add **`--keywords-exclude`** parameter for post filtering - #309
  ```shell
  # Method 1: Include only specific character posts
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords="release"

  # Method 2: Exclude unwanted character posts (OR logic)
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords_exclude="announcement,vote,share"
  
  # Method 3: Combined filtering (most flexible)
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords="ブルアカ" --keywords_exclude="全体公開,結果発表"
  ```
- Add **year/month** **grouping** functionality for post organization - #306
  - You can group downloaded posts by year and month with customizable directory naming formats
  - New configuration options:
    - `job.group_by_year`: Enable grouping by year (Disabled by default)
    - `job.group_by_month`: Enable grouping by month (Disabled by default)
    - `job.year_month_format`: Customize the directory naming format for year grouping (Defaults to `{year}`)
    - `job.month_format`: Customize the directory naming format for month grouping (Defaults to `{year}-{month:02d}`)
  - Run `ktoolbox config-editor` to edit these configurations (`Job -> ...`)
  - Or manually edit them in `.env` file or environment variables
    ```dotenv
    # Environment variables (Defaults to False)
    export KTOOLBOX_JOB__GROUP_BY_YEAR=True
    export KTOOLBOX_JOB__GROUP_BY_MONTH=True
  
    # Custom style naming
    export KTOOLBOX_JOB__YEAR_DIRNAME_FORMAT="Year {year}"
    export KTOOLBOX_JOB__MONTH_DIRNAME_FORMAT="Month {month:02d}"
    ```
    Resulting directory structure:
    ```
    creator/
    ├── Year 2020/
    │   ├── Month 01/
    │   │   └── post_title/
    │   └── Month 12/
    │       └── another_post/
    └── Year 2021/
        └── Month 03/
            └── latest_post/
    ```
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)


[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- 新增 **`--keywords-exclude`** 参数用于帖子筛选 - #309
  ```shell
  # 方法1：仅包含特定关键词的帖子
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords="发布"

  # 方法2：排除不需要的关键词帖子（或逻辑）
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords_exclude="公告,投票,分享"
  
  # 方法3：组合筛选（最灵活）
  ktoolbox sync_creator --url="https://kemono.cr/fanbox/user/32165989" --keywords="ブルアカ" --keywords_exclude="全体公開,結果発表"
  ```
- 新增按**年份/月**分组功能用于帖子整理 - #306
  - 可按年份和月份分组下载的帖子，支持自定义目录命名格式
  - 新配置项：
    - `job.group_by_year`：启用按年份分组（默认关闭）
    - `job.group_by_month`：启用按月份分组（默认关闭）
    - `job.year_month_format`：自定义年份分组目录命名格式（默认为 `{year}`）
    - `job.month_format`：自定义月份分组目录命名格式（默认为 `{year}-{month:02d}`）
  - 可通过运行 `ktoolbox config-editor` 编辑这些配置（`Job -> ...`）
  - 或手动在 `.env` 文件或环境变量中编辑
    ```dotenv
    # 环境变量（默认 False）
    export KTOOLBOX_JOB__GROUP_BY_YEAR=True
    export KTOOLBOX_JOB__GROUP_BY_MONTH=True
  
    # 自定义目录命名
    export KTOOLBOX_JOB__YEAR_DIRNAME_FORMAT="{year}年"
    export KTOOLBOX_JOB__MONTH_DIRNAME_FORMAT="{month:02d}月"
    ```
    目录结构示例：
    ```
    creator/
    ├── 2020年/
    │   ├── 01月/
    │   │   └── post_title/
    │   └── 12月/
    │       └── another_post/
    └── 2021年/
        └── 03月/
            └── latest_post/
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)

[//]: # (### 🪲 修复)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.18.2...v0.19.0