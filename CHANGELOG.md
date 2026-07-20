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
- Replace tqdm and the handwritten ANSI progress layer with Rich live progress, Rich-aware logging, and deterministic plain output for non-TTY, `NO_COLOR`, and `--plain` environments.
- Inject and reuse `PawchiveClient` throughout actions, task generation, and CLI workflows.
- Resolve creator names through profile requests and use the Pawchive post-list and direct post response shapes.
- Select a requested revision from the revision list instead of calling a nonexistent detail endpoint.
- Retain resumable downloads, filters, progress reporting, metadata output, file-size limits, and optional hard-link bucket storage under the new models.

## Testing and quality

- Replace the test suite with 154 fully offline tests using RESPX, HTTPX transports, dependency injection, and temporary filesystems; accidental sockets are blocked.
- Cover every public operation, parameter and response contract, status mapping, retry path, malformed response, schema drift report, and client lifecycle.
- Enforce 100% line and branch coverage for the handwritten API layer and at least 85% for the full project.
- Add Ruff, strict API-layer Mypy, warnings-as-errors, OpenAPI validation, generation checks, `compileall`, package builds, and strict bilingual documentation builds.

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
- 明确排除受 `cookieAuth` 保护的 5 个账号收藏操作；公开投稿标记仍然实现。
- 新增严格的 Pydantic 请求约束和生成的 Pydantic v2 响应模型，覆盖全部文档字段与已确认字段，同时保留未知字段。
- 新增传输、HTTP、认证、未找到、冲突和响应校验类型化异常。
- 只重试传输错误、`429` 和 `5xx`；不跟随重定向，也不重试普通 `4xx` 与校验失败。
- 保留 Pawchive 原始 Schema，以可审查覆盖修正规范，校验规范化 OpenAPI，并在 CI 中验证模型生成结果确定一致。

## 核心与 CLI

- 使用 Cyclopts 命令、直接 Rich 帮助、Shell 补全、常规连字符选项、机器可读输出和明确的 `0`/`1`/`2`/`130` 退出码替换 Python Fire。
- 为 7 个 v0 命令名新增隐藏兼容别名，每次调用提示一次弃用。
- 新增项目级 `ktoolbox.toml`，包含可启停作者清单、别名、保留注释的原子写入、路径发现、校验和 Urwid 编辑支持。
- 新增可扩展异步投稿屏蔽器，支持有序全局/作者作用域、递归 any/all 规则、取反、安全嵌套字段选择器及 contains/equals/regex/exists 操作。
- 新增多作者同步：有界并发生产者、按作者公平轮转队列、流式启动、共享客户端与下载池、部分失败汇总和稳定作者目录。
- 使用 Rich 实时进度、Rich 感知日志和适用于非 TTY、`NO_COLOR`、`--plain` 的确定性逐行输出替换 tqdm 与手写 ANSI 进度层。
- 在 Actions、任务生成和 CLI 工作流中注入并复用 `PawchiveClient`。
- 通过 Profile 获取作者名，使用 Pawchive 投稿列表及直接投稿响应结构。
- 从修订列表选择指定版本，不再请求不存在的单修订详情端点。
- 在新模型下保留断点续传、筛选、进度、元数据输出、文件大小限制和可选硬链接存储桶。

## 测试与质量

- 使用 RESPX、HTTPX Transport、依赖注入和临时文件系统重建 154 项完全离线测试，并阻止意外 Socket。
- 覆盖全部公开操作、参数与响应契约、状态映射、重试路径、非法响应、Schema 漂移报告和客户端生命周期。
- 手写 API 层强制 100% 行与分支覆盖率，全项目覆盖率不低于 85%。
- 加入 Ruff、API 层严格 Mypy、警告即错误、OpenAPI 校验、生成一致性检查、`compileall`、包构建和双语文档严格构建。

## 修复

- 接受 Pawchive 实际返回的时间戳格式，同时保留经过校验的日期时间模型。
- 本地存储桶能力检测改用真实临时路径，并正确清理硬链接探针。
- 存储桶路径移除查询字符串，文件大小筛选去重，并在续传大小校验中计入已有临时字节。

**Full Changelog**: https://github.com/Ljzd-PRO/KToolBox/compare/v0.24.0...v1.0.0
