// Numbers, money and times in the two languages. Times are shown in Larkfield's time (Toronto,
// a fixed offset from the API, as the course's obs tool does), not in the browser's time zone.

import type { Lang } from "./i18n";

const locale = (lang: Lang) => (lang === "fr" ? "fr-CA" : "en-CA");

export function money(lang: Lang, x: number | null | undefined, digits = 5): string {
  if (x === null || x === undefined) return "–";
  const n = new Intl.NumberFormat(locale(lang), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(x);
  return lang === "fr" ? `${n} $ US` : `US$${n}`;
}

export function num(lang: Lang, x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined) return "–";
  return new Intl.NumberFormat(locale(lang), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(x);
}

export function pct(lang: Lang, x: number | null | undefined): string {
  if (x === null || x === undefined) return "–";
  return new Intl.NumberFormat(locale(lang), { style: "percent", maximumFractionDigits: 1 }).format(x);
}

function shifted(ms: number, tzHours: number): Date {
  return new Date(ms + tzHours * 3600_000);
}

export function when(lang: Lang, ms: number, tzHours: number, parts: "day" | "dayhour" | "full" | "time" = "full"): string {
  const opts: Intl.DateTimeFormatOptions = { timeZone: "UTC" };
  if (parts !== "time") Object.assign(opts, { weekday: "short", day: "numeric", month: "short" });
  if (parts === "dayhour" || parts === "full" || parts === "time") Object.assign(opts, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  if (parts === "full" || parts === "time") opts.second = "2-digit";
  return new Intl.DateTimeFormat(locale(lang), opts).format(shifted(ms, tzHours));
}

/** A waiting time: "15 h 25 min" or "4 min 05 s" (the same words in both languages). */
export function waiting(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "–";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return h ? `${h} h ${String(m).padStart(2, "0")} min` : `${m} min ${String(s).padStart(2, "0")} s`;
}

export function short(id: string, n = 8): string {
  return id.length > n ? `${id.slice(0, n)}…` : id;
}

/** Day key (YYYY-MM-DD in Toronto time) of a time, for the Day filter. */
export function dayKey(ms: number, tzHours: number): string {
  return shifted(ms, tzHours).toISOString().slice(0, 10);
}

/** Start and end (ms) of the Toronto day of a day key. */
export function dayRange(key: string, tzHours: number): [number, number] {
  const start = Date.parse(`${key}T00:00:00Z`) - tzHours * 3600_000;
  return [start, start + 86_400_000];
}

/** ": " in English, " : " (with a no-break space) in French. */
export function colon(lang: Lang): string {
  return lang === "fr" ? "\u00a0: " : ": ";
}
