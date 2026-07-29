# MCP

KToolBox 会在 WebUI 的同一进程、同一端口启动 Streamable HTTP MCP 服务。它提供经过筛选的项目、任务、作者、忽略规则、Pawchive 搜索、命名格式、自动同步和安全配置工具。浏览器会话与 MCP 客户端使用不同的凭据。

| 服务 | 默认地址 |
| --- | --- |
| WebUI | `http://127.0.0.1:8789/` |
| MCP | `http://127.0.0.1:8789/mcp` |
| WebUI REST OpenAPI | `http://127.0.0.1:8789/api/v1/openapi.yaml` |

下载 OpenAPI 需要已登录的 WebUI 会话；仓库中的正式契约为 `webui/openapi.yaml`。

## 创建访问令牌

1. 启动 WebUI 并登录。
2. 打开侧栏中的 **MCP**。
3. 选择“新建访问令牌”。
4. 填写易识别的名称，并再次输入当前 WebUI 密码。
5. 选择“只读”或“管理”，再选择 7、30、90、365 天或永不过期。
6. 立即保存页面显示的 `ktmcp_...`；明文只显示一次。

KToolBox 只保存令牌哈希。MCP 页面会显示创建时间、有效期和最后使用时间，并可立即撤销令牌。永不过期令牌会持续有效直至撤销，只应在能够主动管理其生命周期时使用。

## 连接 Codex

将令牌保存在仓库之外：

```shell
export KTOOLBOX_MCP_TOKEN="ktmcp_..."
```

在 Codex 配置中添加：

```toml
[mcp_servers.ktoolbox]
url = "http://127.0.0.1:8789/mcp"
bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"
```

MCP 页面还会生成通用 HTTP、Claude、Cursor、VS Code 和 Codex 配置。模板使用环境变量或受保护输入，不会直接嵌入令牌。

## 权限与限制

- 只读令牌可查看项目摘要、任务、作者、忽略规则、自动同步状态、命名历史、脱敏配置和有界的项目文件。
- 管理令牌还可执行工具目录中明确列出的任务、作者、忽略规则、自动同步和安全结构化配置修改。
- 登录、退出、浏览器会话、dotenv/TOML 原文编辑、秘密值、任意主机文件系统、删除输出以及无上限日志或正文均不开放。
- 搜索和 Pawchive 查询属于开放世界操作，可能访问配置的 Pawchive 服务。
- 工具列表、日志、事件、作品正文和文件均设置上限或分页。

运行版本实际开放的工具以 **MCP** 页面中的目录为准。

## 安全

Bearer 令牌可直接访问项目。不要将其提交到 Git，也不要放入 Shell 历史、截图、日志或聊天消息。建议每个客户端使用独立令牌，并及时撤销不再使用的凭据。

内置服务器使用 HTTP。同一台计算机上的客户端应将 WebUI 绑定到 `127.0.0.1`。远程访问时应在可信反向代理终止 HTTPS，并限制网络访问。切勿通过不可信的明文网络传输令牌。

## API 边界

KToolBox 包含四种不同接口：

- Pawchive OpenAPI 描述上游公开服务；
- [Python API](api.md) 提供类型化 `PawchiveClient`；
- `webui/openapi.yaml` 描述需认证的 KToolBox WebUI REST API；
- `/mcp` 提供从 WebUI 契约中筛选生成的 MCP 工具。

WebUI REST 契约和 MCP 都不能代替上游 Pawchive API。
