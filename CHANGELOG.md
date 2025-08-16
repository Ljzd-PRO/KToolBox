## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.19.2/total)

### 💡 Feature

> - Improved the error log format to make it easier to read and understand (v0.19.1)

### 🪲 Fix

- Fixed the issue where **`content`** data of works could not be obtained due to **Kemono API changes**, resulting in missing **`content.txt`** and `external_links.txt` - #316
> - Fixed the issue where author information and work data could not be retrieved due to **Kemono API changes** - #315 (v0.19.1)
>  - Error messages: `Kemono API call failed: ...`, `404 Not Found`, `403 Forbidden`, ...

- - -

### 💡 新特性

> - 改进报错的日志格式，使其更易于阅读和理解 (v0.19.1)

### 🪲 修复

- 修复由于 **Kemono API 变更** 导致的作品 **`content`** 数据无法获取进而导致 **`content.txt`, `external_links.txt` 缺失**的问题 - #316
> - 修复 Kemono **API 变更**导致的作者信息和作品数据**获取失败**的问题 - #315 (v0.19.1)
>  - 报错信息：`Kemono API call failed: ...`, `404 Not Found`, `403 Forbidden`, ...

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.19.1...v0.19.2