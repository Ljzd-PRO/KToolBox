# 关于 Pawchive

[Pawchive](https://pawchive.pw/) 是 KToolBox v1 唯一正式支持的后端。KToolBox 使用其公开 API 查询创作者与投稿，再从 Pawchive 的独立文件主机下载文件。

## 默认端点

| 用途 | 默认值 |
| --- | --- |
| 公开 API | `https://pawchive.pw/api/v1` |
| 创作者头像与横幅 | `https://pawchive.pw` |
| 投稿文件 | `https://file.pawchive.pw/data/...` |

API 请求永远不会携带账号会话。配置 `downloader.session_key` 后，它只会作为 `session` Cookie 发送给文件下载请求。

## 已支持的 API 范围

KToolBox 实现了 OpenAPI 文档中全部 14 个不需要 `cookieAuth` 的操作：创作者与投稿列表、Profile、公告、Fancard、关联创作者、投稿详情、文件哈希搜索、投稿标记状态与提交、修订、评论和应用版本。

另外 5 个账号收藏操作需要登录 Pawchive，因此明确不实现。

## 合理使用

请遵守适用法律、平台条款与创作者权益。首次同步某位创作者时，建议使用 `--length` 限制投稿数量，并配置文件大小上限。

