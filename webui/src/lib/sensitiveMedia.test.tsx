import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import {
  SENSITIVE_MEDIA_STORAGE_KEY,
  SensitiveMediaProvider,
  useSensitiveMedia,
} from "./sensitiveMedia";

function Harness() {
  const media = useSensitiveMedia();
  return (
    <div>
      <span>{media.enabled ? "enabled" : "disabled"}</span>
      <button type="button" onClick={() => media.requestChange(true)}>request</button>
      <button type="button" onClick={media.disable}>disable</button>
    </div>
  );
}

afterEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.nsfw;
});

describe("SensitiveMediaProvider", () => {
  it("starts disabled and requires confirmation before persisting", async () => {
    const user = userEvent.setup();
    render(<SensitiveMediaProvider><Harness /></SensitiveMediaProvider>);

    expect(screen.getByText("disabled")).toBeInTheDocument();
    expect(localStorage.getItem(SENSITIVE_MEDIA_STORAGE_KEY)).toBeNull();
    await user.click(screen.getByRole("button", { name: "request" }));
    expect(screen.getByRole("heading", { name: "Enable NSFW media previews?" })).toBeInTheDocument();
    expect(localStorage.getItem(SENSITIVE_MEDIA_STORAGE_KEY)).toBeNull();

    await user.click(screen.getByRole("button", { name: "Enable NSFW mode" }));
    expect(screen.getByText("enabled")).toBeInTheDocument();
    expect(localStorage.getItem(SENSITIVE_MEDIA_STORAGE_KEY)).toBe("true");
    expect(document.documentElement).toHaveAttribute("data-nsfw", "enabled");

    await user.click(screen.getByRole("button", { name: "disable" }));
    expect(screen.getByText("disabled")).toBeInTheDocument();
    expect(localStorage.getItem(SENSITIVE_MEDIA_STORAGE_KEY)).toBe("false");
  });

  it("restores and synchronizes the browser-local preference", () => {
    localStorage.setItem(SENSITIVE_MEDIA_STORAGE_KEY, "true");
    render(<SensitiveMediaProvider><Harness /></SensitiveMediaProvider>);
    expect(screen.getByText("enabled")).toBeInTheDocument();

    act(() => {
      window.dispatchEvent(new StorageEvent("storage", {
        key: SENSITIVE_MEDIA_STORAGE_KEY,
        newValue: "false",
        storageArea: localStorage,
      }));
    });
    expect(screen.getByText("disabled")).toBeInTheDocument();
  });
});
