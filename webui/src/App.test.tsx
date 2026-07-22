import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import i18n from "./lib/i18n";

afterEach(async () => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  await i18n.changeLanguage("en");
});

describe("App", () => {
  it("shows the real sign-in screen when no session exists", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "not authenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Sign in to this project" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Use dark theme" }));
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    await user.click(screen.getByRole("button", { name: "Switch language" }));
    await user.click(screen.getByRole("menuitemradio", { name: /简体中文/ }));
    expect(await screen.findByRole("heading", { name: "登录此同步项目" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/session", expect.objectContaining({ credentials: "same-origin" }));
  });

  it("uses a stable disabled busy state during login", async () => {
    let resolveLogin: (response: Response) => void = () => undefined;
    const loginResponse = new Promise<Response>((resolve) => {
      resolveLogin = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, options?: RequestInit) => {
        if (options?.method === "POST") return loginResponse;
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "not authenticated" }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );
    await user.type(await screen.findByLabelText("Username"), "owner");
    await user.type(screen.getByLabelText("Password", { exact: true }), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    const pending = screen.getByRole("button", { name: "Signing in" });
    expect(pending).toBeDisabled();
    expect(pending.closest("form")).toHaveAttribute("aria-busy", "true");
    resolveLogin(
      new Response(JSON.stringify({ detail: "invalid credentials" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    expect(await screen.findByRole("button", { name: "Sign in" })).toBeEnabled();
  });
});
