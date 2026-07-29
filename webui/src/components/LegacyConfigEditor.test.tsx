import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "../lib/theme";
import { LegacyConfigEditor } from "./LegacyConfigEditor";

describe("LegacyConfigEditor", () => {
  it("binds its label and description to the highlighted editor", () => {
    const { rerender } = render(
      <ThemeProvider>
        <LegacyConfigEditor
          description="Paste legacy variables."
          format="env"
          issues={[]}
          label="Legacy environment settings"
          placeholder="KTOOLBOX_JOB__MIX_POSTS=false"
          value="KTOOLBOX_JOB__MIX_POSTS=true"
          onChange={vi.fn()}
        />
      </ThemeProvider>,
    );

    const editor = screen.getByRole("textbox", {
      name: "Legacy environment settings",
    });
    expect(editor).toHaveAttribute("data-language", "properties");
    expect(editor).toHaveAccessibleDescription("Paste legacy variables.");

    rerender(
      <ThemeProvider>
        <LegacyConfigEditor
          description="Paste a naming section."
          format="toml"
          issues={[]}
          label="Legacy TOML naming settings"
          placeholder="[naming]"
          value={'post_dirname_format = "{title}"'}
          onChange={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(
      screen.getByRole("textbox", { name: "Legacy TOML naming settings" }),
    ).toHaveAttribute("data-language", "toml");
  });

  it("marks parser issues at the reported source line", async () => {
    const { container } = render(
      <ThemeProvider>
        <LegacyConfigEditor
          description="Paste a naming section."
          format="toml"
          issues={[{ line: 2, column: 4, message: "Invalid TOML value" }]}
          label="Legacy TOML naming settings"
          placeholder="[naming]"
          value={"[naming]\ninvalid value"}
          onChange={vi.fn()}
        />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".cm-lintRange-error, .cm-lint-marker-error"),
      ).not.toBeNull();
    });
  });
});
