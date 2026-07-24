export interface PawchiveCreatorIdentity {
  service: string;
  creatorId: string;
}

export function parsePawchiveCreatorUrl(value: string): PawchiveCreatorIdentity | null {
  try {
    const url = new URL(value.trim());
    if (!["http:", "https:"].includes(url.protocol)) return null;
    const parts = url.pathname
      .split("/")
      .filter(Boolean)
      .map((part) => decodeURIComponent(part).trim());
    if (parts.length < 3 || parts[1] !== "user" || !parts[0] || !parts[2]) return null;
    return { service: parts[0], creatorId: parts[2] };
  } catch {
    return null;
  }
}
