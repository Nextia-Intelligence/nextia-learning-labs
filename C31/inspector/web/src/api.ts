// The inspector's API, on the same address as the pages. GET only.

import { useEffect, useState } from "react";

export function apiUrl(path: string, params: Record<string, string | number | undefined | null> = {}): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return `api/${path}${s ? `?${s}` : ""}`;
}

export async function getJson<T>(path: string, params: Record<string, string | number | undefined | null> = {}, signal?: AbortSignal): Promise<T> {
  const resp = await fetch(apiUrl(path, params), { signal, headers: { Accept: "application/json" } });
  const body = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
  if (!resp.ok) throw new Error(body.error || `HTTP ${resp.status}`);
  return body as T;
}

export interface Loaded<T> {
  data: T | null;
  error: string;
  loading: boolean;
}

/** Load one API answer; a new key cancels the request before it. */
export function useApi<T>(path: string | null, params: Record<string, string | number | undefined | null> = {}): Loaded<T> {
  const key = path ? apiUrl(path, params) : "";
  const [state, setState] = useState<Loaded<T>>({ data: null, error: "", loading: Boolean(path) });
  useEffect(() => {
    if (!path) {
      setState({ data: null, error: "", loading: false });
      return;
    }
    const ctrl = new AbortController();
    setState((s) => ({ data: s.data, error: "", loading: true }));
    getJson<T>(path, params, ctrl.signal)
      .then((data) => setState({ data, error: "", loading: false }))
      .catch((e: Error) => {
        if (e.name !== "AbortError") setState({ data: null, error: e.message, loading: false });
      });
    return () => ctrl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state;
}
