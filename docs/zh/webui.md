# WebUI

KToolBox WebUI 是绑定单个项目的管理面板，使用 React 与 HeroUI 构建。它与 CLI 共用配置和 Python 应用服务，不会启动或解析 CLI 子进程。任务、尝试记录、日志和输出归属保存在所选项目的 `.ktoolbox/webui.sqlite3`。

## 按任务继续阅读

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **管理项目数据**

    在[项目工作流](webui/project-workflows.md)中管理作者、作品、命名、配置与可选媒体。

-   :material-arrow-right-circle-outline: **监控下载任务**

    在[任务与实时更新](webui/tasks.md)中创建、诊断、暂停、恢复、重新运行和安全删除任务。

-   :material-arrow-right-circle-outline: **部署与维护**

    在[部署参考](webui/reference.md)中查看环境变量、备份、运行环境和多语言覆盖。

</div>

## 安装与启动

安装可选运行依赖并创建项目目录：

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

启动时可以不配置凭据；未配置时，终端会输出本次进程使用的 `admin` 用户名和新随机密码。如需固定凭据，可通过隐藏终端输入生成 Argon2id 密码哈希：

```bash
ktoolbox webui hash-password
```

将账户写入项目 `.env`。请为哈希加引号，以免其中的 `$` 被当作变量：

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

为该项目启动面板：

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

默认监听 `0.0.0.0:8789` 并自动打开本机浏览器。`--host`、`--port`、`--no-open` 只为本次进程覆盖环境配置。缺少 `ktoolbox.toml` 时，启动过程会在终端显示警告，并以原子写入方式创建一份最小有效项目文件。缺少凭据不再阻止启动：用户名留空时使用 `admin`，两种密码均留空时为本次运行生成并在终端输出新密码。

## 安全模型

KToolBox 只提供一个本地 WebUI 账户。显式配置始终优先，`KTOOLBOX_WEBUI__PASSWORD_HASH` 又优先于兼容用的明文 `KTOOLBOX_WEBUI__PASSWORD`。两种密码均未配置时，每次启动都会在内存中生成新密码，并只在该进程的终端中连同有效用户名一起输出。稳定部署应优先配置哈希，并确保两个 dotenv 文件都不进入版本控制。

会话使用随机不透明令牌，SQLite 只保存令牌哈希。浏览器 Cookie 具有 `HttpOnly` 与 `SameSite=Strict` 属性，在 HTTPS 请求下还会增加 `Secure`。修改请求需要每个会话独立的 CSRF 令牌并接受同源检查。登录受速率限制，API 响应禁止缓存，应用还会发送严格的内容、嵌入、来源和浏览器权限安全头。

内置服务使用 HTTP。默认局域网监听仅适合可信网络，否则密码、Cookie、路径、日志和配置在传输中都可能被读取。单机使用请加 `--host 127.0.0.1`；远程使用请通过可信反向代理终止 HTTPS，并限制网络访问。当页面不是安全连接时，登录页和应用顶部会持续显示 HTTP 警告。

同一项目一次只能运行一个调度器。项目锁会阻止两个 WebUI 进程同时修改任务队列与输出。

远程路径选择器使用 KToolBox 进程的文件系统权限。项目范围内的任务、作品和下载结构字段无法离开绑定项目，符号链接也不能绕过此限制；存储桶与日志目录字段则明确使用主机范围，可能显示该账户可访问位置的名称和元数据。选择器可以列出元数据、新建目录，以及在明确确认后删除空目录。删除采用非递归操作：文件、符号链接、项目根目录、主目录根位置和包含任意项目的目录都不会被删除。选择器不会读取文件内容、上传、下载、重命名或删除文件。请输入文件名只会选择路径，不会创建空文件。应将 WebUI 访问视为敏感的主机访问能力，切勿开放给不可信用户。
