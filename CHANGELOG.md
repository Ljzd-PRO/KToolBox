# KToolBox v1.0.0

KToolBox v1 is a breaking release that moves the project to Pawchive as its only supported backend.

## Breaking changes

- Raise the minimum Python version to 3.10 and support Python 3.10 through 3.14.
- Replace the previous backend defaults with `https://pawchive.pw/api/v1`, `https://pawchive.pw`, and `https://file.pawchive.pw/data`.
- Remove the legacy `BaseAPI`, class invokers, module-level `get_*` functions, `APIRet`, and wrapped response shapes without compatibility aliases.
- Move `session_key` from API configuration to downloader configuration. It is sent only to file requests; the API client has no account session.
- Remove the old remote-request test suite and backend-specific documentation and examples.

## Pawchive API

- Add an instantiated asynchronous `PawchiveClient` implementing all 14 public OpenAPI operations.
- Explicitly exclude the five account-favorites operations protected by `cookieAuth`; public post flagging remains implemented.
- Add strict Pydantic request constraints and generated Pydantic v2 response models covering all documented and confirmed fields while preserving unknown fields.
- Add typed transport, HTTP, authentication, not-found, conflict, and response-validation exceptions.
- Retry only transport errors, `429`, and `5xx`; do not follow redirects or retry ordinary `4xx` and validation failures.
- Preserve the original Pawchive Schema, apply auditable compatibility overrides, validate the normalized OpenAPI document, and verify deterministic model generation in CI.

## Core and CLI

- Replace Python Fire with Cyclopts commands, direct Rich help, shell completion, conventional hyphenated options, machine-readable output, and explicit `0`/`1`/`2`/`130` exit codes.
- Add hidden compatibility aliases for the seven v0 command names with one deprecation warning per invocation.
- Add project-level `ktoolbox.toml` with an enabled/disabled creator roster, aliases, comment-preserving atomic writes, path discovery, validation, and Urwid editor support.
- Add extensible asynchronous post blockers with ordered global/creator scopes, recursive any/all rules, negation, safe nested field selectors, and contains/equals/regex/exists operations.
- Add multi-creator synchronization with bounded concurrent producers, fair per-creator queue rotation, streaming startup, one shared client and download pool, partial-failure summaries, and stable creator directories.
- Replace tqdm and the handwritten ANSI progress layer with Rich live progress, per-file and aggregate transfer speeds, Rich-aware logging, and deterministic plain output for non-TTY, `NO_COLOR`, and `--plain` environments.
- Inject and reuse `PawchiveClient` throughout actions, task generation, and CLI workflows.
- Resolve creator names through profile requests and use the Pawchive post-list and direct post response shapes.
- Select a requested revision from the revision list instead of calling a nonexistent detail endpoint.
- Retain resumable downloads, filters, progress reporting, metadata output, file-size limits, and optional hard-link bucket storage under the new models.

## HeroUI WebUI

- Add an optional React 19, TypeScript, Tailwind CSS v4, HeroUI v3, and Lucide management panel whose production assets are embedded in wheels and standalone builds.
- Add `ktoolbox webui [PROJECT_DIR]`, host/port/browser overrides, and `webui hash-password`; use terminal-printed `admin`/random credentials when account settings are absent and prefer configured Argon2id password hashes.
- Warn and atomically create a minimal `ktoolbox.toml` when the selected WebUI project does not have one yet.
- Add rate-limited authentication with hashed opaque sessions, strict cookies, CSRF and Origin validation, security headers, redacted configuration snapshots, and a persistent project lock.
- Add bilingual, responsive light/dark workflows for project overview, `.env`/`prod.env` and TOML editing, author roster, recursive blockers, Pawchive creator/post queries, revision inspection, site version, and task creation.
- Add authenticated remote filesystem pickers to every filesystem-backed WebUI path field, with project/host scopes, breadcrumbs, search, hidden-item control, pagination, safe directory creation, and manual path entry.
- Generate readable bilingual form labels and descriptions from Pydantic metadata and English/Chinese configuration docstrings; include source indicators, secret masking, typed and advanced editors, validation, diff preview, ETag conflict detection, and atomic writes.
- Add a WAL-backed SQLite queue with concurrent scheduling, resource blocking and deduplication, immutable attempts, pause/resume/stop/edit/reorder/rerun/delete actions, restart recovery, SSE replay, aggregate/per-file speeds, ETA, and structured logs.
- Add ownership-aware output cleanup previews that skip symbolic links and any pre-existing, shared, or modified files.
- Rebuild HeroUI form primitives with gray-off/blue-on switches, state-correct checkboxes, centered compact list controls, continuous modal surfaces, and direct icon actions for task, creator, and blocker rows.
- Persist presentation-only task target snapshots so queues remain readable offline by post title and creator name without changing execution, deduplication, or resource locks.
- Standardize Chinese product terminology as “作品”, “平台”, and “忽略规则”, including the overview heading and the sync-all-creators control.
- Cache Pawchive profile names for creator presentation, with bounded refresh concurrency, stale-value fallback, and creator-ID fallback.
- Add locale-aware controlled sorting to task, creator, post, and recent-task views without changing scheduler order.
- Add filtered dashboard navigation and URL-persistent task and creator filters.
- Replace free-form platform fields with HeroUI ComboBoxes that provide Patreon, Pixiv, and Fanbox suggestions while accepting custom platforms.
- Enrich compact HeroUI choices with icons and restrained semantic tones, and refresh verified desktop/mobile screenshots after six-slice visual review.

## Testing and quality

- Replace the test suite with fully offline tests using RESPX, HTTPX transports, dependency injection, and temporary filesystems; accidental sockets are blocked.
- Cover every public operation, parameter and response contract, status mapping, retry path, malformed response, schema drift report, and client lifecycle.
- Enforce 100% line and branch coverage for the handwritten API layer and WebUI authentication/configuration/scheduler core, plus at least 85% for the full project.
- Add Vitest/Testing Library and offline Playwright tests for routes, task lifecycle, desktop/mobile layouts, light/dark themes, and Axe accessibility checks.
- Add browser geometry checks and verified screenshots for single-frame tables, continuous modal actions, centered list switches, responsive tabs, readable task targets, and selected-only checkbox indicators.
- Add Ruff, Mypy, warnings-as-errors, Python and TypeScript OpenAPI generation checks, Node 24 lockfile builds, wheel/PyInstaller asset checks, `compileall`, package builds, and strict bilingual documentation builds.

## Fixes

- Accept the timestamp shape returned by Pawchive while retaining validated datetime models.
- Make local bucket capability checks use real temporary paths and clean up hard-link probes.
- Strip query strings from bucket paths, deduplicate size filtering, and account for existing temporary bytes when validating resumed transfers.

---

KToolBox v1 是一次不兼容升级，项目改为仅支持 Pawchive 后端。

## 破坏性变更

- 最低 Python 版本提升至 3.10，支持 Python 3.10 至 3.14。
- 默认端点替换为 `https://pawchive.pw/api/v1`、`https://pawchive.pw` 和 `https://file.pawchive.pw/data`。
- 直接删除旧 `BaseAPI`、类调用器、模块级 `get_*` 函数、`APIRet` 和包装响应结构，不提供兼容别名。
- 将 `session_key` 从 API 配置迁移到下载器配置。它只发送给文件请求；API 客户端不提供账号会话。
- 删除旧远程请求测试套件以及旧后端专属文档和示例。

## Pawchive API

- 新增实例化异步 `PawchiveClient`，实现 OpenAPI 中全部 14 个公开操作。
- 明确排除受 `cookieAuth` 保护的 5 个账号收藏操作；公开作品标记仍然实现。
- 新增严格的 Pydantic 请求约束和生成的 Pydantic v2 响应模型，覆盖全部文档字段与已确认字段，同时保留未知字段。
- 新增传输、HTTP、认证、未找到、冲突和响应校验类型化异常。
- 只重试传输错误、`429` 和 `5xx`；不跟随重定向，也不重试普通 `4xx` 与校验失败。
- 保留 Pawchive 原始 Schema，以可审查覆盖修正规范，校验规范化 OpenAPI，并在 CI 中验证模型生成结果确定一致。

## 核心与 CLI

- 使用 Cyclopts 命令、直接 Rich 帮助、Shell 补全、常规连字符选项、机器可读输出和明确的 `0`/`1`/`2`/`130` 退出码替换 Python Fire。
- 为 7 个 v0 命令名新增隐藏兼容别名，每次调用提示一次弃用。
- 新增项目级 `ktoolbox.toml`，包含可启停作者清单、别名、保留注释的原子写入、路径发现、校验和 Urwid 编辑支持。
- 新增可扩展异步作品忽略规则，支持有序全局/作者作用域、递归 any/all 规则、取反、安全嵌套字段选择器及 contains/equals/regex/exists 操作。
- 新增多作者同步：有界并发生产者、按作者公平轮转队列、流式启动、共享客户端与下载池、部分失败汇总和稳定作者目录。
- 使用 Rich 实时进度、单文件与总下载速度、Rich 感知日志和适用于非 TTY、`NO_COLOR`、`--plain` 的确定性逐行输出替换 tqdm 与手写 ANSI 进度层。
- 在 Actions、任务生成和 CLI 工作流中注入并复用 `PawchiveClient`。
- 通过 Profile 获取作者名，使用 Pawchive 作品列表及直接作品响应结构。
- 从修订列表选择指定版本，不再请求不存在的单修订详情端点。
- 在新模型下保留断点续传、筛选、进度、元数据输出、文件大小限制和可选硬链接存储桶。

## HeroUI WebUI

- 新增可选 React 19、TypeScript、Tailwind CSS v4、HeroUI v3 与 Lucide 管理面板，生产资源会嵌入 wheel 和独立构建。
- 新增 `ktoolbox webui [项目目录]`、主机/端口/浏览器覆盖参数及 `webui hash-password`；未配置账户时使用终端输出的 `admin`/随机密码，并优先使用已配置的 Argon2id 密码哈希。
- WebUI 项目尚无 `ktoolbox.toml` 时给出警告，并以原子写入方式创建最小有效配置。
- 新增登录速率限制、哈希化不透明会话、严格 Cookie、CSRF 与 Origin 校验、安全响应头、脱敏配置快照及持久项目锁。
- 新增双语、响应式深浅色流程，覆盖项目概览、`.env`/`prod.env` 与 TOML 编辑、作者清单、递归忽略规则、Pawchive 作者/作品查询、修订查看、站点版本与任务创建。
- 为 WebUI 中全部基于文件系统的路径字段新增需认证的远程路径选择器，支持项目/主机作用域、面包屑、搜索、隐藏项控制、分页、安全创建目录及手动输入路径。
- 从 Pydantic 元数据及中英文配置 docstring 生成可读双语标签和说明，提供来源标记、秘密遮蔽、类型化与高级编辑、校验、差异预览、ETag 冲突检测和原子写入。
- 新增 WAL SQLite 队列，支持并发调度、资源阻塞与去重、不可变尝试、暂停/恢复/停止/编辑/排序/重跑/删除、重启恢复、SSE 续接、总速度/单文件速度、ETA 和结构化日志。
- 新增基于输出归属的删除预览，跳过符号链接及任何既存、共享或已修改文件。
- 重建 HeroUI 表单基础组件：开关关闭灰、开启蓝，复选框严格按状态显示标记，列表紧凑开关居中，弹窗表面连续，并为任务、作者和忽略规则条目直接展示图标操作。
- 持久化仅用于展示的任务目标快照，使队列离线时仍可按作品标题和作者名识别，且不影响执行、去重或资源锁。
- 统一使用“作品”“平台”“忽略规则”等中文产品术语，并将同步全部作者选项明确为“同步所有已启用作者”。

## 测试与质量

- 使用 RESPX、HTTPX Transport、依赖注入和临时文件系统重建完全离线测试，并阻止意外 Socket。
- 覆盖全部公开操作、参数与响应契约、状态映射、重试路径、非法响应、Schema 漂移报告和客户端生命周期。
- 手写 API 层及 WebUI 认证/配置/调度核心强制 100% 行与分支覆盖率，全项目覆盖率不低于 85%。
- 加入 Vitest/Testing Library 和离线 Playwright 测试，覆盖路由、任务生命周期、桌面/移动布局、深浅主题与 Axe 无障碍检查。
- 新增浏览器几何检查与实拍截图，覆盖单层表格、连续弹窗操作栏、列表开关居中、响应式标签页、可读任务目标及仅在选中时显示的复选框标记。
- 加入 Ruff、Mypy、警告即错误、Python 与 TypeScript OpenAPI 生成一致性检查、Node 24 锁文件构建、wheel/PyInstaller 资源检查、`compileall`、包构建和双语文档严格构建。

## 修复

- 接受 Pawchive 实际返回的时间戳格式，同时保留经过校验的日期时间模型。
- 本地存储桶能力检测改用真实临时路径，并正确清理硬链接探针。
- 存储桶路径移除查询字符串，文件大小筛选去重，并在续传大小校验中计入已有临时字节。

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.24.0...v1.0.0
