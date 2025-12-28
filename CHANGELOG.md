## Changes

![Downloads](https://img.shields.io/github/downloads/Ljzd-PRO/KToolBox/v0.24.0/total)

### ✨ Features

- Track and **log files that already exist** during download progress, and add tests to cover file-exists handling
- Throttle the progress display to **0.1s** and only refresh when content changes to reduce flicker and CPU usage
- Add **Python 3.14** support and update CI/workflows to test against 3.14

### 🪲 Fixes

- Ensure that the program **can terminate immediately** when all downloads are complete, rather than having to wait for a period of time before ending.
- Prevent **overcounting completed jobs** when multiple files already exist

- - -

### ✨ 新特性

- 在下载进度中**记录已存在的文件**并在进度中反映，添加了针对文件已存在处理的测试
- 将进度刷新节流为**0.1秒**且仅在内容变更时刷新，以减少抖动和 CPU 使用
- 添加 **Python 3.14** 支持，并在 CI/workflow 中加入对 3.14 的测试

### 🪲 修复

- 确保下载全部完成时程序**能即刻结束**，而不是要等待一段时间才能结束
- 修复当多个文件已存在时**完成计数被重复计算**的问题

## Upgrade

Use this command to upgrade if you are using **pipx**:
```shell
pipx upgrade ktoolbox
```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.23.0...v0.24.0