import { useMemo } from "react";
import { useApi } from "../api";
import { label, useApp } from "../context";
import { colon, dayKey, dayRange, num, when } from "../format";
import type { Key } from "../i18n";
import { go, href } from "../router";
import type { FlagName, RunsAnswer } from "../types";
import { Constructed, ErrorBox, Flags, Loading, Outcome, Select } from "../ui";

const FILTERS = ["outcome", "flag", "model", "language", "min_cost", "max_cost", "from", "to", "q", "sort", "order", "release"];

export function RunsScreen({ params }: { params: Record<string, string> }) {
  const { t, lang, ds, info } = useApp();
  const query: Record<string, string> = { ds };
  for (const k of FILTERS) if (params[k]) query[k] = params[k];
  const { data, error, loading } = useApi<RunsAnswer>("runs", query);
  const all = useApi<RunsAnswer>("runs", { ds });
  const tz = info.tz_hours;

  const set = (changes: Record<string, string | undefined>) => {
    const next: Record<string, string | undefined> = { ...params, ds, ...changes };
    go("runs", "", next);
  };
  const days = useMemo(() => {
    const keys = new Set<string>();
    for (const r of all.data?.runs ?? []) keys.add(dayKey(r.start, tz));
    return [...keys].sort();
  }, [all.data, tz]);
  const currentDay = (() => {
    if (!params.from || !params.to) return "";
    const key = dayKey(Number(params.from), tz);
    const [a, b] = dayRange(key, tz);
    return Number(params.from) === a && Number(params.to) === b ? key : "";
  })();
  const timeChip = params.from && params.to && !currentDay;

  const facets = all.data?.facets ?? data?.facets;
  const sortHeader = (col: "start" | "cost" | "duration" | "steps", text: string) => {
    const active = (params.sort || "start") === col;
    const desc = params.order === "desc";
    return (
      <th scope="col" aria-sort={active ? (desc ? "descending" : "ascending") : "none"}>
        <button type="button" className="sort" onClick={() => set({ sort: col, order: active && !desc ? "desc" : "asc" })}>
          {text}
          <span className="sr-only"> {t("sort_by", { col: text })}</span>
          <span aria-hidden="true">{active ? (desc ? " ▼" : " ▲") : " ↕"}</span>
        </button>
      </th>
    );
  };

  return (
    <section aria-labelledby="runs-h">
      <h1 id="runs-h">{t("runs_title")}</h1>
      <p className="intro">{t("runs_intro")}</p>
      <form key={JSON.stringify(params)} className="filters" role="search" onSubmit={(e) => e.preventDefault()}>
        <Select id="f-outcome" labelText={t("f_outcome")} value={params.outcome ?? ""} all={t("f_all")}
          onChange={(v) => set({ outcome: v || undefined })}
          options={(facets?.outcomes ?? []).map((o) => ({ value: o, text: label(t, "out_", o) }))} />
        <Select id="f-flag" labelText={t("f_flag")} value={params.flag ?? ""} all={t("f_all")}
          onChange={(v) => set({ flag: v || undefined })}
          options={[{ value: "any", text: t("f_any_flag") }, { value: "none", text: t("f_no_flag") },
            ...info.flags.map((f) => ({ value: f, text: t(`flag_${f}` as Key) }))]} />
        <Select id="f-model" labelText={t("f_model")} value={params.model ?? ""} all={t("f_all")}
          onChange={(v) => set({ model: v || undefined })}
          options={(facets?.models ?? []).map((m) => ({ value: m, text: m }))} />
        <Select id="f-language" labelText={t("f_language")} value={params.language ?? ""} all={t("f_all")}
          onChange={(v) => set({ language: v || undefined })}
          options={(facets?.languages ?? []).map((m) => ({ value: m, text: m }))} />
        <Select id="f-day" labelText={t("f_day")} value={currentDay} all={t("f_all")}
          onChange={(v) => {
            if (!v) return set({ from: undefined, to: undefined });
            const [a, b] = dayRange(v, tz);
            set({ from: String(a), to: String(b) });
          }}
          options={days.map((d) => { const [a] = dayRange(d, tz); return { value: d, text: when(lang, a, tz, "day") }; })} />
        <div className="field">
          <label htmlFor="f-min">{t("f_min_cost")}</label>
          <input id="f-min" type="number" inputMode="decimal" min="0" step="0.0001" defaultValue={params.min_cost ?? ""}
            onBlur={(e) => set({ min_cost: e.target.value || undefined })}
            onKeyDown={(e) => { if (e.key === "Enter") set({ min_cost: (e.target as HTMLInputElement).value || undefined }); }} />
        </div>
        <div className="field">
          <label htmlFor="f-max">{t("f_max_cost")}</label>
          <input id="f-max" type="number" inputMode="decimal" min="0" step="0.0001" defaultValue={params.max_cost ?? ""}
            onBlur={(e) => set({ max_cost: e.target.value || undefined })}
            onKeyDown={(e) => { if (e.key === "Enter") set({ max_cost: (e.target as HTMLInputElement).value || undefined }); }} />
        </div>
        <div className="field">
          <label htmlFor="f-q">{t("f_search")}</label>
          <input id="f-q" type="search" defaultValue={params.q ?? ""} placeholder="T-90104"
            onKeyDown={(e) => { if (e.key === "Enter") set({ q: (e.target as HTMLInputElement).value || undefined }); }}
            onBlur={(e) => set({ q: e.target.value || undefined })} />
        </div>
        <div className="field end">
          <a className="button ghost" href={href("runs", "", { ds })}>{t("f_clear")}</a>
        </div>
      </form>
      {timeChip ? (
        <p className="chips">
          <span className="chip">
            {t("f_time")}{colon(lang)}{when(lang, Number(params.from), tz, "dayhour")} – {when(lang, Number(params.to), tz, "dayhour")}
            <button type="button" onClick={() => set({ from: undefined, to: undefined })} aria-label={t("f_remove")}>×</button>
          </span>
        </p>
      ) : null}
      {error ? <ErrorBox message={error} /> : null}
      {data ? (
        <>
          <div className="summary" aria-live="polite">
            <p>{t("runs_count", { shown: data.shown, total: data.total, flagged: data.flagged })}</p>
            <ul className="badges" aria-label={t("col_flags")}>
              {(Object.entries(data.flag_counts) as [FlagName, number][]).map(([f, n]) => (
                <li key={f}>
                  <a className={`badge flag flag-${f}`} href={href("runs", "", { ...params, ds, flag: f })}>
                    <span aria-hidden="true">⚑ </span>{t(`flag_${f}` as Key)}{colon(lang)}{n}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          {data.runs.length === 0 ? <p>{t("no_runs")}</p> : (
            <div className="table-wrap" tabIndex={0} role="region" aria-label={t("runs_caption")}>
              <table className="runs">
                <caption className="sr-only">{t("runs_caption")}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("col_run")}</th>
                    <th scope="col">{t("col_ticket")}</th>
                    {sortHeader("start", t("col_started"))}
                    <th scope="col">{t("col_outcome")}</th>
                    {sortHeader("steps", t("col_steps"))}
                    <th scope="col" className="num">{t("col_tools")}</th>
                    <th scope="col" className="num">{t("col_approvals")}</th>
                    {sortHeader("cost", t("col_cost"))}
                    {sortHeader("duration", t("col_duration"))}
                    <th scope="col">{t("col_model")}</th>
                    <th scope="col">{t("col_flags")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.runs.map((r) => (
                    <tr key={r.run_id} className={r.flags.length ? "flagged" : undefined}>
                      <th scope="row">
                        <a href={href("run", r.run_id, { ds })}>{r.run_id}</a> {r.constructed ? <Constructed /> : null}
                      </th>
                      <td>{r.ticket}</td>
                      <td className="nowrap">{when(lang, r.start, tz, "dayhour")}</td>
                      <td><Outcome value={r.outcome} /></td>
                      <td className="num">{r.model_calls}</td>
                      <td className="num">{r.tool_calls}</td>
                      <td className="num">{r.approvals}</td>
                      <td className="num">{num(lang, r.cost, 5)}</td>
                      <td className="num">{num(lang, r.duration_s, 1)}</td>
                      <td>{r.model}</td>
                      <td><Flags names={r.flags} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : loading ? <Loading /> : null}
    </section>
  );
}
