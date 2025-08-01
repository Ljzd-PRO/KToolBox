# 向导

前往 [参考](reference.md) 所有命令以及它们的标志/参数.

## 获取帮助总览

- `--help`, `-h`

```bash
ktoolbox -h
```
  
## 获取某个命令的帮助信息

- `--help`, `-h`

```bash
ktoolbox download-post -h
```

## 启动图形化配置编辑器

`config-editor`

```bash
ktoolbox config-editor
```

## 生成一个配置文件样例 (`.env`/`prod.env`)

`example-env`

```bash
ktoolbox example-env
```

## 下载指定的帖子

`download-post`

```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```
??? info "如果部分文件下载失败"
    如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被 **跳过**。
  
## 下载作者的所有帖子

`sync-creator`

```bash
# 下载作者/画师的所有帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --offset=10 --length=5
```
??? info "关于 `creator-indices.ktoolbox` 文件"
    默认情况下你会在作者目录下得到一个 `creator-indices.ktoolbox` 文件，它包含目录下的所有帖子的信息和路径。

??? tip "更新作者目录"
    你可以再次运行命令，文件名相同的文件将会被跳过。

## 下载指定数量的帖子

`sync-creator`

- `--offset`：帖子结果偏移量（或起始偏移量）
- `--length`：要获取的帖子数量，默认获取所有帖子

```bash
# 下载作者/画师最新的 10 个帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --length=10

# 下载作者/画师最新的第 11 至 15 个帖子
ktoolbox sync-creator https://kemono.su/fanbox/user/9016 --offset=10 --length=5
```

## 下载在指定时间范围内发布的帖子

`sync-creator`

- `--start-time`：下载指定开始时间范围内的帖子
- `--end-time`：下载指定结束时间范围内的帖子

```bash
# 从 2023-8-5 到 2023-12-6
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --start-time=2023-8-5 --end-time=2023-12-6

# 从 2023-8-5 到 现在
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --start-time=2023-8-5

# 2023-8-5 之前
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --end-time=2023-8-5
```

### 时间格式

时间值应当符合 `%Y-%m-%d` 格式，例如：

- `2023-12-7`
- `2023-12-07`
- `2023-12-31`
