import { useState } from "react";
import { apiUrl, useApi } from "../api";
import { label, useApp } from "../context";
import { colon, num, waiting, when } from "../format";
import { go, href } from "../router";
import { effectText, role, sentenceFr } from "../story";
import type { AuditAnswer } from "../types";
import { Constructed, ErrorBox, Loading } from "../ui";
import { useDefaultRun } from "./Run";

export function AuditScreen({ id }: { id: string }) {
  const { t, lang, ds, info } = useApp();
  useDefaultRun(id, "audit");
  const { data, error, loading } = useApi<AuditAnswer>(id ? `runs/${encodeURIComponent(id)}/audit` : null, { ds });
  const [pick, setPick] = useState(id);
  const tz = info.tz_hours;

  const picker = (
    <form className="filters" onSubmit={(e) => { e.preventDefault(); if (pick) go("audit", pick.trim(), { ds }); }}>
      <div className="field">
        <label htmlFor="audit-run">{t("audit_pick")}</label>
        <input id="audit-run" value={pick} onChange={(e) => setPick(e.target.value)} spellCheck={false} />
      </div>
      <div className="field end"><button type="submit" className="button">{t("audit_open")}</button></div>
    </form>
  );

  if (!id) return <><h1>{t("audit_title")}</h1><Loading /></>;
  if (error) return <><h1>{t("audit_title")}</h1>{picker}<ErrorBox message={error} /></>;
  if (!data) return loading ? <Loading /> : null;

  const proposals = data.records.filter((r) => r.type === "proposal");
  const decisions = data.records.filter((r) => r.type === "approval" || r.type === "refusal");
  const closed = data.records.find((r) => r.type === "run_closed");
  const list = (xs: string[]) => (xs.length ? xs.join(", ") : t("none"));

  return (
    <section aria-labelledby="audit-h" className="audit">
      <h1 id="audit-h">
        {t("audit_title")}{colon(lang)}{data.ticket} <span className="muted">· {data.run_id}</span>{" "}
        {data.run_id.startsWith("C-") ? <Constructed /> : null}
      </h1>
      <p className="intro">{t("audit_intro")}</p>
      <div className="no-print">{picker}</div>

      <div className={`callout ${data.verify.ok ? "ok" : "danger"}`} role="status">
        <p className="big">
          <span aria-hidden="true">{data.verify.ok ? "✓ " : "✗ "}</span>
          {data.verify.ok ? t("verifies", { count: num(lang, data.verify.count) }) : t("not_verifies")}
        </p>
        {data.verify.problems.length && !data.verify.ok ? <ul>{data.verify.problems.map((p) => <li key={p} lang="en">{p}</li>)}</ul> : null}
        <p className="muted small">{t("head_hash", { head: data.verify.head.slice(0, 16) })}</p>
      </div>

      <dl className="facts">
        <div>
          <dt>{t("q_who_asked")}</dt>
          <dd>{t("who_asked", { customer: list(data.customers), ticket: data.ticket })}</dd>
        </div>
        <div>
          <dt>{t("q_read")}</dt>
          <dd>
            <ul>
              {data.reads.map((r) => (
                <li key={r.seq}>{t("read_item", { tool: r.tool, orders: (r.orders ?? []).join(", ") || "–", status: r.status })}</li>
              ))}
            </ul>
            <p>{t("evidence_orders", { list: list(data.orders) })}</p>
            <p>{t("evidence_passages", { list: list(data.passages) })}</p>
          </dd>
        </div>
        <div>
          <dt>{t("q_proposed")}</dt>
          <dd>
            {proposals.length ? (
              <ul>
                {proposals.map((p) => {
                  const acts = (p.action.actions ?? []).map((x: any) => effectText(lang, x)).join("; ") || t("no_change");
                  const need = p.authority.needs_role;
                  return <li key={p.seq}>{need ? t("proposed_item", { outcome: p.action.outcome, rule: p.action.rule, actions: acts, role: role(lang, need) }) : t("proposed_item_norole", { outcome: p.action.outcome, rule: p.action.rule, actions: acts })}</li>;
                })}
              </ul>
            ) : t("none")}
          </dd>
        </div>
        <div>
          <dt>{t("q_approved")}</dt>
          <dd>
            {decisions.length ? (
              <ul>
                {decisions.map((d) => (
                  <li key={d.seq}>
                    {t("approved_item", {
                      name: d.actor.name ?? d.actor.id, id: d.actor.id, title: lang === "en" && d.actor.title ? d.actor.title : role(lang, d.actor.role),
                      decision: label(t, "dec_", d.action.decision ?? ""), wait: waiting(d.action.wait_s),
                      limit: d.authority.limit === -1 || d.authority.limit === null || d.authority.limit === undefined ? t("no_limit") : num(lang, d.authority.limit),
                    })}
                  </li>
                ))}
              </ul>
            ) : t("nobody_approved")}
          </dd>
        </div>
        <div>
          <dt>{t("q_changed")}</dt>
          <dd>
            {data.changes.length ? (
              <ul>
                {data.changes.map((c) => (
                  <li key={JSON.stringify(c.effect)} className={c.calls > 1 ? "danger-text" : undefined}>
                    {t("changed_item", { effect: effectText(lang, c.effect), calls: c.calls, outcomes: c.outcomes.join(", "), keys: c.keys.length })}
                    {c.calls > 1 ? <strong> {t("changed_twice", { calls: c.calls })}</strong> : null}
                  </li>
                ))}
              </ul>
            ) : t("nothing_changed")}
          </dd>
        </div>
        {closed ? (
          <div>
            <dt>{t("q_closed")}</dt>
            <dd>{t("closed_item", { outcome: label(t, "out_", closed.action.outcome), writes: closed.action.writes_done, reply: closed.action.reply_status })}</dd>
          </div>
        ) : null}
      </dl>

      <h2>{t("story_head")}</h2>
      <div className="table-wrap" tabIndex={0} role="region" aria-label={t("story_caption")}>
        <table className="story">
          <caption className="sr-only">{t("story_caption")}</caption>
          <thead>
            <tr>
              <th scope="col" className="num">{t("col_seq")}</th>
              <th scope="col">{t("col_time")}</th>
              <th scope="col">{t("col_what")}</th>
            </tr>
          </thead>
          <tbody>
            {data.records.map((r) => (
              <tr key={r.seq} className={`rec rec-${r.type}${r.type === "write" && r.action.outcome !== "done" ? " err" : ""}`}>
                <th scope="row" className="num">{r.seq}</th>
                <td className="nowrap">{when(lang, Date.parse(r.at), tz)}</td>
                <td>{lang === "fr" ? sentenceFr(r) : r.sentence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>{t("chain_head")}</h2>
      <p className="muted">{t("chain_intro")}</p>
      <div className="table-wrap" tabIndex={0} role="region" aria-label={t("chain_caption")}>
        <table className="chain">
          <caption className="sr-only">{t("chain_caption")}</caption>
          <thead>
            <tr>
              <th scope="col" className="num">{t("col_seq")}</th>
              <th scope="col">{t("col_hash")}</th>
              <th scope="col">{t("col_prev")}</th>
              <th scope="col">{t("col_link_ok")}</th>
            </tr>
          </thead>
          <tbody>
            {data.records.map((r) => (
              <tr key={r.seq}>
                <th scope="row" className="num">{r.seq}</th>
                <td><code>{r.hash.slice(0, 16)}</code></td>
                <td><code>{r.prev.slice(0, 16)}</code> <span className="muted">(→ {r.seq - 1})</span></td>
                <td>{r.links_ok ? <span className="ok-text"><span aria-hidden="true">✓ </span>{t("yes")}</span> : <span className="danger-text"><span aria-hidden="true">✗ </span>{t("no")}</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">{t("traces_of_record", { list: data.trace_ids.join(", ") })}</p>

      <section aria-labelledby="export-h" className="no-print">
        <h2 id="export-h">{t("export_head")}</h2>
        <ul className="actions">
          <li><a className="button" href={apiUrl(`runs/${encodeURIComponent(data.run_id)}/audit.md`, { ds })} download>{t("export_md")}</a></li>
          <li><button type="button" className="button ghost" onClick={() => window.print()}>{t("export_pdf")}</button></li>
          <li><a className="button ghost" href={href("run", data.run_id, { ds })}>{t("nav_run")} {data.run_id}</a></li>
        </ul>
        <p className="muted small">{t("export_note")}</p>
      </section>
    </section>
  );
}
