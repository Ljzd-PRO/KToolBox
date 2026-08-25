# 迁移至 v1

KToolBox v1 对后端和 Python 库 API 都进行了不兼容升级。

## 推荐迁移流程

1. 备份旧配置和下载目录。
2. 在现有项目目录中安装并启动 [WebUI](webui.md)。
3. 在迁移弹窗中逐项检查检测到的旧设置，再确认任何修改。
4. 预览目录转换，然后先执行一次小范围同步，再启用定时计划或完整归档。

WebUI 会创建备份、检查冲突，并将配置迁移与可选的目录转换分开处理。下方详细表格主要供脚本和 Python 集成参考。

## 升级前

1. 备份 `.env` 或 `prod.env`。
2. 等待当前 v0 下载结束，或先取消任务。
3. 完整同步前，先使用 `--length=1` 做一次受限测试。

## 必须修改的项目

| v0 行为 | v1 行为 |
| --- | --- |
| Kemono/Coomer 端点 | 仅支持 Pawchive |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| API 与文件主机混在 API 配置中 | API/静态主机属于 `api`，文件主机属于 `downloader` |
| 请求单个修订详情 | 先获取修订列表，再按 `revision_id` 选择 |
| `.data.post` 等包装响应 | 直接返回类型化的 `Post`、`Revision` 等 Pydantic 模型 |
| Python Fire 命令面 | Cyclopts 命令树、连字符选项和明确退出码 |
| 每次只能同步一位作者 | 任意数量目标或已启用项目清单 |
| 仅全局 `keywords_exclude` | 有序的全局与作者级 `field-match` 忽略规则 |

新的默认值为：

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## CLI 命令

隐藏别名会暂时保持旧自动化可运行，但每次调用都会提示弃用：

| v0 命令 | v1 命令 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

选项现在显示为 `--creator-id`，不再显示 Python 下划线形式。兼容别名仍接受旧下划线拼写。帮助直接打印，不再需要退出分页器。

CLI 失败改用进程状态：`0` 成功，`1` 远程/作者/下载失败，`2` 参数/配置失败，`130` 中断。JSON 与表格写入 stdout，进度与日志写入 stderr。

## 项目设置、作者清单与忽略规则

`ktoolbox.toml` 现在统一保存项目默认下载目录、命名格式、自动同步计划、可复用作者清单和结构化忽略规则。文件缺失时 CLI 仍可使用内置默认值启动；WebUI 会在警告后创建最小项目文件。

```toml
schema_version = 5
default_output = "downloads"

[naming]
sequential_filename = true

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

相对输出路径以项目目录为基准解析。移动既有下载前请先阅读[命名格式](naming.md)，并在确认作者清单和输出位置后再配置[自动同步](automatic-sync.md)。

请将非空 `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 迁移为全局 `field-match` 标题条件。旧设置仍会作为隐式忽略规则生效并发出警告，但 KToolBox 不会改写本地文件。详见[配置指南](configuration/guide.md#post-blockers)。

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` 默认 `4`，限制作者生产者；现有 `KTOOLBOX_JOB__COUNT` 继续限制文件工作器。

## 使用 WebUI 迁移

v1 新增全新的 HeroUI 面板，不会迁移或复用历史实验性 `webui` 分支。请安装 `ktoolbox[webui]` 并选择项目目录；缺少 `ktoolbox.toml` 时会在警告后自动创建。未配置账户时，每次启动都会在终端输出 `admin` 用户名和新随机密码；需要固定凭据时再配置单账户即可。

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env` 与 `prod.env` 现在是被忽略的本地文件，不再作为受版本控制示例。请在其中保存凭据和下载会话，以 `example.env` 作为公开模板；升级前应检查曾经被跟踪的 dotenv 文件。WebUI 会创建 `.ktoolbox/webui.sqlite3` 与项目锁，但不会改变 CLI 下载输出格式。

命名模板和默认输出位置现归属于项目 Schema v5；旧下载位置不再属于命名配置，只供转换工具使用。检测到旧命名键时，WebUI 启动阶段只警告；登录后由用户逐字段检查差异并明确确认带备份的原子迁移，之后才会修改文件。目录扫描仍是独立的显式步骤。详见[命名格式指南](naming.md)。

HTTP 部署风险和持久任务语义详见 [WebUI 指南](webui.md)。

## Python 库 API

旧 `BaseAPI`、类调用器、模块级 `get_*` 函数、`APIRet` 和 Kemono 响应包装已直接删除，不提供兼容别名。请改用实例化的异步客户端：

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

成功调用返回 Pydantic v2 模型；失败会抛出类型化的 `PawchiveError` 子类。详见 [API 文档](api.md)。
