# 常见问题

## 为什么没有账号收藏功能？

KToolBox v1 实现 Pawchive 中无需登录的 14 个操作。OpenAPI 中受 `cookieAuth` 保护的 5 个操作明确排除，因此 API 客户端不会接受或发送账号会话。

投稿标记是独立的公开操作，已经实现。请有意识地调用：成功标记会改变服务端状态，重复标记可能抛出 `PawchiveConflictError`。

## API 调用失败时怎么办？

CLI 会报告类型化的 Pawchive 错误，不会返回只解析了一部分的响应。常见类型包括传输、HTTP、认证、未找到、冲突和响应校验错误。

- 检查 URL 或 `service`、作者 ID、投稿 ID 是否正确。
- 网络较慢时增大 `KTOOLBOX_API__TIMEOUT`。
- 对临时传输错误、`429` 或 `5xx`，调整 `KTOOLBOX_API__RETRY_TIMES` 与 `KTOOLBOX_API__RETRY_INTERVAL`。
- 不要向 API 配置添加账号 Cookie；API 请求不会使用它。

重定向、普通 `4xx`、冲突和非法响应数据不会重试。

## 文件下载为什么返回 403？

若文件主机要求特定资源携带会话，可设置只属于下载器的密钥：

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

该 Cookie 仅用于文件下载请求，不会发送到 Pawchive API。请将 `.env` 和 `prod.env` 视作可能包含密钥的本地文件，不要提交。

## 如何继续中断的下载？

重新运行相同命令即可。KToolBox 会跳过完整的目标文件。如果存在带 `downloader.temp_suffix` 的未完成文件，且服务器支持范围请求，下载器会请求剩余字节并校验合并后的大小。

## 如何禁用封面或附件？

```dotenv
# 只下载附件。
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# 只下载封面。
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file` 指投稿主文件，通常为封面。两个选项默认均为 `True`。

## 能否把附件直接放进投稿目录？

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 如何避免文件名过长？

使用顺序命名或格式精度限制：

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## 如何配置代理？

HTTPX 会读取标准代理环境变量：

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

PowerShell：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## 为什么配置编辑器无法打开？

安装可选的终端 UI 依赖：

```bash
pip install "ktoolbox[urwid]"
# 或
pipx install "ktoolbox[urwid]" --force
```

## 如何定期同步很多作者？

将每位作者加入项目清单，可选设置短别名，然后执行无目标 `sync`：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

使用 `creator disable` 可保留作者但不加入无目标同步；仍可显式同步已禁用别名。作者准备与文件传输使用不同并发限制，因此大型作者不会长期占据全部已就绪下载。

## 如何为不同作者排除不同主题？

在 `ktoolbox.toml` 中添加不同 `[[blockers]]`。所有作者共享的规则使用 `scope.mode = "global"`；特定作者规则使用 `scope.mode = "creators"` 并填写精确 `service:id`。屏蔽器按文件顺序求值，第一个命中后停止。

长时间同步前先校验正则与作用域：

```bash
ktoolbox config validate
```

## 为什么重定向日志中的进度显示不同？

Rich 实时进度仅用于交互终端。界面会显示每个活动文件的速度与预计剩余时间，并在 `Files` 总体行显示所有活动下载的速度总和。管道、CI、`NO_COLOR` 与 `--plain` 使用稳定逐行输出，日志不会破坏 ANSI 实时区域。需要无颜色交互布局时使用 `--no-color`，完全隐藏进度与普通日志时使用 `--quiet`。

## uvloop 或 winloop 是必需的吗？

不是。它们只是可选的事件循环优化。Linux/macOS 使用 `ktoolbox[uvloop]`，Windows 使用 `ktoolbox[winloop]`。两者都未安装时，KToolBox 会继续使用 Python 标准 asyncio 循环。

## 为什么杀毒软件可能标记打包后的可执行文件？

部分启发式扫描会标记 PyInstaller 包或下载管理器。发布包通过仓库中公开的自动化流程构建；也可以改用 `pipx` 安装，或审查源码后自行构建。
