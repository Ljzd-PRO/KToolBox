import { describe, expect, it } from "vitest";

import { mcpClientConfiguration, mcpReadyConfiguration } from "./mcp";

describe("MCP client configurations", () => {
  const endpoint = "http://127.0.0.1:8789/mcp";

  it("keeps reusable examples free of literal access tokens", () => {
    for (const client of ["general", "claude", "cursor", "vscode", "codex"] as const) {
      const configuration = mcpClientConfiguration(client, endpoint);
      expect(configuration).toContain(endpoint);
      expect(configuration).not.toContain("ktmcp_");
    }
    expect(mcpClientConfiguration("general", endpoint)).toContain("${KTOOLBOX_MCP_TOKEN}");
    expect(mcpClientConfiguration("vscode", endpoint)).toContain("${input:ktoolbox-token}");
    expect(mcpClientConfiguration("codex", endpoint)).toContain('bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"');
  });

  it("only places the one-time token in the explicit ready configuration", () => {
    const configuration = mcpReadyConfiguration(endpoint, "ktmcp_once");
    expect(configuration).toContain("Bearer ktmcp_once");
  });
});
