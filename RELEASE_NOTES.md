# KToolBox v1.1.0-beta.1

> [!WARNING]
> This is a prerelease for testing the first post-v1 migration fixes. Back up configuration and existing downloads, start with a bounded task, and review naming-conversion previews before moving files.

KToolBox v1.1.0-beta.1 concentrates on two real upgrade problems reported after v1.0.0: legacy attachments stored directly in work directories and timezone-less Pawchive publication timestamps. It also hardens cross-platform packaging and makes the documentation lead with the WebUI workflow.

中文说明在前，后附 English summary。

## 本次重点

### Service 发布时间时区

- 修复 [#390](https://github.com/Ljzd-PRO/KToolBox/issues/390)：Pawchive Fanbox 的无时区 `published` 现在先按 `Asia/Tokyo` 解释，再转换到项目目标时区。
- Patreon 默认使用 `UTC`；未知或自定义 Service 使用可配置的回退时区，也可逐 Service 指定任意有效 IANA 时区。
- 目录与文件命名、年月分组、手动日期筛选、自动同步回退时间、CLI、WebUI 和 MCP 使用同一套有效发布时间。
- Pawchive 原始 `published` 仍原样保存在 `post.json`，不会修改上游元数据。
- 新建项目会根据主机系统时区，把 `KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE` 明文写入 `.env`。已有项目不会在启动或读取配置时被自动改写，未设置时继续使用 `UTC` 默认值。
- WebUI 顶栏显示当前目标时区；全局配置页可以修改目标、回退和各 Service 时区。
- 命名布局快照会冻结对应的时间策略。只有时区变化确实影响 `{published}` 或年月目录时，才会提示旧目录转换。

Fanbox 跨日示例：

```text
Pawchive 原值：2025-12-21T00:35:43
Service 时区：Asia/Tokyo
UTC 结果：    2025-12-20T15:35:43+00:00
```

### 旧版根目录附件

- 修复 [#389](https://github.com/Ljzd-PRO/KToolBox/issues/389)：项目命名、粘贴旧 `.env`/TOML 和 v0 迁移重新支持 `attachments = "."` 或 `ATTACHMENTS=./`。
- 旧下载转换器可逐个识别并移动作品根目录中的附件与修订附件，同时保留封面、元数据和无关文件。
- 源布局与目标布局分别计算顺序文件名，避免 `1.png`、`2.png` 等编号相互污染。
- 暂停、继续、取消回滚和父目录改名后的操作日志均会重新验证，目标冲突或不安全路径不会被覆盖。
- WebUI 目录树会把根目录附件显示在封面旁，并展示最终顺序命名结果。

### 发布与兼容性

- README 与文档现在优先引导用户使用功能完整的 WebUI，并保留更精简的 CLI 与 Python API 入口。
- 修复 Windows 下 `/attachments` 可能被误判为相对路径的问题；POSIX 与 Windows 根路径现在在所有系统上保持一致校验。
- Python 支持范围修正为 `>=3.10,<3.15`，覆盖完整 Python 3.10 至 3.14 系列，并锁定提供 `cp314` wheel 的 `windows-curses 2.4.2`，使 Windows Python 3.14 可安装可选终端界面。
- tag 发布流程提供 wheel、sdist、Windows x64/x86、macOS arm64/x64、Linux x64/arm64 和 `SHA256SUMS`。

## 从 v1.0.0 测试升级

1. 备份 `.env`、`prod.env`、`ktoolbox.toml` 和已有下载目录。
2. 安装 beta，并先使用一位作者、一个作品或较小的输出目录验证。
3. 打开 WebUI 的“全局配置”，确认“发布时间”中的目标时区符合预期。
4. 如果命名模板包含 `{published}` 或启用了年月分组，先查看“命名格式”页面生成的转换预览，再决定是否移动旧文件。
5. 使用 `ATTACHMENTS=./` 的旧项目可通过迁移向导或可复用的旧下载目录转换器转换；粘贴内容只用于推断源布局，不会覆盖当前项目配置。

若现有项目希望使用本地时区，可明确设置：

```dotenv
KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=Asia/Shanghai
KTOOLBOX_PUBLISHED_TIME__FALLBACK_SERVICE_TIMEZONE=UTC
KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__FANBOX=Asia/Tokyo
KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__PATREON=UTC
```

## 安装 beta

PyPI 会把 SemVer beta 规范化为 PEP 440 的 `1.1.0b1`：

```bash
pipx install --force 'ktoolbox[webui]==1.1.0b1'
```

也可以从本 Release 下载适合系统架构的独立压缩包，并使用 `SHA256SUMS` 验证完整性。

## 已知风险

- 这是预发布版本，主要用于验证 v1.0.0 之后的迁移和时区修复，不建议在没有备份的唯一下载目录上首次试用。
- 更改目标时区可能改变跨日作品的目录与文件名。KToolBox 不会自动移动旧内容，任何转换都必须先预览并明确确认。
- Pawchive 仍可能返回 OpenAPI 未描述的数据形态。请提交经过脱敏的错误阶段、Service、作者 ID 和字段路径，不要包含 Cookie、令牌、作品正文或完整下载地址。

## 下载与校验

| 产物 | 用途 |
| --- | --- |
| `ktoolbox-1.1.0b1-py3-none-any.whl` | Python wheel |
| `ktoolbox-1.1.0b1.tar.gz` | Python 源码包 |
| `ktoolbox-Windows-x64-v1.1.0-beta.1.zip` | Windows 64 位独立程序 |
| `ktoolbox-Windows-x86-v1.1.0-beta.1.zip` | Windows 32 位独立程序 |
| `ktoolbox-macOS-arm64-v1.1.0-beta.1.zip` | Apple Silicon 独立程序 |
| `ktoolbox-macOS-x64-v1.1.0-beta.1.zip` | Intel macOS 独立程序 |
| `ktoolbox-Linux-x64-v1.1.0-beta.1.zip` | Linux x64 独立程序 |
| `ktoolbox-Linux-arm64-v1.1.0-beta.1.zip` | Linux ARM64 独立程序 |
| `SHA256SUMS` | 全部发布文件的 SHA-256 校验值 |

完整记录见 [CHANGELOG.md](https://github.com/Ljzd-PRO/KToolBox/blob/v1.1.0-beta.1/CHANGELOG.md) 和 [v1.0.0...v1.1.0-beta.1](https://github.com/Ljzd-PRO/KToolBox/compare/v1.0.0...v1.1.0-beta.1)。

---

## English summary

KToolBox v1.1.0-beta.1 is a prerelease focused on migration correctness after v1.0.0.

### Highlights

- Fix [#390](https://github.com/Ljzd-PRO/KToolBox/issues/390) by interpreting timezone-less Pawchive publication timestamps in a configurable Service timezone before converting them to the project's target timezone. Fanbox defaults to `Asia/Tokyo`, Patreon to `UTC`.
- Use the same effective publication instant for naming, year/month grouping, manual filtering, automatic-sync fallback windows, CLI, WebUI, and MCP while preserving raw Pawchive metadata.
- Persist the detected IANA target timezone only when creating a new project. Existing projects are never rewritten merely by loading configuration or starting WebUI.
- Show the effective target timezone in the WebUI app bar and edit target, fallback, and per-Service zones in Global Configuration.
- Fix [#389](https://github.com/Ljzd-PRO/KToolBox/issues/389) by restoring `.` / `./` attachment layouts and safely converting flat legacy attachments with independent source and target sequence numbering.
- Harden paused conversion journals, conflict checks, cross-platform rooted-path validation, and old-layout previews.
- Correct Python metadata to support the complete Python 3.10 through 3.14 range and lock `windows-curses 2.4.2` with Windows CPython 3.14 wheels.
- Make WebUI the primary getting-started path in the multilingual documentation.

### Upgrade checklist

1. Back up environment files, `ktoolbox.toml`, and downloaded directories.
2. Install `ktoolbox[webui]==1.1.0b1` and begin with a bounded task.
3. Verify the publication target timezone in Global Configuration.
4. If naming uses `{published}` or year/month grouping, inspect the generated conversion preview before moving old content.
5. Use the guided migration or reusable converter for legacy `ATTACHMENTS=./` layouts.

This is a beta. Please report sanitized failures through [GitHub Issues](https://github.com/Ljzd-PRO/KToolBox/issues) and do not include cookies, downloader sessions, MCP tokens, post content, or private absolute paths.
