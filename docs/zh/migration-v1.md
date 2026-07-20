# 迁移至 v1

KToolBox v1 对后端和 Python 库 API 都进行了不兼容升级。

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

新的默认值为：

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

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

