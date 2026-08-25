# WebUI

WebUI 是使用 KToolBox 的推荐方式。它在浏览器界面中集中管理一个同步项目的设置、任务、进度和历史。

## 首次运行

安装 WebUI 版本，创建项目目录并启动 KToolBox：

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

浏览器会自动打开。使用终端中显示的 `admin` 用户名和随机密码登录。缺少 `ktoolbox.toml` 时 KToolBox 会自动创建；新任务默认使用项目中的 `downloads` 目录。

![KToolBox WebUI 概览](../assets/webui/40-overview-showcase-desktop-light.png)

## 第一次同步

1. 打开“作者”，选择“添加作者”。
2. 粘贴 Pawchive 作者 URL，或填写平台与 ID。
3. 打开“任务”，选择“创建任务”，再选择“同步作者”。
4. 首次检查新作者和命名格式时，建议先设置较小的作品数量限制。
5. 打开任务详情，查看下载、速度、重试和有用的活动日志。

已经完成的文件会被保留；兼容的临时文件可继续下载；单个作者失败也不会删除同一任务中其他作者已成功下载的内容。

## 按目标继续阅读

<div class="grid cards" markdown>

-   :material-folder-account-outline: **作者、作品、忽略规则和命名**

    日常项目管理请阅读[项目工作流](webui/project-workflows.md)。

-   :material-progress-download: **进度和任务控制**

    暂停、停止、重新运行、错误诊断和安全清理见[任务与实时更新](webui/tasks.md)。

-   :material-server-security: **账号与部署**

    只有需要固定凭据、远程访问、备份或详细安全机制时，才需要阅读[部署参考](webui/reference.md)。

-   :material-update: **现有 v0 项目**

    转换旧设置或下载前，请先阅读[迁移指南](migration-v1.md)。

</div>

## 可选的固定账号

首次运行使用自动生成的凭据即可。如需在重启后保持相同账号，请生成密码哈希：

```bash
ktoolbox webui hash-password
```

将结果写入项目 `.env`：

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## 安全访问

内置服务使用 HTTP。仅在本机使用时，请绑定到 `127.0.0.1`：

```bash
ktoolbox webui . --host 127.0.0.1
```

远程访问请使用可信网络或 HTTPS 反向代理。能够登录的用户可以查看项目路径、配置和任务日志，请勿向不可信用户开放。同一项目一次只能由一个 WebUI 进程管理。
