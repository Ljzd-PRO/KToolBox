import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the HeroUI workspace marker", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "KToolBox WebUI" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });
});
