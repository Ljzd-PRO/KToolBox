## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.18.2/total)

[//]: # (### 💡 Feature)

### 🪲 Fix

- Fixed the issue where **warning messages** were displayed regardless of whether **`job.include_revisions`** was enabled or not.
- Fixed the issue where extracted external links contained extra characters (v0.18.0)
  - Related configuration options: `job.extract_external_links`, `job.external_link_patterns`

- - -

[//]: # (### 💡 新特性)

### 🪲 修复

- 修复了无论是否开启 **`job.include_revisions`** 都会提示**警告信息**的问题
- 修复了程序提取的外部链接（external links）包含多余字符的问题 (v0.18.0)
  - 相关配置选项：`job.extract_external_links`, `job.external_link_patterns`

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.18.1...v0.18.2