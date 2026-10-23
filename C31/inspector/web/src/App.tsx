import { useEffect, useMemo, useRef, useState } from "react";
import { useApi } from "./api";
import { AppContext, makeT } from "./context";
import type { Key, Lang } from "./i18n";
import { href, useRoute, type Screen } from "./router";
import type { Info } from "./types";
import { ErrorBox, Loading } from "./ui";
import { AuditScreen } from "./screens/Audit";
import { CompareScreen } from "./screens/Compare";
import { CostScreen } from "./screens/Cost";
import { RunScreen } from "./screens/Run";
import { RunsScreen } from "./screens/Runs";

function stored(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}
function store(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* private window: the choice is not kept */
  }
}

function startLang(): Lang {
  const q = new URLSearchParams(window.location.search).get("lang");
  if (q === "fr" || q === "en") return q;
  const s = stored("inspector.lang");
  if (s === "fr" || s === "en") return s;
  return navigator.language?.toLowerCase().startsWith("fr") ? "fr" : "en";
}

function systemDark(): boolean {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

function startTheme(): "light" | "dark" | "" {
  const q = new URLSearchParams(window.location.search).get("theme");
  if (q === "light" || q === "dark") return q;
  const s = stored("inspector.theme");
  return s === "light" || s === "dark" ? s : "";
}

const NAV: { screen: Screen; key: Key }[] = [
  { screen: "runs", key: "nav_runs" },
  { screen: "run", key: "nav_run" },
  { screen: "audit", key: "nav_audit" },
  { screen: "cost", key: "nav_cost" },
  { screen: "compare", key: "nav_compare" },
];

const DS_KEY: Record<string, Key> = {
  week: "ds_week", "healthy-week": "ds_healthy_week", constructed: "ds_constructed", live: "ds_live", yours: "ds_yours",
};
const HONESTY: Record<string, Key> = {
  week: "honesty_week", "healthy-week": "honesty_healthy_week", constructed: "honesty_constructed",
  live: "honesty_live", yours: "honesty_yours",
};

export function App() {
  const route = useRoute();
  const [lang, setLang] = useState<Lang>(startLang);
  const [theme, setTheme] = useState<"light" | "dark" | "">(startTheme);
  const [sysDark, setSysDark] = useState(systemDark);
  const info = useApi<Info>("info");
  const t = useMemo(() => makeT(lang), [lang]);
  const main = useRef<HTMLElement>(null);
  const [lastRun, setLastRun] = useState<string>("");

  useEffect(() => {
    document.documentElement.lang = lang === "fr" ? "fr-CA" : "en";
    store("inspector.lang", lang);
  }, [lang]);
  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
  }, [theme]);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    const on = () => setSysDark(mq.matches);
    mq?.addEventListener("change", on);
    return () => mq?.removeEventListener("change", on);
  }, []);

  const ds = route.params.ds || info.data?.default || "week";
  const screenTitle = t(NAV.find((n) => n.screen === route.screen)!.key);
  useEffect(() => {
    document.title = `${screenTitle}${route.id ? ` ${route.id}` : ""} · ${t("app_name")}`;
  }, [screenTitle, route.id, t]);
  useEffect(() => {
    if ((route.screen === "run" || route.screen === "audit") && route.id) setLastRun(route.id);
  }, [route.screen, route.id]);

  const dark = theme ? theme === "dark" : sysDark;

  if (!info.data) {
    return <main className="page">{info.error ? <ErrorBox message={info.error} /> : <p role="status">Loading…</p>}</main>;
  }
  const ctx = { lang, info: info.data, ds, t };
  const dataset = info.data.datasets.find((d) => d.id === ds);

  const switchDs = (next: string) => {
    setLastRun("");
    window.location.hash = href(route.screen, "", { ds: next });
  };

  return (
    <AppContext.Provider value={ctx}>
      <a className="skip" href="#main" onClick={(e) => { e.preventDefault(); main.current?.focus(); }}>
        {t("skip")}
      </a>
      <header className="top">
        <div className="brand">
          <svg aria-hidden="true" width="28" height="28" viewBox="0 0 16 16">
            <rect width="16" height="16" rx="3" fill="var(--accent)" />
            <path d="M3 5h10M3 8h6M3 11h8" stroke="var(--on-accent)" strokeWidth="1.6" />
          </svg>
          <div>
            <p className="brand-name">{t("app_name")}</p>
            <p className="brand-sub">{t("app_sub")}</p>
          </div>
        </div>
        <nav aria-label={t("nav_label")} className="nav">
          <ul>
            {NAV.map((n) => {
              const id = n.screen === "run" || n.screen === "audit" ? lastRun : "";
              return (
                <li key={n.screen}>
                  <a href={href(n.screen, id, { ds })} aria-current={route.screen === n.screen ? "page" : undefined}>
                    {t(n.key)}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="controls">
          <div className="field inline">
            <label htmlFor="ds">{t("dataset")}</label>
            <select id="ds" value={ds} onChange={(e) => switchDs(e.target.value)}>
              {info.data.datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {DS_KEY[d.id] ? t(DS_KEY[d.id]) : d.id}
                </option>
              ))}
            </select>
          </div>
          <div className="seg" role="group" aria-label={t("language")}>
            {(["en", "fr"] as Lang[]).map((l) => (
              <button key={l} type="button" aria-pressed={lang === l} lang={l === "fr" ? "fr-CA" : "en"} onClick={() => setLang(l)}>
                {l === "en" ? "EN" : "FR"}
                <span className="sr-only">{l === "en" ? " English" : " français"}</span>
              </button>
            ))}
          </div>
          <button type="button" className="theme" aria-pressed={dark} onClick={() => {
            const next = dark ? "light" : "dark";
            setTheme(next);
            store("inspector.theme", next);
          }}>
            <span aria-hidden="true">{dark ? "☾" : "☀"} </span>
            {t("theme_dark")}
          </button>
        </div>
      </header>
      <div className={`honesty ${ds}`} role="note">
        {t(HONESTY[ds] ?? "honesty_yours")}
        {dataset?.error ? <span className="danger-text"> {t("live_error", { error: dataset.error })}</span> : null}
      </div>
      <main id="main" ref={main} tabIndex={-1} className="page">
        {route.screen === "runs" && <RunsScreen params={route.params} />}
        {route.screen === "run" && <RunScreen key={`${ds}-${route.id}`} id={route.id} />}
        {route.screen === "audit" && <AuditScreen key={`${ds}-${route.id}`} id={route.id} />}
        {route.screen === "cost" && <CostScreen params={route.params} />}
        {route.screen === "compare" && <CompareScreen params={route.params} />}
      </main>
      <footer className="foot">
        <p>
          {t("footer")} · v{info.data.version}
        </p>
      </footer>
      {info.loading ? <Loading /> : null}
    </AppContext.Provider>
  );
}
