## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.18.0/total)

### 💡 Feature

- Add **winloop** support for **Windows** platforms as uvloop alternative - #268 (@IvanmaAcademic)
  - uvloop or winloop can improve the asynchronous performance of the program
  - The executables provided on the **GitHub Releases** page **already include** uvloop or winloop
  - If you installed via **pipx**, you can run the following commands to add uvloop or winloop
    ```shell
    # Windows
    pipx install ktoolbox[urwid,winloop] --force
    # Linux / macOS
    pipx install ktoolbox[urwid,uvloop] --force
    ```
  - This feature is enabled only when the configuration option `use_uvloop` (`KTOOLBOX_USE_UVLOOP`) is set to its default value `True`

- **Preserve image metadata** (**modified/creation time**) when downloading files - #248
- Include filename, post name, post id, URL in downloader **retry logging** for better traceability - #223 (@LuanaNight)
- Add **keyword filtering** support to `sync-creator` command (title) - #292
  - Use the new command option `--keywords`
  - Examples:
    ```shell
    # Filter posts containing "表情、効果音差分" in title
    ktoolbox sync_creator https://kemono.cr/fanbox/user/xxxx --keywords "表情、効果音差分"

    # Filter with multiple keywords (OR logic)
    ktoolbox sync_creator https://kemono.cr/fanbox/user/xxxx --keywords "表情、効果音差分,Live2Dアニメ"
    ```
- Add **selective sequential filename** feature with excludes option - #191
  - For example, if you want to name post images sequentially (1.jpg, 2.jpg, ...) but keep the original filenames for
  videos or archives (such as "March Collection.zip"), you can use this configuration option.
  - Run `ktoolbox config-editor` to edit this configurations (`Job -> sequential_filename_excludes`)
  - Or manually edit it in `.env` file or environment variables
    ```dotenv
    # Enable sequential naming but exclude certain file types
    KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
    KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".psd", ".zip", ".mp4"]'
    ```
  - 📖More information: [Configuration-Reference-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)

[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- 为 **Windows** 平台新增 **winloop** 支持，作为 uvloop 的替代方案 - #268 (@IvanmaAcademic)
  - uvloop 或 winloop 能够提升程序的异步性能
  - **GitHub Releases** 页面中提供的可执行文件**已经包含**了 uvloop 或 winloop
  - 如果你是用 **pipx** 安装的，你可以执行下面的命令来增加包含 uvloop 或 winloop
    ```shell
    # Windows
    pipx install ktoolbox[urwid,winloop] --force
    # Linux / macOS
    pipx install ktoolbox[urwid,uvloop] --force
    ```
  - 当配置项 `use_uvloop`（`KTOOLBOX_USE_UVLOOP`）设为默认值 `True` 时才会启用
- 下载文件时**保留图片元数据**（**修改/创建 日期**） - #248
- 下载器**重试日志**中包含文件名、帖子名称、帖子ID、URL，以便更好地追踪 - #223 (@LuanaNight)
- `sync-creator` 命令新增**关键词过滤**功能（标题） - #292
  - 使用新命令选项 `--keywords`
  - 示例：
    ```shell
    # 过滤标题包含“表情、効果音差分”的帖子
    ktoolbox sync_creator https://kemono.cr/fanbox/user/xxxx --keywords "表情、効果音差分"

    # 使用多个关键词过滤（“或”逻辑）
    ktoolbox sync_creator https://kemono.cr/fanbox/user/xxxx --keywords "表情、効果音差分,Live2Dアニメ"
    ```
- 新增**选择性顺序文件名**功能，可设置排除项 - #191
  - 例如当你想按顺序命名帖子图片（1.jpg, 2.jpg, ...）但又希望保留视频或压缩包的原始文件名（如“3月合集.zip”）时，你可以用这个配置项
  - 可运行 `ktoolbox config-editor` 编辑此配置（`Job -> sequential_filename_excludes`）
  - 或手动在 `.env` 文件或环境变量中编辑
    ```dotenv
    # 启用顺序命名但排除部分文件类型
    KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
    KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".psd", ".zip", ".mp4"]'
    ```
  - 📖更多信息：[配置参考-JobConfiguration](https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.JobConfiguration)
    
[//]: # (### 🪲 修复)

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.17.0...v0.18.0