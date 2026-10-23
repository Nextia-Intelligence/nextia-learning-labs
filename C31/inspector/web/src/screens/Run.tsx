import { Fragment, useEffect, useState } from "react";
import { useApi } from "../api";
import { label, useApp } from "../context";
import { colon, money, num, waiting, when } from "../format";
import type { Key } from "../i18n";
import { go, href } from "../router";
import type { RunDetail, RunsAnswer, SpanView } from "../types";
import { Constructed, ErrorBox, FlagBadge, Loading, Outcome, Stat } from "../ui";

/** The run to open when the Run screen has no run: the double refund if it is there, else the first flagged run. */
export function useDefaultRun(id: string, screen: "run" | "audit") {
  const { ds } = useApp();
  const list = useApi<RunsAnswer>(id ? null : "runs", { ds });
  useEffect(() => {
    if (id || !list.data) return;
    const runs = list.data.runs;
    const pick = runs.find((r) => r.run_id === "R-1014-040") ?? runs.find((r) => r.flags.length) ?? runs[0];
    if (pick) go(screen, pick.run_id, { ds });
  }, [id, list.data, ds, screen]);
  return list;
}

function result(s: SpanView, t: ReturnType<typeof useApp>["t"], lang: "en" | "fr"): string {
  const a = s.attrs;
  const bits: string[] = [];
  if (s.kind === "model") {
    const req = (a["larkfield.model.requested"] as string[] | undefined) ?? [];
    if (req.length) bits.push(req.join(", "));
    const fin = a["gen_ai.response.finish_reasons"] as string[] | undefined;
    if (fin?.length) bits.push(fin.join(","));
  } else if (s.kind === "read" || s.kind === "write") {
    if (s.status) bits.push(String(s.status));
    if (a["larkfield.order.id"]) bits.push(String(a["larkfield.order.id"]));
    if (a["larkfield.refund.amount"] !== undefined) bits.push(`${num(lang, Number(a["larkfield.refund.amount"]), 2)} ${a["larkfield.refund.reason"] ?? ""}`.trim());
    if (a["larkfield.sku"] && s.tool !== "get_order") bits.push(`${a["larkfield.sku"]}${a["larkfield.quantity"] ? ` × ${a["larkfield.quantity"]}` : ""}`);
    if (a["larkfield.idempotency_key"]) bits.push(t("res_key", { key: String(a["larkfield.idempotency_key"]) }));
    if (a["larkfield.input.injection"]) bits.push(t("res_injected", { ask: String(a["larkfield.input.injection_ask"]) }));
  } else if (s.kind === "agent") {
    const p = a["larkfield.proposal.outcome"] || a["larkfield.stop_reason"];
    if (p) bits.push(String(p));
    if (a["larkfield.proposal.rule"]) bits.push(t("res_rule", { rule: String(a["larkfield.proposal.rule"]) }));
  } else if (s.name === "approval.request") {
    bits.push(t("res_needs", { role: label(t, "role_", String(a["larkfield.approval.needs_role"] ?? "")) }));
  } else if (s.op === "approve") {
    const lim = a["larkfield.approval.limit"];
    bits.push(`${label(t, "dec_", String(a["larkfield.approval.decision"] ?? ""))} · ${a["larkfield.approval.approver"]} (${label(t, "role_", String(a["larkfield.approval.role"] ?? ""))}, ${lim === -1 ? t("no_limit") : lim})`);
  } else if (s.kind === "check") {
    bits.push(a["larkfield.reconcile.found"] ? t("found_yes") : t("found_no"));
  }
  return bits.join(" · ");
}

function Bar({ s, total }: { s: SpanView; total: number }) {
  const left = total > 0 ? (s.offset_s / total) * 100 : 0;
  const width = total > 0 ? Math.max((s.duration_s / total) * 100, 0.6) : 100;
  return (
    <div className="track" aria-hidden="true">
      <div className={`bar bar-${s.kind}${s.error ? " bar-error" : ""}`} style={{ left: `${Math.min(left, 99.4)}%`, width: `${Math.min(width, 100 - Math.min(left, 99.4))}%` }} />
    </div>
  );
}

export function RunScreen({ id }: { id: string }) {
  const { t, lang, ds, info } = useApp();
  useDefaultRun(id, "run");
  const { data, error, loading } = useApi<RunDetail>(id ? `runs/${encodeURIComponent(id)}` : null, { ds });
  const [open, setOpen] = useState<string>("");
  if (!id) return <><h1>{t("nav_run")}</h1><p>{t("run_pick")}</p><Loading /></>;
  if (error) return <><h1>{t("run_title", { id })}</h1><ErrorBox message={error} /></>;
  if (!data) return loading ? <Loading /> : null;
  const r = data.run;
  const tz = info.tz_hours;
  const marked = new Map<string, string[]>();
  for (const f of data.flags) for (const sid of f.spans) marked.set(sid, [...(marked.get(sid) ?? []), f.name]);
  const others = data.same_ticket.filter((x) => x !== r.run_id);

  return (
    <section aria-labelledby="run-h">
      <h1 id="run-h">
        {t("run_title", { id: r.run_id })} {r.constructed ? <Constructed /> : null}
      </h1>
      <p className="intro">{t("run_meta", { ticket: r.ticket, model: r.model, design: r.design, release: r.release, language: r.language })}</p>
      <dl className="stats">
        <Stat name={t("stat_outcome")}><Outcome value={r.outcome} /></Stat>
        <Stat name={t("stat_model_calls")}>{r.model_calls}</Stat>
        <Stat name={t("stat_reads")}>{r.reads}</Stat>
        <Stat name={t("stat_writes")}>{r.writes}</Stat>
        <Stat name={t("stat_approvals")}>{r.approvals}</Stat>
        <Stat name={t("stat_tokens")}>{num(lang, r.tokens_in)} / {num(lang, r.tokens_out)}</Stat>
        <Stat name={t("stat_cost")}>{money(lang, r.cost)}</Stat>
        <Stat name={t("stat_duration")}>{num(lang, r.duration_s, 1)} s</Stat>
      </dl>
      <ul className="actions">
        <li><a className="button" href={href("audit", r.run_id, { ds })}>{t("open_audit")}</a></li>
        {others.length ? (
          <li><a className="button ghost" href={href("compare", "", { ds, a: r.run_id, b: others[others.length - 1] })}>{t("open_compare")}</a></li>
        ) : null}
        {data.traces.map((tr) => (
          <Fragment key={tr.trace_id}>
            {tr.links.grafana ? <li><a className="button ghost" href={tr.links.grafana} target="_blank" rel="noreferrer noopener">{t("open_grafana", { n: tr.number })} <span aria-hidden="true">↗</span></a></li> : null}
            {tr.links.langfuse ? <li><a className="button ghost" href={tr.links.langfuse} target="_blank" rel="noreferrer noopener">{t("open_langfuse", { n: tr.number })} <span aria-hidden="true">↗</span></a></li> : null}
          </Fragment>
        ))}
      </ul>

      <section aria-labelledby="why-h" className={`callout ${data.flags.length ? "warn" : "ok"}`}>
        <h2 id="why-h">{t("why_flagged")}</h2>
        {data.flags.length === 0 ? <p>{t("no_flags")}</p> : (
          <ul className="why">
            {data.flags.map((f) => (
              <li key={f.name}>
                <p><FlagBadge name={f.name} /></p>
                <p><strong>{t("rule_text")}{colon(lang)}</strong>{t(`rule_${f.name}` as Key)}</p>
                <p><strong>{t("rule_output")}{colon(lang)}</strong><code lang="en">{f.why}</code></p>
                <p className="muted">{t("marked_steps", { n: f.spans.length })}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <h2>{t("timeline")}</h2>
      <p className="muted">{t("timeline_intro")}</p>
      {data.traces.map((tr) => {
        const wait = data.waits.find((w) => w.before_trace === tr.trace_id);
        return (
          <Fragment key={tr.trace_id}>
            {wait ? (
              <div className="wait" role="note">
                <p className="wait-time"><span aria-hidden="true">⏸ </span>{t("wait_band", { wait: waiting(wait.seconds) })}</p>
                {wait.approver ? (
                  <p>{t("wait_who", { name: wait.approver_name || wait.approver, id: wait.approver, role: label(t, "role_", wait.role), limit: wait.limit === -1 || wait.limit === null ? t("no_limit") : num(lang, wait.limit), decision: label(t, "dec_", wait.decision) })}</p>
                ) : null}
                <p className="muted">{when(lang, wait.from, tz)} → {when(lang, wait.to, tz)}</p>
                {wait.link.length ? <p className="muted">{t("wait_link", { n: tr.number, span: wait.link[0].span_id, trace: wait.link[0].trace_id })}</p> : null}
              </div>
            ) : null}
            <h3>
              {t("trace_head", { n: tr.number })} <code>{tr.trace_id}</code>
              <span className="muted"> · {when(lang, tr.start, tz)} · {num(lang, tr.duration_s, 1)} s</span>
            </h3>
            <div className="table-wrap" tabIndex={0} role="region" aria-label={t("trace_caption", { n: tr.number })}>
              <table className="waterfall">
                <caption className="sr-only">{t("trace_caption", { n: tr.number })}</caption>
                <thead>
                  <tr>
                    <th scope="col" className="num">{t("col_at")}</th>
                    <th scope="col">{t("col_step")}</th>
                    <th scope="col" className="barcol">{t("col_bar")}</th>
                    <th scope="col" className="num">{t("col_secs")}</th>
                    <th scope="col" className="num">{t("col_tokens")}</th>
                    <th scope="col" className="num">{t("col_cost")}</th>
                    <th scope="col">{t("col_result")}</th>
                  </tr>
                </thead>
                <tbody>
                  {tr.spans.map((s) => {
                    const flags = marked.get(s.span_id) ?? [];
                    const isOpen = open === s.span_id;
                    return (
                      <Fragment key={s.span_id}>
                        <tr className={`${flags.length ? "marked" : ""} ${s.error ? "err" : ""}`.trim() || undefined}>
                          <td className="num">{num(lang, s.offset_s, 1)}</td>
                          <th scope="row" style={{ paddingInlineStart: `${0.5 + s.depth * 1.1}rem` }}>
                            {flags.length ? <span className="mark" title={t("flagged_step")}><span aria-hidden="true">⚑</span><span className="sr-only">{t("flagged_step")}{colon(lang)}{flags.map((f) => t(`flag_${f}` as Key)).join(", ")}</span></span> : null}
                            <span className={`kind kind-${s.kind}`}>{s.name}</span>
                            {s.retry ? <span className="badge retry">{t("retry", { n: s.attempt ?? 2 })}</span> : null}
                            {s.error ? <span className="badge danger">{t("error_word")}{colon(lang)}{s.error_type}</span> : null}
                          </th>
                          <td className="barcol"><Bar s={s} total={tr.duration_s} /></td>
                          <td className="num">{num(lang, s.duration_s, 2)}</td>
                          <td className="num">{s.tokens_in !== null ? `${num(lang, s.tokens_in)} / ${num(lang, s.tokens_out ?? 0)}` : ""}</td>
                          <td className="num">{s.cost !== null ? num(lang, s.cost, 5) : ""}</td>
                          <td className="result">
                            <span>{result(s, t, lang)}</span>{" "}
                            <button type="button" className="link" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? "" : s.span_id)}>
                              {t("attrs")}<span className="sr-only"> {s.name}</span>
                            </button>
                          </td>
                        </tr>
                        {isOpen ? (
                          <tr className="attrs-row">
                            <td colSpan={7}>
                              <dl className="attrs" lang="en">
                                <div><dt>span_id</dt><dd><code>{s.span_id}</code></dd></div>
                                {Object.entries(s.attrs).map(([k, v]) => (
                                  <div key={k}><dt>{k}</dt><dd><code>{Array.isArray(v) ? v.join(", ") : String(v)}</code></dd></div>
                                ))}
                              </dl>
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Fragment>
        );
      })}
      {data.price_tables.length ? <p className="muted small">{t("price_note", { dates: data.price_tables.join(", ") })}</p> : null}
    </section>
  );
}
