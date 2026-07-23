export const mcpClientKeys = ["general", "claude", "cursor", "vscode", "codex"] as const;

export type MCPClientKey = (typeof mcpClientKeys)[number];

const tokenVariable = "${KTOOLBOX_MCP_TOKEN}";

function bearerValue(token?: string): string {
  return `Bearer ${token ?? tokenVariable}`;
}

function genericConfiguration(endpoint: string, token?: string): string {
  return JSON.stringify(
    {
      mcpServers: {
        ktoolbox: {
          type: "http",
          url: endpoint,
          headers: {
            Authorization: bearerValue(token),
          },
        },
      },
    },
    null,
    2,
  );
}

function vscodeConfiguration(endpoint: string): string {
  return JSON.stringify(
    {
      inputs: [
        {
          id: "ktoolbox-token",
          type: "promptString",
          description: "KToolBox MCP token",
          password: true,
        },
      ],
      servers: {
        ktoolbox: {
          type: "http",
          url: endpoint,
          headers: {
            Authorization: "Bearer ${input:ktoolbox-token}",
          },
        },
      },
    },
    null,
    2,
  );
}

function codexConfiguration(endpoint: string): string {
  return [
    "[mcp_servers.ktoolbox]",
    `url = ${JSON.stringify(endpoint)}`,
    'bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"',
  ].join("\n");
}

export function mcpClientConfiguration(client: MCPClientKey, endpoint: string): string {
  if (client === "vscode") return vscodeConfiguration(endpoint);
  if (client === "codex") return codexConfiguration(endpoint);
  return genericConfiguration(endpoint);
}

export function mcpReadyConfiguration(endpoint: string, token: string): string {
  return genericConfiguration(endpoint, token);
}
