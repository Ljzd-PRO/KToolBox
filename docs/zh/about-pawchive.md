# 关于 Pawchive

[Pawchive](https://pawchive.pw/) 是 KToolBox v1 唯一正式支持的后端。KToolBox 使用其公开 API 查询创作者与作品，再从 Pawchive 的独立文件主机下载文件。

## 默认端点

| 用途 | 默认值 |
| --- | --- |
| 公开 API | `https://pawchive.pw/api/v1` |
| 创作者头像与横幅 | `https://pawchive.pw` |
| 作品文件 | `https://file.pawchive.pw/data/...` |

API 请求不会携带账号会话。配置 `downloader.session_key` 后，只在下载普通文件时将其作为 `session` Cookie 发送。

KToolBox 会自动使用作品详情中的链接下载仍可用的临时文件，无需修改文件主机或路径前缀。临时下载直连 Pawchive，不使用已配置的下载反向代理、会话 Cookie 或断点续传。文件过期时，任务会报告该文件并继续处理其他文件。

## 已支持的 API 范围

KToolBox 实现了 OpenAPI 文档中全部 14 个不需要 `cookieAuth` 的操作：创作者与作品列表、Profile、公告、Fancard、关联创作者、作品详情、文件哈希搜索、作品标记状态与提交、修订、评论和应用版本。

另外 5 个账号收藏操作需要登录 Pawchive，因此明确不实现。

## 合理使用

请遵守适用法律、平台条款与创作者权益。首次同步某位创作者时，建议使用 `--length` 限制作品数量，并配置文件大小上限。

## 相关指南

- 返回[快速开始](index.md)，完成一次有边界的首次下载。
- 继续阅读[命令指南](commands/guide.md)，下载作品或同步作者。
- 直接集成 `PawchiveClient` 时，请参阅 [Python API 参考](api.md)。
