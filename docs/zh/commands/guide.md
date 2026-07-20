# 命令向导

建议使用连字符形式的命令和选项名。Python Fire 也接受下划线，但连字符更易读。

```bash
ktoolbox -h
ktoolbox sync-creator -h
```

## 下载单篇投稿

可以传入 Pawchive 页面 URL，也可以分别提供三个标识：

```bash
ktoolbox download-post https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download-post \
  --service=fanbox \
  --creator-id=6570768 \
  --post-id=1836570 \
  --path=downloads
```

使用 `--revision-id` 选择修订版本。KToolBox 会获取修订列表并匹配指定 ID；Pawchive 没有独立的单修订接口。设置 `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` 可在下载当前投稿时一并包含全部修订。

传输中断后可重复运行相同命令。已完成文件会被跳过，兼容的临时文件会继续下载。

## 同步作者

检查新作者时，建议先执行有数量上限的同步：

```bash
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --length=1
```

省略 `--length` 会遍历全部可用页面。CLI 的 `--offset` 表示投稿序号，可以是任意非负整数；KToolBox 会将其转换为 Pawchive 使用的 50 条分页偏移。

```bash
# 前 10 篇投稿。
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --length=10

# 第 11 至 15 篇投稿。
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 --offset=10 --length=5
```

可按包含边界的发布日期或不区分大小写的标题文本筛选：

```bash
ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 \
  --start-time=2025-01-01 --end-time=2025-03-01

ktoolbox sync-creator https://pawchive.pw/fanbox/user/6570768 \
  --keywords=preview --keywords-exclude=archive
```

日期格式为 `%Y-%m-%d`。启用 `--save-creator-indices=True` 可写入便于继续同步的作者索引；使用 `--mix-posts=True` 会将文件直接放入作者目录，不创建投稿子目录，也不记录索引。

## 查看公开数据

```bash
# 在公开作者列表中进行本地筛选。
ktoolbox search-creator --name=example --service=fanbox

# 搜索已知作者的投稿。
ktoolbox search-creator-post --id=6570768 --service=fanbox --q=preview --o=0

# 校验并输出单篇投稿模型。
ktoolbox get-post fanbox 6570768 1836570
```

搜索命令和 `get-post` 均可使用 `--dump=path.json` 写入 JSON，避免依赖终端输出。

## 配置工具

```bash
ktoolbox config-editor
ktoolbox example-env
ktoolbox version
ktoolbox site-version
```

配置编辑器需要可选的 `urwid` 依赖。`example-env` 会根据当前配置模型渲染全部字段。
