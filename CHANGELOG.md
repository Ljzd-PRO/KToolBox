## Changes

### 💡 Feature

- Added support for downloading works within a specified range of quantity.
  - Added `--offset`, `--length` options in `sync-creator` command
  - `--offset`: Posts result offset (or start offset)
  - `--length`: The number of posts to fetch, defaults to fetching all posts
  
  ```bash
  # Download latest 10 posts of the creator/artist
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx --length=10
  
  # Download latest No.11-No.15 posts of the creator/artist
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx --offset=10 --length=5
  
  # Download all posts of the creator/artist
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx
  ```

- - -

### 💡 新特性

- 增加下载指定数量范围作品的支持
  - 在 `sync-creator` 命令中增加了 `--offset`, `--length` 选项
  - `--offset`：作品结果偏移量（或起始偏移量）
  - `--length`：要获取的作品数量，默认获取所有作品
  
  ```bash
  # 下载作者/画师最新的 10 个作品
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx --length=10
  
  # 下载作者/画师最新的第 11 至 15 个作品
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx --offset=10 --length=5
  
  # 下载作者/画师的所有作品
  ktoolbox sync-creator https://kemono.su/fanbox/user/xxxx
  ```

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.5.0...v0.5.1