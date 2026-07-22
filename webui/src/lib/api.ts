export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: unknown,
    message?: string,
  ) {
    super(message || detailText(detail, `Request failed (HTTP ${status})`));
    this.name = "ApiError";
  }
}

export type ApiOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  csrfToken?: string;
};

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.csrfToken) headers.set("X-CSRF-Token", options.csrfToken);
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: "same-origin",
    headers,
  });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    let message = response.statusText || `Request failed (HTTP ${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown; message?: unknown };
      detail = body.detail ?? body;
      message = detailText(body.message, detailText(detail, message));
    } catch {
      // Preserve the HTTP status text when a proxy returns a non-JSON body.
    }
    throw new ApiError(response.status, detail, message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const MESSAGE_KEYS = ["message", "detail", "error", "reason", "title"] as const;
const LOCATION_PREFIXES = new Set(["body", "cookie", "header", "path", "query"]);

export function detailText(detail: unknown, fallback = "Request failed"): string {
  const messages = [...new Set(detailMessages(detail))];
  return messages.length ? messages.join("; ") : fallback;
}

export function errorText(error: unknown): string {
  if (error instanceof Error && error.message.trim()) return error.message;
  return detailText(error);
}

function detailMessages(detail: unknown): string[] {
  if (typeof detail === "string") {
    const text = detail.trim();
    return text ? [text] : [];
  }
  if (Array.isArray(detail)) return detail.flatMap(detailMessages);
  if (!isRecord(detail)) return [];

  const validationMessage = validationIssueText(detail);
  if (validationMessage) return [validationMessage];
  for (const key of MESSAGE_KEYS) {
    if (key in detail) {
      const messages = detailMessages(detail[key]);
      if (messages.length) return messages;
    }
  }
  return "errors" in detail ? detailMessages(detail.errors) : [];
}

function validationIssueText(issue: Record<string, unknown>): string | null {
  if (typeof issue.msg !== "string" || !issue.msg.trim()) return null;
  const location = Array.isArray(issue.loc)
    ? issue.loc
        .map(String)
        .filter((part, index) => index > 0 || !LOCATION_PREFIXES.has(part))
        .map((part) => part.replaceAll("_", " "))
        .join(".")
    : "";
  return location ? `${location}: ${issue.msg.trim()}` : issue.msg.trim();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
