import { useState } from "react";
import { useApi } from "../api";
import { label, useApp } from "../context";
import { money, num, pct, when } from "../format";
import { go, href } from "../router";
import type { CostAnswer, CostBucket, CostGroup } from "../types";
import { ErrorBox, Loading, Outcome, Select, Stat } from "../ui";

const W = 960;
const H = 300;
const PAD = { l: 72, r: 16, t: 48, b: 40 };

/** A round step for about 5 grid lines, and the top of the axis. */
function niceScale(x: number): { step: number; max: number } {
  const raw = Math.max(x, 1e-6) / 5;
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = ([1, 2, 5, 10].find((m) => m * p >= raw) ?? 10) * p;
  return { step, max: Math.ceil(x / step) * step };
}

function Chart({ data, onPick }: { data: CostAnswer; onPick: (b: CostBucket) => void }) {
  const { t, lang } = useApp();
  const [hover, setHover] = useState<CostBucket | null>(null);
  const tz = data.tz_hours;
  const s = data.series;
  const budget = data.budget_per_resolved;
  const { step, max } = niceScale(Math.max(budget * 1.2, ...s.map((b) => b.per_resolved ?? 0)));
  const iw = W - PAD.l - PAD.r;
  const ih = H - PAD.t - PAD.b;
  const bw = iw / Math.max(s.length, 1);
  const y = (v: number) => PAD.t + ih - (v / max) * ih;
  const x0 = s.length ? s[0].start : 0;
  const x1 = s.length ? s[s.length - 1].end : 1;
  const xOf = (ms: number) => PAD.l + ((ms - x0) / (x1 - x0)) * iw;
  const ticks = Array.from({ length: Math.round(max / step) + 1 }, (_, i) => i * step);
  const fmtBucket = (b: CostBucket) => when(lang, b.start, tz, data.bucket === "hour" ? "dayhour" : "day");
  const barLabel = (b: CostBucket) => b.per_resolved === null
    ? t("bar_empty", { when: fmtBucket(b), runs: b.runs })
    : t("bar_label", { when: fmtBucket(b), value: money(lang, b.per_resolved), runs: b.runs, resolved: b.resolved });
  const every = data.bucket === "hour" ? 24 : 1;

  return (
    <figure className="chart">
      <p className="legend">
        <svg width="34" height="10" aria-hidden="true"><line x1="0" x2="34" y1="5" y2="5" className="budget" /></svg>
        <span className="budget-text">{t("budget", { budget: num(lang, budget, 3) })}</span>
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t("chart_label", { bucket: t(data.bucket === "hour" ? "per_hour" : "per_day").toLowerCase() })}>
        {ticks.map((v) => (
          <g key={v} aria-hidden="true">
            <line x1={PAD.l} x2={W - PAD.r} y1={y(v)} y2={y(v)} className="grid" />
            <text x={PAD.l - 8} y={y(v) + 4} textAnchor="end" className="axis">{num(lang, v, 3)}</text>
          </g>
        ))}
        {data.releases.slice(1).map((r) => (
          <g key={r.release} aria-hidden="true">
            <line x1={xOf(r.first_run)} x2={xOf(r.first_run)} y1={14} y2={PAD.t + ih} className="release" />
            <text x={xOf(r.first_run) + 4} y={14} className="axis release-label">{t("release_mark", { release: r.release })}</text>
          </g>
        ))}
        {s.map((b, i) => {
          const v = b.per_resolved ?? 0;
          const h = Math.max(ih - (y(v) - PAD.t), v > 0 ? 2 : 0);
          const gap = Math.min(2, bw * 0.2);
          const over = v > budget;
          return (
            <a key={b.start} href={href("runs", "", { ds: data.dataset, from: b.start, to: b.end })}
              aria-label={barLabel(b)}
              onClick={(e) => { e.preventDefault(); onPick(b); }}
              onMouseEnter={() => setHover(b)} onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(b)} onBlur={() => setHover(null)}
              className="barlink">
              <rect x={PAD.l + i * bw} y={PAD.t} width={bw} height={ih} className="hit" />
              <path className={`cbar${over ? " over" : ""}${hover === b ? " hot" : ""}`}
                d={h > 0 ? roundedTop(PAD.l + i * bw + gap / 2, y(v), bw - gap, h, Math.min(4, (bw - gap) / 2)) : ""} />
              {data.bucket === "day" && b.per_resolved !== null ? (
                <text x={PAD.l + i * bw + bw / 2} y={y(v) - 6} textAnchor="middle" className="value" aria-hidden="true">{num(lang, v, 4)}</text>
              ) : null}
              {i % every === 0 ? (
                <text x={PAD.l + i * bw + (every === 1 ? bw / 2 : 2)} y={H - PAD.b + 18} textAnchor={every === 1 ? "middle" : "start"} className="axis" aria-hidden="true">
                  {when(lang, b.start, tz, "day")}
                </text>
              ) : null}
            </a>
          );
        })}
        <line x1={PAD.l} x2={W - PAD.r} y1={y(budget)} y2={y(budget)} className="budget" aria-hidden="true" />
        <line x1={PAD.l} x2={W - PAD.r} y1={PAD.t + ih} y2={PAD.t + ih} className="baseline" aria-hidden="true" />
      </svg>
      <figcaption>
        <p className="hover-readout" aria-hidden="true">{hover ? barLabel(hover) : " "}</p>
      </figcaption>
    </figure>
  );
}

function roundedTop(x: number, y: number, w: number, h: number, r: number): string {
  const rr = Math.min(r, h);
  return `M${x},${y + h} V${y + rr} Q${x},${y} ${x + rr},${y} H${x + w - rr} Q${x + w},${y} ${x + w},${y + rr} V${y + h} Z`;
}

function GroupTable({ title, rows, kind }: { title: string; rows: (CostGroup & { key: string })[]; kind: string }) {
  const { t, lang } = useApp();
  return (
    <div className="table-wrap" tabIndex={0} role="region" aria-label={title}>
      <table className="compact">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th scope="col">{t("col_key")}</th>
            <th scope="col" className="num">{t("col_runs")}</th>
            <th scope="col" className="num">{t("col_resolved")}</th>
            <th scope="col" className="num">{t("col_cost")}</th>
            <th scope="col" className="num">{t("col_per_run")}</th>
            <th scope="col" className="num">{t("col_per_resolved")}</th>
            <th scope="col" className="num">{t("col_success")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <th scope="row">{kind === "outcome" ? <Outcome value={r.key} /> : r.key || "–"}</th>
              <td className="num">{r.runs}</td>
              <td className="num">{r.resolved}</td>
              <td className="num">{num(lang, r.cost, 4)}</td>
              <td className="num">{num(lang, r.per_run, 5)}</td>
              <td className="num">{r.per_resolved === null ? "–" : num(lang, r.per_resolved, 5)}</td>
              <td className="num">{pct(lang, r.success)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CostScreen({ params }: { params: Record<string, string> }) {
  const { t, lang, ds, info } = useApp();
  const q = { ds, bucket: params.bucket, model: params.model, language: params.language, outcome: params.outcome };
  const { data, error, loading } = useApi<CostAnswer>("cost", q);
  const facets = useApi<CostAnswer>("cost", { ds });
  const set = (c: Record<string, string | undefined>) => go("cost", "", { ...params, ds, ...c });
  const pickBar = (b: CostBucket) => go("runs", "", { ds, from: b.start, to: b.end, model: params.model, language: params.language, outcome: params.outcome });
  const total = data?.total;
  const budget = info.budget_per_resolved;
  const ratio = total?.per_resolved ? total.per_resolved / budget : null;
  const prom = data?.prometheus;
  const promTotal = prom?.series?.reduce((acc, s) => acc + s.points.reduce((a, p) => a + p[1], 0), 0);

  return (
    <section aria-labelledby="cost-h">
      <h1 id="cost-h">{t("cost_title")}</h1>
      <p className="intro">{t("cost_intro")}</p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <div className="seg" role="group" aria-label={t("bucket")}>
          {(["day", "hour"] as const).map((b) => (
            <button key={b} type="button" aria-pressed={(params.bucket || "day") === b} onClick={() => set({ bucket: b === "day" ? undefined : b })}>
              {t(b === "day" ? "per_day" : "per_hour")}
            </button>
          ))}
        </div>
        <Select id="c-model" labelText={t("f_model")} value={params.model ?? ""} all={t("f_all")} onChange={(v) => set({ model: v || undefined })}
          options={(facets.data?.groups.model ?? []).map((g) => ({ value: g.key, text: g.key }))} />
        <Select id="c-lang" labelText={t("f_language")} value={params.language ?? ""} all={t("f_all")} onChange={(v) => set({ language: v || undefined })}
          options={(facets.data?.groups.language ?? []).map((g) => ({ value: g.key, text: g.key }))} />
        <Select id="c-out" labelText={t("f_outcome")} value={params.outcome ?? ""} all={t("f_all")} onChange={(v) => set({ outcome: v || undefined })}
          options={(facets.data?.groups.outcome ?? []).map((g) => ({ value: g.key, text: label(t, "out_", g.key) }))} />
      </form>
      {error ? <ErrorBox message={error} /> : null}
      {!data ? (loading ? <Loading /> : null) : (
        <>
          <p className="muted small">{t("prices_from", { dates: data.price_tables.map((p) => p.date).join(", ") || t("none") })}</p>
          <dl className="stats">
            <Stat name={t("total_cost")}>{money(lang, data.total.cost, 4)}</Stat>
            <Stat name={t("total_runs")}>{data.total.runs}</Stat>
            <Stat name={t("total_resolved")}>{data.total.resolved}</Stat>
            <Stat name={t("total_per_resolved")}>
              {money(lang, data.total.per_resolved)}{" "}
              {ratio !== null ? <span className={ratio > 1 ? "danger-text" : "ok-text"}>({ratio > 1 ? t("over_budget", { x: num(lang, ratio, 1) }) : t("under_budget")})</span> : null}
            </Stat>
          </dl>
          <Chart data={data} onPick={pickBar} />
          <details className="table-view">
            <summary>{t("chart_label", { bucket: t(data.bucket === "hour" ? "per_hour" : "per_day").toLowerCase() })}</summary>
            <div className="table-wrap" tabIndex={0} role="region" aria-label={t("chart_label", { bucket: "" })}>
              <table className="compact">
                <thead>
                  <tr>
                    <th scope="col">{t("bucket")}</th>
                    <th scope="col" className="num">{t("col_runs")}</th>
                    <th scope="col" className="num">{t("col_resolved")}</th>
                    <th scope="col" className="num">{t("col_cost")}</th>
                    <th scope="col" className="num">{t("col_per_resolved")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.series.filter((b) => b.runs).map((b) => (
                    <tr key={b.start}>
                      <th scope="row"><a href={href("runs", "", { ds, from: b.start, to: b.end })}>{when(lang, b.start, data.tz_hours, data.bucket === "hour" ? "dayhour" : "day")}</a></th>
                      <td className="num">{b.runs}</td>
                      <td className="num">{b.resolved}</td>
                      <td className="num">{num(lang, b.cost, 4)}</td>
                      <td className="num">{b.per_resolved === null ? "–" : num(lang, b.per_resolved, 5)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <div className="grid2">
            <GroupTable title={t("by_model")} rows={data.groups.model} kind="model" />
            <GroupTable title={t("by_language")} rows={data.groups.language} kind="language" />
            <GroupTable title={t("by_outcome")} rows={data.groups.outcome} kind="outcome" />
            <GroupTable title={t("by_release")} rows={data.groups.release} kind="release" />
          </div>
          <h2>{t("top_runs")}</h2>
          <div className="table-wrap" tabIndex={0} role="region" aria-label={t("top_runs")}>
            <table className="compact">
              <thead>
                <tr>
                  <th scope="col">{t("col_run")}</th>
                  <th scope="col">{t("col_ticket")}</th>
                  <th scope="col">{t("col_started")}</th>
                  <th scope="col">{t("col_model")}</th>
                  <th scope="col">{t("col_outcome")}</th>
                  <th scope="col" className="num">{t("col_steps")}</th>
                  <th scope="col" className="num">{t("col_tokens")}</th>
                  <th scope="col" className="num">{t("col_cost")}</th>
                </tr>
              </thead>
              <tbody>
                {data.top.map((r) => (
                  <tr key={r.run_id}>
                    <th scope="row"><a href={href("run", r.run_id, { ds })}>{r.run_id}</a></th>
                    <td>{r.ticket}</td>
                    <td className="nowrap">{when(lang, r.start, data.tz_hours, "dayhour")}</td>
                    <td>{r.model}</td>
                    <td><Outcome value={r.outcome} /></td>
                    <td className="num">{r.model_calls}</td>
                    <td className="num">{num(lang, r.tokens_in)} / {num(lang, r.tokens_out)}</td>
                    <td className="num">{num(lang, r.cost, 5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h2>{t("by_step")}</h2>
          <div className="table-wrap" tabIndex={0} role="region" aria-label={t("by_step")}>
            <table className="compact">
              <thead>
                <tr>
                  <th scope="col">{t("col_model")}</th>
                  <th scope="col" className="num">{t("col_step_n")}</th>
                  <th scope="col" className="num">{t("col_calls")}</th>
                  <th scope="col" className="num">{t("col_tokens")}</th>
                  <th scope="col" className="num">{t("col_cost")}</th>
                </tr>
              </thead>
              <tbody>
                {data.steps.map((s) => (
                  <tr key={`${s.model}-${s.step}`}>
                    <th scope="row">{s.model}</th>
                    <td className="num">{s.step}</td>
                    <td className="num">{s.calls}</td>
                    <td className="num">{num(lang, s.tokens_in)} / {num(lang, s.tokens_out)}</td>
                    <td className="num">{num(lang, s.cost, 4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {prom ? (
            <section aria-labelledby="prom-h">
              <h2 id="prom-h">{t("prom_head")}</h2>
              {prom.available ? <p>{t("prom_total", { query: prom.query, total: money(lang, promTotal ?? 0, 4) })}</p> : <p>{t("prom_none", { error: prom.error ?? "" })}</p>}
            </section>
          ) : null}
        </>
      )}
    </section>
  );
}
