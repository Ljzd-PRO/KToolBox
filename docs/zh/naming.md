# 命名格式

KToolBox v1 的命名设置属于当前项目。CLI 与 WebUI 共同读取 `ktoolbox.toml` 中的 `[naming]`；命名字段不再作为全局 dotenv 配置编辑。

## 设置目录结构

在 WebUI 打开**命名格式**，可以设置：

- 一个或多个下载根目录；
- 作者、作品、修订、年份和月份目录模板；
- 主文件与附件文件模板；
- 作品内部的附件、修订、正文和外链名称；
- 年月分组、混合作品和附件顺序命名。

模板只能使用字段旁列出的变量 Chip，例如 `{creator_name}`、`{creator_id}`、`{service}`、`{title}`、`{post_id}`、`{revision_id}`、`{year}` 和 `{month}`。路径分隔符、父目录跳转、未知变量和不安全名称会在扫描前被拒绝。

![深色主题下的命名模板](../assets/webui/34-naming-templates-desktop-dark.png)

## 预览已下载内容

点击**扫描并预览**后，KToolBox 会扫描真实下载根目录，不依赖任务历史，也不会访问 Pawchive。它通过作者目录身份、`creator-indices.ktoolbox` 与 `post.json` 识别内容，并拒绝跟随越出根目录的符号链接。

预览会显示每位作者的新旧路径、作品数、文件数、总大小、跳过项和冲突。**转换已下载作者**默认开启；所有可安全转换的作者默认选中，也可逐项取消。

![移动端命名转换预览](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox 不会覆盖或合并目标目录。扫描结果过期、配置变化、相关任务处于活动状态、目标重复或文件系统变化时，都必须重新扫描。

## 应用与恢复

启用转换时，KToolBox 会先保存待生效配置快照，再以后台转换作业移动文件。只有全部选定操作成功后，新命名格式才会生效。取消、写入失败或进程中断会按相反顺序回滚已完成移动，并继续使用旧配置。

转换进度和历史保存在 `.ktoolbox/webui.sqlite3`。成功后会清理临时操作日志，完成记录会保留到用户手动删除。转换会删除已空的旧来源目录，但不会删除无关文件。

关闭转换时只保存新格式；旧下载保持原位，之后的 CLI 与 WebUI 下载使用新的项目格式。

## 首次启动迁移

首次启动 WebUI 时，KToolBox 会在创建默认项目配置之前迁移 `.env` 和 `prod.env` 中的旧命名键：

1. 将最终生效值写入 `ktoolbox.toml`；
2. 备份到 `.ktoolbox/migrations/project-naming-v2/`；
3. 删除旧 dotenv 键；
4. 在终端输出摘要；
5. 登录后显示一次性 WebUI 通知。

![一次性命名迁移通知](../assets/webui/36-naming-migration-notice-light.png)

CLI 同样使用项目命名设置。旧项目尚未完成迁移时，请启动一次该项目的 WebUI，以完成带备份的原子迁移。
