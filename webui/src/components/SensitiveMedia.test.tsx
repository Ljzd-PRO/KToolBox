import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SENSITIVE_MEDIA_STORAGE_KEY, SensitiveMediaProvider } from "../lib/sensitiveMedia";
import type { MediaAsset } from "../types";
import { CreatorAvatar, CreatorBanner } from "./SensitiveMedia";

const asset: MediaAsset = {
  kind: "avatar",
  thumbnail_url: "/api/v1/media/avatar?variant=thumbnail",
  preview_url: "/api/v1/media/avatar?variant=preview",
  original_url: "/api/v1/media/avatar?variant=original",
};

afterEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.nsfw;
});

function renderMedia() {
  return render(
    <SensitiveMediaProvider>
      <CreatorAvatar asset={asset} name="Demo Studio" />
      <CreatorBanner asset={{ ...asset, kind: "banner" }} name="Demo Studio" />
    </SensitiveMediaProvider>,
  );
}

describe("sensitive creator media", () => {
  it("does not mount image elements or placeholders while disabled", () => {
    renderMedia();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByTestId("creator-avatar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("creator-banner")).not.toBeInTheDocument();
  });

  it("uses stable media frames and falls back to the creator initial", () => {
    localStorage.setItem(SENSITIVE_MEDIA_STORAGE_KEY, "true");
    renderMedia();
    const images = screen.getAllByRole("img");
    expect(images).toHaveLength(2);
    expect(screen.getByTestId("creator-avatar")).toHaveTextContent("D");
    fireEvent.error(images[0]);
    expect(screen.getByTestId("creator-avatar")).toHaveTextContent("D");
    expect(screen.getAllByRole("img")).toHaveLength(1);
  });
});
