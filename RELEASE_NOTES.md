# KToolBox v1.0.0

> [!WARNING]
> KToolBox v1 is a new major release and has not yet received enough real-world validation. Some workflows may still contain defects. Back up your configuration and downloads, begin with a small bounded task, and report problems through GitHub Issues.

KToolBox v1 is the first release of the redesigned Pawchive generation. Because the Kemono site is no longer available, **Pawchive is now the only supported backend and the default service**. This is a breaking upgrade from v0.24.0: it replaces the API and CLI foundations, adds a project-oriented HeroUI management panel, and introduces multi-author and scheduled synchronization.

中文说明在前，后附 English summary。

## 主要变化

### Pawchive API 与下载核心

- 使用实例化异步 `PawchiveClient` 完整实现 Pawchive OpenAPI 中 14 个无需登录的公开操作，并明确排除 5 个需要账号登录的收藏操作。
- 请求参数和响应字段使用 Pydantic v2 类型化校验；传输、HTTP、认证、未找到、冲突和上游响应不兼容均有明确异常类型。
- 保留 Pawchive 原始 OpenAPI，使用可审查兼容覆盖生成规范化 Schema 与模型，并在 CI 中检查确定性生成结果。
- 支持断点续传、文件大小限制、筛选、修订选择、元数据、可选主文件（封面）下载、硬链接存储桶及结构化失败报告。
- 修复上游实际数据中的标签类型变化、延迟附件字段、时间戳差异，以及并发下载进度可能倒退或提前把任务标为完成的问题。

### 全新 CLI 与多作者同步

- 使用 Cyclopts 替换 Python Fire，提供常规连字符参数、Rich 帮助、Shell 补全、JSON 输出及明确的 `0`、`1`、`2`、`130` 退出码。
- `sync` 可一次同步任意数量作者；无参数时同步项目中所有已启用作者，并以有界并发、公平队列和共享下载池流式处理。
- 使用 Rich 展示稳定的总进度、单文件速度和总下载速度；非 TTY、`NO_COLOR` 与 `--plain` 使用可预测的逐行输出。
- 新增项目作者清单和可扩展“忽略规则”，支持全局/指定作者作用域、递归任一/全部条件、取反、包含、等于、正则和存在判断。
- 在统一命令入口捕获用户中断和预期配置拒绝，只输出简洁日志，不再向普通用户展示整段 traceback。

### HeroUI WebUI

- 新增 React 19、TypeScript、Tailwind CSS v4、HeroUI v3 管理面板，使用 `ktoolbox[webui]` 安装；生产资源同时打包进 wheel 和独立可执行文件。
- 支持登录保护、CSRF/Origin 校验、会话与项目锁、深浅主题、响应式桌面/移动布局，以及简体中文、繁体中文、英语、日语、韩语、法语和俄语。
- 提供项目概览、任务队列、作者清单、作品查询、忽略规则、全局配置、命名格式、自动同步、MCP、系统与关于页面。
- 持久任务队列支持并发、资源冲突阻塞、去重、暂停、继续、停止、编辑、批量操作、已完成同步重新运行、安全删除预览及重启恢复。
- 使用全局 SSE 自动刷新任务、作者、配置、MCP 令牌和文件系统视图；断线时自动降级为本地查询轮询，并保护未保存表单。
- 任务详情提供总速度、活动作者、活动下载、等待重试、结构化失败原因和可筛选日志；下载面板采用稳定高度，不再随文件数量导致页面抖动。
- 新增认证远程路径选择器，可浏览主机目录、搜索、创建目录和确认删除空目录。
- 新增浏览器本地可选 NSFW 模式。默认关闭时不请求或预留媒体；开启并确认后可通过同源认证代理显示作者头像、横幅、作品封面和分页画廊。

### 项目配置、命名与自动同步

- `ktoolbox.toml` Schema 升级至 v5，统一保存作者清单、忽略规则、默认输出目录、项目级命名格式和自动同步计划。
- 默认输出目录为项目下的 `downloads`；任务、CLI、MCP 和自动同步可继承，也可显式保存到项目外的绝对路径。
- 附件顺序命名默认开启，不可读的 Pawchive 存储名会按项目格式保存并在实时下载、重试和日志中显示为 `1.png`、`2.png` 等最终文件名。
- 命名格式页面提供目录树预览、历史布局版本及可暂停/继续/取消回滚的旧目录转换。
- 旧下载转换器支持项目历史格式，以及粘贴旧 `.env` 或 TOML 作为源格式；当前项目配置始终作为只读目标，原始粘贴内容不会持久化。
- 检测到旧 dotenv 命名字段时不会在启动阶段静默修改文件；登录后通过带备份、逐字段确认的迁移向导处理，目录扫描仍需单独确认。
- 自动同步支持多个计划、Cron 或固定间隔、IANA 时区、多作者选择、暂停和立即执行、按作者检查点、重叠窗口去重，以及按当天/近 1、7、14、30 天统计最近新增作品数。

### WebUI OpenAPI 与 MCP

- `webui/openapi.yaml` 成为 WebUI REST API 的正式确定性契约，并用于生成 TypeScript 类型。
- WebUI 启动时在同一进程和端口挂载 Streamable HTTP MCP `/mcp`。
- MCP 使用再次确认 WebUI 密码后签发的高熵 Bearer Token，支持只读/管理权限、限时或永久令牌、撤销及最后使用时间。
- MCP 页面提供工具目录、OpenAPI 下载和通用客户端、Claude、Cursor、VS Code、Codex 的可复制配置。
- 工具只开放经过筛选且有边界的项目能力，不开放登录、原始秘密配置、任意主机文件操作或删除下载输出。

### 测试、质量与发布产物

- 默认测试完全离线，使用 RESPX、HTTPX MockTransport、临时文件系统和 Socket 禁用保护。
- API 手写层及 WebUI 认证/配置/调度核心要求 100% 行与分支覆盖率，全项目覆盖率至少 85%。
- CI 覆盖 Python 3.10 至 3.14、Ruff、Mypy、OpenAPI 生成差异、Vitest、Playwright、Axe、严格 MkDocs 构建、wheel 内容检查和独立程序冒烟测试。
- Release 直接提供 wheel、sdist、Windows x64/x86、macOS arm64/x64、Linux x64/arm64，以及 `SHA256SUMS` 校验文件。

## 破坏性变更

- 最低 Python 版本由 3.8 提升至 **3.10**；支持范围为 Python 3.10 至 3.14。
- Kemono/Coomer 兼容层已删除，默认且唯一正式支持的后端为 Pawchive。
- 旧 `BaseAPI`、类调用器、模块级 `get_*`、`APIRet` 和 `.data.post` 等包装响应已删除，不提供 Python API 兼容适配器。
- `session_key` 从 API 配置移动到下载器配置，且只用于文件请求。
- CLI 从 Fire 命令面改为 Cyclopts 命令树。七个旧命令名暂时以隐藏别名保留，但会提示弃用。
- 项目命名、默认输出目录和自动同步计划改由 `ktoolbox.toml` 管理；旧 dotenv 命名字段不再作为可编辑全局配置。
- `.env` 与 `prod.env` 是本地秘密配置文件，不应继续受 Git 版本控制；公开示例为 `example.env`。

## 从 v0.24.0 迁移

### 1. 备份并小范围验证

升级前请备份：

- `.env`、`prod.env` 和 `ktoolbox.toml`。
- 已下载目录和自定义命名模板。
- 仍需保留的 v0 自动化脚本。

请先结束或取消 v0 下载。升级后先同步一位作者的一件作品，并禁用不需要的附件或主文件，确认目录与权限正确后再进行完整同步。

### 2. 安装 v1

核心 CLI：

```bash
pipx install 'ktoolbox==1.0.0'
```

包含 WebUI：

```bash
pipx install 'ktoolbox[webui]==1.0.0'
```

也可以从本 Release 下载适合系统架构的独立压缩包，并使用 `SHA256SUMS` 校验文件完整性。

### 3. 更新后端与会话配置

默认端点已经内置；仅在确有需要时覆盖：

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

将旧变量：

```dotenv
KTOOLBOX_API__SESSION_KEY=...
```

迁移为：

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=...
```

### 4. 更新 CLI 命令

| v0 | v1 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

参数使用 `--creator-id` 一类连字符拼写。旧别名暂时接受下划线拼写，但请尽快更新脚本。

### 5. 建立项目配置

在同步项目目录运行 WebUI：

```bash
ktoolbox webui /path/to/project
```

若目录中没有 `ktoolbox.toml`，WebUI 会先警告再创建最小项目配置。未设置固定账户时，终端会输出本次启动使用的 `admin` 和随机密码。

在“命名格式”页面检查默认输出目录和目录树。若检测到 v0 命名字段，请在迁移向导中逐项核对；配置迁移和旧下载目录转换是两个独立步骤，任何文件移动都需要再次预览和确认。

### 6. 更新 Python API 调用

使用实例化的异步客户端，成功时直接接收 Pydantic 模型：

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        works = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(works))


asyncio.run(main())
```

错误现在抛出 `PawchiveError` 的类型化子类。账号收藏相关 API 不在支持范围内。

更完整的步骤见[简体中文迁移指南](https://github.com/Ljzd-PRO/KToolBox/blob/v1.0.0/docs/zh/migration-v1.md)和[英文迁移指南](https://github.com/Ljzd-PRO/KToolBox/blob/v1.0.0/docs/en/migration-v1.md)。

## 已知风险与反馈

- v1 涉及后端、CLI、配置、下载调度和 WebUI 的大范围重写，尚未覆盖足够多的真实作者、文件组合、旧目录结构及网络环境。
- Pawchive 上游数据可能出现 OpenAPI 尚未描述的字段形态。KToolBox 会尽量给出结构化失败原因，但仍可能需要兼容修复。
- 自动同步、目录转换和输出清理会操作持久数据。首次使用请保留备份并先用小目录验证。
- NSFW 媒体预览默认关闭；开启前请确认当前设备和网络环境适合显示相关内容。

问题反馈：[GitHub Issues](https://github.com/Ljzd-PRO/KToolBox/issues)。提交问题时请删除 Cookie、下载会话、令牌、作品正文和完整私有路径。

## 下载与校验

| 产物 | 用途 |
| --- | --- |
| `ktoolbox-1.0.0-*.whl` | Python wheel |
| `ktoolbox-1.0.0.tar.gz` | Python 源码包 |
| `ktoolbox-Windows-x64-v1.0.0.zip` | Windows 64 位独立程序 |
| `ktoolbox-Windows-x86-v1.0.0.zip` | Windows 32 位独立程序 |
| `ktoolbox-macOS-arm64-v1.0.0.zip` | Apple Silicon 独立程序 |
| `ktoolbox-macOS-x64-v1.0.0.zip` | Intel macOS 独立程序 |
| `ktoolbox-Linux-x64-v1.0.0.zip` | Linux x64 独立程序 |
| `ktoolbox-Linux-arm64-v1.0.0.zip` | Linux ARM64 独立程序 |
| `SHA256SUMS` | 全部发布文件的 SHA-256 校验值 |

完整实现记录见 [CHANGELOG.md](https://github.com/Ljzd-PRO/KToolBox/blob/v1.0.0/CHANGELOG.md) 或 [v0.24.0...v1.0.0](https://github.com/Ljzd-PRO/KToolBox/compare/v0.24.0...v1.0.0)。

---

## English summary

KToolBox v1.0.0 is the first release of a breaking Pawchive-focused generation. Kemono is no longer available, so Pawchive is now the only supported backend and the default service.

### Highlights

- A typed asynchronous `PawchiveClient` covers all 14 public OpenAPI operations; the five account-authenticated favorites operations remain intentionally unsupported.
- The Cyclopts CLI adds conventional hyphenated options, Rich help and progress, aggregate speed, explicit exit codes, multi-creator synchronization, and structured failures.
- Project Schema v5 stores the creator roster, scoped post blockers, default output, naming layouts, and multiple automatic synchronization plans.
- Sequential attachment names are enabled by default, and live download, retry, and log views show the final project-configured names instead of opaque Pawchive storage identifiers.
- The new optional HeroUI WebUI provides a persistent task queue, pause/resume/stop/rerun and bulk operations, global SSE refresh, creator/work search, configuration and naming workflows, safe cleanup previews, and seven interface languages.
- Project naming migration can scan real download roots, preview statistics, pause or resume conversion, and roll back cancellation. It supports historical project layouts and pasted legacy `.env`/TOML source layouts.
- Automatic synchronization supports Cron or fixed intervals, IANA time zones, per-creator checkpoints, overlap-safe deduplication, and privacy-preserving recent-update counts.
- A curated Streamable HTTP MCP endpoint starts with WebUI at `/mcp`, using password-confirmed, hashed, revocable bearer tokens and bounded tools.
- Opt-in browser-local NSFW mode can display validated creator and work images through an authenticated same-origin proxy; it remains text-only and makes no media requests by default.
- Release assets include wheel, sdist, standalone Windows/macOS/Linux builds for x64 and ARM where applicable, and `SHA256SUMS`.

### Migration checklist

1. Back up `.env`, `prod.env`, `ktoolbox.toml`, naming templates, and existing downloads.
2. Upgrade to Python 3.10-3.14 and install `ktoolbox==1.0.0` or `ktoolbox[webui]==1.0.0`.
3. Move `KTOOLBOX_API__SESSION_KEY` to `KTOOLBOX_DOWNLOADER__SESSION_KEY`.
4. Replace v0 Fire commands with `download`, `sync`, `creator ...`, `post ...`, and `config ...` commands.
5. Review the project default output and naming layout in `ktoolbox.toml`; use the guided WebUI migration before moving old downloads.
6. Replace removed library wrappers with an instantiated async `PawchiveClient` and direct Pydantic response models.
7. Run one bounded creator/work test before a full synchronization.

See the [English migration guide](https://ktoolbox.readthedocs.io/latest/migration-v1/), the [Simplified Chinese migration guide](https://ktoolbox.readthedocs.io/latest/zh/migration-v1/), and the detailed [CHANGELOG.md](https://github.com/Ljzd-PRO/KToolBox/blob/v1.0.0/CHANGELOG.md).

Please report sanitized problems through [GitHub Issues](https://github.com/Ljzd-PRO/KToolBox/issues). Do not include cookies, downloader sessions, MCP tokens, post content, or private absolute paths.
