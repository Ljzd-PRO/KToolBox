export const TIME_ZONE_SUGGESTIONS = [
  "UTC",
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Asia/Seoul",
  "Europe/Paris",
  "Europe/Moscow",
  "America/New_York",
  "America/Los_Angeles",
] as const;

const ambiguousAbbreviations = new Set(["AST", "BST", "CST", "IST", "MST"]);

export function systemTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export function timeZoneOptions(value?: string) {
  return [...new Set([value, systemTimeZone(), ...TIME_ZONE_SUGGESTIONS])]
    .filter((item): item is string => Boolean(item))
    .map((item) => ({ value: item, label: item }));
}

export function timeZoneOffsetMinutes(timeZone: string, instant = new Date()): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(instant);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const represented = Date.UTC(
    Number(values.year),
    Number(values.month) - 1,
    Number(values.day),
    Number(values.hour),
    Number(values.minute),
    Number(values.second),
  );
  return Math.round((represented - instant.getTime()) / 60_000);
}

export function formatUtcOffset(minutes: number, includeMinutes = true): string {
  if (minutes === 0) return "UTC";
  const sign = minutes < 0 ? "-" : "+";
  const absolute = Math.abs(minutes);
  const hours = Math.floor(absolute / 60);
  const remainder = absolute % 60;
  if (!includeMinutes && remainder === 0) return `UTC${sign}${String(hours).padStart(2, "0")}`;
  return `UTC${sign}${String(hours).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

export function timeZonePresentation(timeZone: string, instant = new Date()) {
  try {
    const offsetMinutes = timeZoneOffsetMinutes(timeZone, instant);
    if (timeZone === "UTC" || timeZone === "Etc/UTC") {
      return { abbreviation: "UTC", offset: "UTC" };
    }
    const abbreviation = new Intl.DateTimeFormat("en-US", {
      timeZone,
      timeZoneName: "short",
    }).formatToParts(instant).find((part) => part.type === "timeZoneName")?.value;
    const safeAbbreviation = abbreviation
      && /^[A-Z]{2,5}$/.test(abbreviation)
      && !ambiguousAbbreviations.has(abbreviation)
      ? abbreviation
      : formatUtcOffset(offsetMinutes, false);
    return { abbreviation: safeAbbreviation, offset: formatUtcOffset(offsetMinutes) };
  } catch {
    return { abbreviation: "UTC", offset: "UTC" };
  }
}
