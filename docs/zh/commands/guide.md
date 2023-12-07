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

## 下载指定的作品

`download-post`

```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```
??? info "如果部分文件下载失败"
    如果部分文件下载失败，你可以尝试重新运行命令，已下载完成的文件会被 **跳过**。
  
## 下载作者的所有作品

`sync-creator`

```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/9016
```
??? info "输出"
    默认情况下你会在作者目录下得到一个 `creator-indices.ktoolbox` 文件，你可以用它来更新目录。
  

## 更新一个作者目录

`sync-creator`

- `--update-with`

```bash
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --update-with=./xxx/creator-indices.ktoolbox
```
??? info "关于 `creator-indices.ktoolbox` 文件"
    `creator-indices.ktoolbox` 包含目录下的所有作品的信息和路径。

## 下载在指定时间范围内发布的作品

`sync-creator`

- `--start-time`
- `--end-time`

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
