# 欢迎使用 KToolBox

KToolBox 用于从 Pawchive 下载公开作品。推荐使用 WebUI：常用操作都有引导式表单，离开页面后仍可查看任务进度。

!!! warning "全新大版本"
    v1 尚未经过足够广泛的实际验证，部分功能仍可能出错。迁移前请备份原有配置和下载；遇到异常时欢迎反馈。

## 从 WebUI 开始

1. 安装 WebUI 版本。
2. 为同步项目创建一个目录。
3. 在该目录中启动 KToolBox。

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

浏览器会自动打开。使用终端中显示的 `admin` 用户名和随机密码登录，添加作者，然后创建第一个任务。需要时 KToolBox 会自动创建 `ktoolbox.toml`，并默认下载到 `downloads` 目录。

![KToolBox WebUI 概览](../assets/webui/40-overview-showcase-desktop-light.png)

## 选择下一步

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **添加作者并下载**

    根据[项目工作流](webui/project-workflows.md)添加作者、搜索作品、创建任务和调整忽略规则。

-   :material-progress-download: **查看任务进度**

    在[任务与实时更新](webui/tasks.md)中了解进度、重试、暂停、停止、重新运行和安全清理。

-   :material-calendar-sync-outline: **定时运行**

    根据[自动同步指南](automatic-sync.md)创建周期计划。

-   :material-folder-cog-outline: **设置名称和目录**

    使用[命名格式指南](naming.md)设置默认输出和易读的目录结构。

</div>

## 进阶入口

普通用户首次运行不需要阅读以下页面。

| 目标 | 指南 |
| --- | --- |
| 固定登录账号或部署到其他设备 | [WebUI 部署参考](webui/reference.md) |
| 在终端中自动化 | [命令行指南](commands/guide.md)与[命令参考](commands/reference.md) |
| 查看全部设置 | [配置指南](configuration/guide.md)与[配置参考](configuration/reference.md) |
| 连接 AI 客户端或 Python 程序 | [MCP](mcp.md) 与 [Python API](api.md) |
| 升级旧项目或解决问题 | [迁移指南](migration-v1.md)与[常见问题](faq.md) |

## 安全默认值

WebUI 默认生成登录凭据、关闭敏感媒体预览，并使用项目内的输出目录。仅本机使用时请绑定 `127.0.0.1`；不可信网络应使用 HTTPS。KToolBox 不实现 Pawchive 账号或收藏操作。
