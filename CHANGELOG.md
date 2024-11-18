## Changes

### 💡 Feature

- The `search-creator` command will include search results with similar names.
  - For example, the search parameter `--name abc` might return author information such as: `abc, abcd, hi-abc`
- Share an HTTPX client to reuse underlying TCP connections through an HTTP connection pool when calling APIs and downloading, 
**significantly improving query and download speeds as well as connection stability**

[//]: # (### 🪲 Fix)

- - -

### 💡 新特性

- search-creator 搜索作者的命令将包含那些名字相近的搜索结果
  - 如搜索参数 `--name abc` 可能得到如下作者信息：`abc, abcd, hi-abc`
- 共享 HTTPX 客户端，调用 API 和下载时将通过 HTTP 连接池重用底层 TCP 连接，**显著提升查询、下载速度和连接稳定性**

[//]: # (### 🪲 修复)

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.10.0...v0.11.0