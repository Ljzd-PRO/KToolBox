# MCP

KToolBox starts a Streamable HTTP MCP server in the same process and on the same port as the WebUI. It exposes a curated set of project, task, creator, ignore-rule, Pawchive search, naming, automatic-sync, and safe configuration tools. Browser sessions and MCP clients use separate credentials.

| Service | Default address |
| --- | --- |
| WebUI | `http://127.0.0.1:8789/` |
| MCP | `http://127.0.0.1:8789/mcp` |
| WebUI REST OpenAPI | `http://127.0.0.1:8789/api/v1/openapi.yaml` |

The OpenAPI download requires an authenticated WebUI session. The committed canonical contract is `webui/openapi.yaml`.

## Create an access token

1. Start the WebUI and sign in.
2. Open **MCP** in the sidebar.
3. Select **New access token**.
4. Enter a descriptive name and confirm the current WebUI password.
5. Choose **Read only** or **Manage**, then choose 7, 30, 90, or 365 days, or no expiration.
6. Store the displayed `ktmcp_...` value immediately. It is shown only once.

KToolBox stores only a token hash. The MCP page lists creation, expiration, and last-use times and can revoke a token immediately. A non-expiring token remains valid until revoked and should be used only when its lifecycle is actively managed.

## Connect Codex

Store the token outside the repository:

```shell
export KTOOLBOX_MCP_TOKEN="ktmcp_..."
```

Add the server to the Codex configuration:

```toml
[mcp_servers.ktoolbox]
url = "http://127.0.0.1:8789/mcp"
bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"
```

The MCP page also generates ready-to-copy configurations for generic HTTP clients, Claude, Cursor, VS Code, and Codex. Templates use an environment variable or protected input instead of embedding a token.

## Permissions and limits

- A read-only token can inspect project summaries, tasks, creators, ignore rules, automatic-sync state, naming history, redacted configuration, and bounded project files.
- A management token can also perform the explicitly listed task, creator, ignore-rule, automatic-sync, and safe structured-configuration changes.
- Login, logout, browser sessions, raw dotenv/TOML editing, secrets, arbitrary host filesystem access, output deletion, and unbounded logs or content are not exposed.
- Search and Pawchive lookup tools are open-world operations and can contact the configured Pawchive service.
- Tool lists, logs, events, work content, and files are bounded or paginated.

The **MCP** page is the authoritative catalog for the tools available in the running version.

## Security

Bearer tokens grant direct project access. Keep them out of Git, shell history, screenshots, logs, and chat messages. Use a separate token per client and revoke unused credentials.

The built-in server uses HTTP. For a client on the same computer, bind WebUI to `127.0.0.1`. For remote access, terminate HTTPS at a trusted reverse proxy and restrict network access. Never send a bearer token over an untrusted plaintext network.

## API boundaries

KToolBox documents four different interfaces:

- the Pawchive OpenAPI contract describes the upstream public service;
- the [Python API](api.md) provides the typed `PawchiveClient`;
- `webui/openapi.yaml` describes the authenticated KToolBox WebUI REST API;
- `/mcp` exposes the curated MCP tools generated from that WebUI contract.

The WebUI REST contract and MCP surface are not replacements for the upstream Pawchive API.
