import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { SENSITIVE_MEDIA_STORAGE_KEY, SensitiveMediaProvider } from "../lib/sensitiveMedia";
import type { MediaAsset } from "../types";
import { CreatorAvatar, CreatorBanner, MediaGallery, MediaViewer } from "./SensitiveMedia";

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

const galleryAssets = Array.from({ length: 14 }, (_, index): MediaAsset => ({
  kind: index === 0 ? "cover" : "attachment",
  thumbnail_url: `/api/v1/media/files/${index}?variant=thumbnail`,
  preview_url: `/api/v1/media/files/${index}?variant=preview`,
  original_url: `/api/v1/media/files/${index}?variant=original`,
}));

function GalleryHarness() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  return (
    <SensitiveMediaProvider>
      <MediaGallery assets={galleryAssets} title="Fixture work" onOpen={setActiveIndex} />
      <MediaViewer
        assets={galleryAssets}
        index={activeIndex ?? 0}
        open={activeIndex !== null}
        title="Fixture work"
        onClose={() => setActiveIndex(null)}
        onIndexChange={setActiveIndex}
      />
    </SensitiveMediaProvider>
  );
}

describe("sensitive work media", () => {
  it("does not mount the gallery while disabled", () => {
    render(<GalleryHarness />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /media gallery/i })).not.toBeInTheDocument();
  });

  it("paginates thumbnails and supports keyboard viewer navigation", () => {
    localStorage.setItem(SENSITIVE_MEDIA_STORAGE_KEY, "true");
    render(<GalleryHarness />);
    expect(screen.getAllByRole("img")).toHaveLength(12);
    fireEvent.click(screen.getByRole("button", { name: "Show 12 more" }));
    expect(screen.getAllByRole("img")).toHaveLength(14);

    fireEvent.click(screen.getByRole("button", { name: "Media preview 1" }));
    expect(screen.getByText("Image 1 of 14")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "ArrowRight" });
    expect(screen.getByText("Image 2 of 14")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("Image 2 of 14")).not.toBeInTheDocument();
  });
});
