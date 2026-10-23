import { useApi } from "../api";
import { label, type Ctx, useApp } from "../context";
import { colon, money, num, waiting } from "../format";
import type { Key } from "../i18n";
import { go, href } from "../router";
import type { CompareAnswer, RunRow, Step } from "../types";
import { Constructed, ErrorBox, Flags, Loading, Outcome, Select } from "../ui";

export function stepText(s: Step, t: Ctx["t"], lang: Ctx["lang"]): string {
  const v = s.value;
  if (s.kind === "model") {
    if (v.error) return t("step_model_error");
    if (v.proposal !== undefined) return t("step_model_decides", { proposal: v.proposal || "–", rule: v.rule || "–" });
    return t("step_model_asks", { tools: (v.requested as string[]).join(", ") || "–" });
  }
  if (s.kind === "tool") {
    if (s.sig.startsWith("check:")) return t("step_check", { name: s.name, found: v.found ? t("found_yes") : t("found_no") });
    const bits = [String(v.status || (v.error ? t("error_word") : ""))];
    if (s.order) bits.push(s.order);
    if (v.amount !== null && v.amount !== undefined) bits.push(num(lang, v.amount, 2));
    if (v.quantity) bits.push(`× ${v.quantity}`);
    if (s.attempt && s.attempt > 1) bits.push(t("retry", { n: s.attempt }));
    return t("step_tool", { tool: s.tool ?? s.name, status: bits.filter(Boolean).join(" · ") });
  }
  if (s.sig === "approval_request") return t("step_approval_request", { role: label(t, "role_", v.needs_role ?? "") });
  const lim = v.limit === -1 || v.limit === null || v.limit === undefined ? t("no_limit") : num(lang, v.limit);
  return t("step_approval", { who: v.approver ?? "?", decision: label(t, "dec_", v.decision ?? ""), role: label(t, "role_", v.role ?? ""), limit: lim })
    + (s.wait_s ? ` · ${waiting(s.wait_s)}` : "");
}

function Summary({ r, side }: { r: RunRow; side: "A" | "B" }) {
  const { t, lang, ds } = useApp();
  return (
    <div className="card">
      <h2>{side === "A" ? t("pick_a") : t("pick_b")}{colon(lang)}<a href={href("run", r.run_id, { ds })}>{r.run_id}</a> {r.constructed ? <Constructed /> : null}</h2>
      <dl className="kv">
        <div><dt>{t("col_model")}</dt><dd>{r.model} ({r.design})</dd></div>
        <div><dt>{t("col_outcome")}</dt><dd><Outcome value={r.outcome} /></dd></div>
        <div><dt>{t("stat_model_calls")}</dt><dd>{r.model_calls}</dd></div>
        <div><dt>{t("stat_writes")}</dt><dd>{r.writes}</dd></div>
        <div><dt>{t("stat_approvals")}</dt><dd>{r.approvals}</dd></div>
        <div><dt>{t("stat_tokens")}</dt><dd>{num(lang, r.tokens_in)} / {num(lang, r.tokens_out)}</dd></div>
        <div><dt>{t("stat_cost")}</dt><dd>{money(lang, r.cost)}</dd></div>
        <div><dt>{t("col_flags")}</dt><dd><Flags names={r.flags} /></dd></div>
      </dl>
    </div>
  );
}

export function CompareScreen({ params }: { params: Record<string, string> }) {
  const { t, lang, ds } = useApp();
  const { data, error, loading } = useApi<CompareAnswer>("compare", { ds, a: params.a, b: params.b });
  if (error) return <><h1>{t("compare_title")}</h1><ErrorBox message={error} /></>;
  if (!data) return loading ? <Loading /> : null;
  const ticket = data.a.ticket;
  const runsOfTicket = data.tickets[ticket] ?? [data.a.run_id, data.b.run_id];
  const fd = data.first_difference;
  const diffKind = fd ? t(`diff_${fd.kind}` as Key) : "";

  return (
    <section aria-labelledby="cmp-h">
      <h1 id="cmp-h">{t("compare_title")}</h1>
      <p className="intro">{t("compare_intro")}</p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <Select id="cmp-ticket" labelText={t("pick_ticket")} value={ticket} onChange={(v) => {
          const rs = data.tickets[v];
          if (rs) go("compare", "", { ds, a: rs[rs.length - 1], b: rs[0] });
        }} options={Object.entries(data.tickets).map(([k, v]) => ({ value: k, text: `${k} (${v.length})` }))} />
        <Select id="cmp-a" labelText={t("pick_a")} value={data.a.run_id} onChange={(v) => go("compare", "", { ds, a: v, b: data.b.run_id })}
          options={runsOfTicket.map((r) => ({ value: r, text: r }))} />
        <Select id="cmp-b" labelText={t("pick_b")} value={data.b.run_id} onChange={(v) => go("compare", "", { ds, a: data.a.run_id, b: v })}
          options={runsOfTicket.map((r) => ({ value: r, text: r }))} />
      </form>
      {!data.same_ticket ? <div className="callout warn" role="note">{t("not_same_ticket")}</div> : null}
      <div className="grid2">
        <Summary r={data.a} side="A" />
        <Summary r={data.b} side="B" />
      </div>
      <div className={`callout ${fd ? "warn" : "ok"}`} role="status">
        {fd ? (
          <>
            <p className="big">{t("first_diff", { row: fd.row + 1, kind: diffKind })}</p>
            <ul>
              <li><strong>A</strong> ({data.a.run_id}){colon(lang)}{fd.a ? stepText(fd.a, t, lang) : t("no_step")}</li>
              <li><strong>B</strong> ({data.b.run_id}){colon(lang)}{fd.b ? stepText(fd.b, t, lang) : t("no_step")}</li>
            </ul>
          </>
        ) : <p className="big">{t("no_diff")}</p>}
      </div>
      <div className="table-wrap" tabIndex={0} role="region" aria-label={t("compare_caption")}>
        <table className="compare">
          <caption className="sr-only">{t("compare_caption")}</caption>
          <thead>
            <tr>
              <th scope="col" className="num">{t("col_row")}</th>
              <th scope="col">{t("col_a", { id: data.a.run_id })}</th>
              <th scope="col">{t("col_b", { id: data.b.run_id })}</th>
              <th scope="col">{t("col_same")}</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i} className={`${row.same ? "" : "diff"}${fd && fd.row === i ? " first" : ""}`.trim() || undefined}>
                <th scope="row" className="num">{i + 1}</th>
                <td className={row.a ? `step step-${row.a.kind}` : "gap"}>{row.a ? <><span className="sname">{row.a.name}</span> <span>{stepText(row.a, t, lang)}</span></> : <span className="muted">— <span className="sr-only">{t("no_step")}</span></span>}</td>
                <td className={row.b ? `step step-${row.b.kind}` : "gap"}>{row.b ? <><span className="sname">{row.b.name}</span> <span>{stepText(row.b, t, lang)}</span></> : <span className="muted">— <span className="sr-only">{t("no_step")}</span></span>}</td>
                <td>{row.same ? <span className="ok-text"><span aria-hidden="true">= </span>{t("yes")}</span> : <span className="danger-text"><span aria-hidden="true">≠ </span>{t("no")}</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
