import { createContext, useContext } from "react";
import { hasKey, translate, type Key, type Lang } from "./i18n";
import type { Info } from "./types";

export interface Ctx {
  lang: Lang;
  info: Info;
  ds: string;
  t: (key: Key, vars?: Record<string, string | number>) => string;
}

export const AppContext = createContext<Ctx | null>(null);

export function useApp(): Ctx {
  const c = useContext(AppContext);
  if (!c) throw new Error("useApp outside the app");
  return c;
}

export function makeT(lang: Lang) {
  return (key: Key, vars?: Record<string, string | number>) => translate(lang, key, vars);
}

/** A label from a data value, if the dictionary has one (outcomes, roles, decisions), else the value. */
export function label(t: Ctx["t"], prefix: "out_" | "role_" | "dec_" | "flag_", value: string): string {
  const k = `${prefix}${value}`;
  return hasKey(k) ? t(k) : value.replace(/_/g, " ");
}
