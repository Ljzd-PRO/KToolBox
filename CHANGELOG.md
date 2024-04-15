## Changes

[//]: # (### 💡 Feature)

### 🪲 Fix

- Fix `FileNotFoundError` occurred when filename contains special characters (#94)
- Fix `TypeError` occurred when using `--start-time`, `--end-time` options and posts had no `published` property (#93)
- Fixed incorrect argument order when using bucket storage (#89 - @Nacosia)
- Duplicate file check after HTTP connection started (#88)

- - -

[//]: # (### 💡 新特性)

### 🪲 修复

- 修复当文件名包含特殊字符时会出现 `FileNotFoundError` 错误的问题 (#94)
- 修复当使用 `--start-time`, `--end-time` 参数且作品 `published` 属性不存在的情况下会出现 `TypeError` 错误的问题 (#93)
- 修复当使用桶储存时参数顺序不正确的问题 (#89 - @Nacosia)
- 在建立 HTTP 连接后进行重复文件检查 (#88)

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.5.1...v0.5.2