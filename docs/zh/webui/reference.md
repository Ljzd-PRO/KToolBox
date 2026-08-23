# WebUI 部署参考

完成首次安全设置后，请通过本参考维护、备份和检查 WebUI 实例。

## 关于

关于页集中展示包版本、许可证和运行环境，并提供文档、源代码与问题反馈入口。URL、IP 和监听地址统一使用行内代码样式；外部链接在新标签页安全打开。

![深色窄屏关于页](../../assets/webui/32-about-mobile-dark.png)

## WebUI 环境变量参考

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | 监听接口。 |
| `KTOOLBOX_WEBUI__PORT` | `8789` | 监听端口，范围 1–65535。 |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | 启动后打开本机 URL。 |
| `KTOOLBOX_WEBUI__USERNAME` | 空 → 启动时为 `admin` | 可选的单账户用户名。 |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | 空 | 推荐的固定 Argon2id 哈希。 |
| `KTOOLBOX_WEBUI__PASSWORD` | 空 → 每次启动随机生成 | 明文后备值；存在哈希时忽略。 |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | 顶层并发任务数，范围 1–16。 |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | 距最后一次使用的会话期限。 |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | 距登录时间的会话最长期限。 |

任务历史需要备份时，请一起备份 `ktoolbox.toml`、本地 dotenv 文件与 `.ktoolbox/webui.sqlite3`；不要在 WebUI 运行期间复制数据库。

## 多语言浏览器验收

七种语言目录均在桌面端与移动端接受深浅主题实测。以下为通过验收的代表性界面；用户内容与文件系统路径始终保持原文。

![法语移动端配置页](../../assets/webui/24-configuration-mobile-fr.png)

![俄语移动端远程路径选择器](../../assets/webui/25-path-picker-mobile-ru.png)

## 相关 WebUI 指南

- [安装与安全概览](../webui.md)
- [项目工作流](project-workflows.md)
- [任务与实时更新](tasks.md)
- [部署参考](reference.md)
