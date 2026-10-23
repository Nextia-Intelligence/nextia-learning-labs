// Hash routes: #/runs?ds=week&flag=loop, #/run/R-1014-040, #/audit/R-1014-040, #/cost, #/compare?a=..&b=..

import { useEffect, useState } from "react";

export type Screen = "runs" | "run" | "audit" | "cost" | "compare";
export const SCREENS: Screen[] = ["runs", "run", "audit", "cost", "compare"];

export interface Route {
  screen: Screen;
  id: string;
  params: Record<string, string>;
}

export function parseHash(hash: string): Route {
  const raw = hash.replace(/^#\/?/, "");
  const [path, query = ""] = raw.split("?");
  const [first = "", ...rest] = path.split("/");
  const screen = (SCREENS as string[]).includes(first) ? (first as Screen) : "runs";
  const params: Record<string, string> = {};
  new URLSearchParams(query).forEach((v, k) => {
    if (v !== "") params[k] = v;
  });
  return { screen, id: decodeURIComponent(rest.join("/")), params };
}

export function href(screen: Screen, id = "", params: Record<string, string | number | undefined | null> = {}): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return `#/${screen}${id ? `/${encodeURIComponent(id)}` : ""}${s ? `?${s}` : ""}`;
}

export function go(screen: Screen, id = "", params: Record<string, string | number | undefined | null> = {}): void {
  window.location.hash = href(screen, id, params);
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const on = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}
