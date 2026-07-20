# 命令指南

KToolBox 使用 Cyclopts 命令、常规连字符选项和 Rich 帮助。帮助会直接打印，绝不会打开分页器。

```bash
ktoolbox --help
ktoolbox sync --help
```

![KToolBox 命令概览](../../assets/cli-overview.png)

全局选项可以放在命令之前或之后：

```bash
ktoolbox --config ./ktoolbox.toml --plain sync
ktoolbox creator list --json --config ./ktoolbox.toml
```

`--verbose` 输出诊断日志，`--quiet` 隐藏进度和普通日志，`--plain` 使用稳定逐行进度，`--no-color` 保留交互布局但不输出 ANSI 颜色。

## 下载单篇投稿

可传入 Pawchive 页面 URL，或完整的三个身份字段：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download \
  --service fanbox \
  --creator-id 6570768 \
  --post-id 1836570 \
  --output downloads
```

使用 `--revision-id` 选择一个修订。Pawchive 没有单修订详情端点，因此 KToolBox 会读取修订列表并匹配该 ID。设置 `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` 可在下载当前投稿时包含全部修订。

中断后重新执行同一命令即可。完整文件会被跳过，兼容的临时文件会通过 HTTP Range 续传。显式 `download` 不应用同步屏蔽器。

## 同步多个作者

`sync` 接受任意数量的作者 URL、`service:id` 身份或项目清单别名：

```bash
# 限制单作者首次同步。
ktoolbox sync fanbox:123 --length 1

# 多作者共享一个并发下载池。
ktoolbox sync fanbox:123 patreon:456 studio-c --length 10
```

省略 `--length` 会遍历全部页面。CLI 的 `--offset` 表示投稿索引，KToolBox 会将其转换为 Pawchive 的 50 项分页偏移量。

```bash
ktoolbox sync fanbox:123 --offset 10 --length 5
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

作者目录固定为 `作者名 [service-creator_id]`。最多同时运行 `job.creator_concurrency` 个作者生产者，其有界队列通过公平轮转调度器进入同一个下载池；`job.count` 控制文件传输并发。首批任务生成后立即下载，无需等待全部作者加载完成。

单个作者失败不会丢弃其他作者已完成的内容。失败作者不会覆盖旧索引，命令会在打印汇总后以状态 `1` 退出。

## 维护作者清单

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add https://pawchive.pw/patreon/user/456 --alias studio-b
ktoolbox creator disable studio-b
ktoolbox creator list
ktoolbox creator enable studio-b
ktoolbox creator remove studio-b
```

不带目标运行 `ktoolbox sync` 会同步清单中全部已启用作者；显式指定已禁用作者时仍会执行。`service:id` 必须唯一，别名可选且唯一，配置写回会保留注释。

## 排除非作品投稿

在 `ktoolbox.toml` 中定义有序字段屏蔽器。它们可全局生效或仅作用于指定 `service:id` 作者，并可检查标题、正文、标签、文件名、ID 及嵌套列表路径。第一个命中的屏蔽器会在详情、修订、元数据、目录和下载任务创建前排除投稿。

完整示例见[配置指南](../configuration/guide.md#post-blockers)。`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 仅作为迁移用的弃用全局标题屏蔽器保留。

## 查询公开数据

```bash
ktoolbox creator search --name example --service fanbox
ktoolbox post search --creator-id 6570768 --service fanbox --query preview --offset 0
ktoolbox post show fanbox 6570768 1836570
```

查询命令默认输出紧凑 Rich 表格。添加 `--json` 可向 stdout 输出机器可读 JSON，日志与进度始终写入 stderr；`--dump path.json` 还会将校验后的模型写入文件。

## 配置工具

```bash
ktoolbox config path
ktoolbox config validate
ktoolbox config example
ktoolbox config edit
ktoolbox site-version
```

编辑器需要可选 `urwid` 依赖。它可编辑 dotenv 设置与作者/屏蔽器项目文档，并在保存前校验。

## 退出状态

| 状态码 | 含义 |
| --- | --- |
| `0` | 命令成功完成。 |
| `1` | 远程操作、作者或文件下载失败；保留已完成的部分。 |
| `2` | 参数或配置无效。 |
| `130` | 用户中断命令。 |

预期错误不会显示 Python traceback。
