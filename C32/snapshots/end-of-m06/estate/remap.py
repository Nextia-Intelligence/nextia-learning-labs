"""The remap gate: before a capability moves to another model, every consumer's own evaluation must pass.

    python -m estate remap gate strong-reasoning --to azure/chat-small --param reasoning_effort=none

A remap changes every agent that asks for the capability at once, so it is a release. The gate finds the
consumers (the registrations that list the capability), runs each one's evaluation (its registration names
it, with a measure and a minimum) with the CURRENT mapping and with the CANDIDATE, and decides:

    pass   every consumer reaches its own minimum with the candidate
    block  at least one consumer does not, or a consumer has no evidence: no evaluation that the gate can run,
           or no answer of the candidate to score (nobody recorded these requests on that model)

It also prints the average over all items of all consumers, because that is the number a platform team is
tempted to use, and the cost per item. The evaluations replay the real recordings of the earlier courses, so
"the candidate" means "the answers that model really gave to these requests".
"""

import gzip
import json
from pathlib import Path

import yaml

from estate import catalog, paths

EVALUATIONS = paths.PROJECT / "evaluations"


class Caller:
    """Sends a request to one deployment of the provider simulator (in-process: no server needed)."""

    def __init__(self, target: catalog.Target):
        from starlette.testclient import TestClient

        from provsim.app import create_app

        self.target = target
        self.client = TestClient(create_app(state_dir=paths.state() / "remap-provider", speed=0.0, egress="open"))
        self.key = {"azure": "sim-az-gateway-0009", "azure-canada": "sim-az-gateway-0009"}.get(target.provider, "")
        self.tokens_in = self.tokens_out = self.calls = self.errors = self.inexact = 0

    def post(self, body: dict, repeat: int | None = None) -> tuple[int, dict]:
        headers = {"api-key": self.key}
        if repeat:
            headers["x-sim-repeat"] = str(repeat)
        r = self.client.post(f"/{self.target.provider}/v1/chat/completions", json=self.target.body_for(body),
                             headers=headers)
        self.calls += 1
        if r.headers.get("x-sim-match", "exact") != "exact":
            self.inexact += 1   # replayed from a recording made with another reasoning_effort: not the same request
        data = r.json()
        if r.status_code == 200:
            u = data.get("usage") or {}
            self.tokens_in += int(u.get("prompt_tokens") or 0)
            self.tokens_out += int(u.get("completion_tokens") or 0)
        else:
            self.errors += 1
        return r.status_code, data

    def cost(self, models: dict) -> float:
        p = (models.get(self.target.deployment) or {}).get("price") or {}
        return (self.tokens_in * p.get("input", 0) + self.tokens_out * p.get("output", 0)) / 1e6


def _items(name: str) -> list[dict]:
    with gzip.open(EVALUATIONS / name, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _content(data: dict) -> dict | None:
    try:
        text = data["choices"][0]["message"]["content"]
        return json.loads(text) if text else None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None


def eval_triage(target: catalog.Target) -> dict:
    """The evaluation course's triage set, dev split: team (if any) and needs_human both right."""
    caller = Caller(target)
    passed, items = 0, []
    for it in _items("ticket-triage.jsonl.gz"):
        status, data = caller.post(it["body"], 1)
        ans = _content(data) if status == 200 else None
        team_ok = not it["expected_team"] or (ans is not None and ans.get("team") == it["expected_team"])
        ok = ans is not None and ans.get("needs_human") == it["expected_needs_human"] and team_ok
        passed += ok
        items.append({"id": it["case_id"], "ok": bool(ok), "status": status})
    return {"items": items, "passed": passed, "total": len(items), "caller": caller}


def eval_judge(target: catalog.Target) -> dict:
    """The evaluation course's reference judge, dev: does the judge call a reply bad (critical or a score of
    1-2) exactly when the code checks found a failed rule? Requests without a verdict (the content filter)
    are left out, as that course did."""
    caller = Caller(target)
    passed, items, no_verdict = 0, [], 0
    for it in _items("release-judge.jsonl.gz"):
        status, data = caller.post(it["body"])
        v = _content(data) if status == 200 else None
        if not v or v.get("score") is None:
            no_verdict += 1
            items.append({"id": it["case_id"], "ok": None, "status": status})
            continue
        judge_bad = bool(v.get("critical")) or int(v["score"]) <= 2
        ok = judge_bad == it["code_bad"]
        passed += ok
        items.append({"id": it["case_id"], "ok": ok, "status": status})
    total = sum(1 for i in items if i["ok"] is not None)
    return {"items": items, "passed": passed, "total": total, "no_verdict": no_verdict, "caller": caller}


def eval_workflow(target: catalog.Target) -> dict:
    """The agents course's 70 resolution tasks with its structured agent: task success, every proposal
    approved as it is (that course's default: the worst case), on a fresh practice database per task."""
    from resolver.data import load_tasks
    from resolver.evaluate import run_and_score
    from resolver.providers import Completion, ProviderError

    caller = Caller(target)

    def complete(request, meta):
        status, data = caller.post(request, meta.get("repeat") or 1)
        if status != 200:
            raise ProviderError(f"HTTP {status}: {(data.get('error') or {}).get('message', '')}", status)
        return Completion.from_response(data, 0.0)

    items, passed, unexpected = [], 0, 0
    for task in load_tasks().values():
        s, _ = run_and_score(task, "agent_structured", "strong-reasoning", complete, "all", 1)
        passed += bool(s.success)
        unexpected += len(s.unexpected or [])
        items.append({"id": task.task_id, "ok": bool(s.success), "slice": task.slice, "unexpected": s.unexpected})
    return {"items": items, "passed": passed, "total": len(items), "unexpected_changes": unexpected,
            "caller": caller}


EVALUATORS = {
    "evaluation course, triage set, dev split": eval_triage,
    "evaluation course, agreement with the code checks (dev, bad or not)": eval_judge,
    "agents course, 70 resolution tasks": eval_workflow,
}


def _retired() -> set[str]:
    """The IDs that the registry marks as retired (none before the registry exists: Module 3 adds it)."""
    db = paths.state() / "registry.db"
    if not db.exists():
        return set()
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(db)) as con:
        try:
            return {r[0] for r in con.execute("select agent_id from agents where status = 'retired'")}
        except sqlite3.OperationalError:     # a registry file without the agents table yet
            return set()


def consumers(capability: str, also: list | None = None) -> list[dict]:
    """The registrations that list the capability (the forms in registrations/, registered or not), plus any
    "what if" forms given with --also. A form whose agent the registry has retired is not a consumer any more."""
    out, retired = [], _retired()
    for path in [*sorted(paths.REGISTRATIONS.glob("*.yaml")), *(Path(a) for a in also or [])]:
        form = yaml.safe_load(path.read_text(encoding="utf-8"))
        if capability in (form.get("capabilities") or []) and form.get("id") not in retired:
            out.append(form)
    return out


def gate(capability: str, provider: str, deployment: str, params: dict | None = None,
         consumers_only: list[str] | None = None, cat: dict | None = None, also: list | None = None) -> dict:
    cat = cat or catalog.load_catalog()
    models = catalog.load_models()
    current = catalog.targets(cat, capability)[0]
    candidate = catalog.Target(provider, deployment, dict(params or {}))
    result = {"capability": capability, "current": current.label(), "candidate": candidate.label(),
              "candidate_params": params or {}, "consumers": []}
    for form in consumers(capability, also):
        if consumers_only and form["id"] not in consumers_only:
            continue
        ev = (form.get("evaluations") or {}).get(capability)
        row = {"consumer": form["id"], "owner": form["owner"]}
        if not ev or ev["evaluation"] not in EVALUATORS:
            row.update(evaluation=(ev or {}).get("evaluation", "none"), verdict="no evidence",
                       reason="no evaluation that the gate can run: no evidence, no remap for this consumer")
            result["consumers"].append(row)
            continue
        fn = EVALUATORS[ev["evaluation"]]
        now, cand = fn(current), fn(candidate)
        if cand["total"] == 0 or cand["caller"].errors == cand["caller"].calls:   # not one answer to score
            row.update(evaluation=ev["evaluation"], verdict="no evidence",
                       reason=f"no answer of {candidate.label()} to score: no evidence, no remap for this consumer")
            result["consumers"].append(row)
            continue
        rate_now = now["passed"] / max(1, now["total"])
        rate_cand = cand["passed"] / max(1, cand["total"])
        row.update(evaluation=ev["evaluation"], measure=ev["measure"], minimum=ev["minimum"],
                   current={"passed": now["passed"], "total": now["total"], "rate": round(rate_now, 4),
                            "cost_usd": round(now["caller"].cost(models), 6), "errors": now["caller"].errors},
                   candidate={"passed": cand["passed"], "total": cand["total"], "rate": round(rate_cand, 4),
                              "cost_usd": round(cand["caller"].cost(models), 6), "errors": cand["caller"].errors,
                              "inexact_replays": cand["caller"].inexact},
                   verdict="pass" if rate_cand >= ev["minimum"] else "fail",
                   changed=[i["id"] for i, j in zip(now["items"], cand["items"]) if i["ok"] != j["ok"]])
        for k in ("unexpected_changes", "no_verdict"):
            if k in cand:
                row["candidate"][k] = cand[k]
                row["current"][k] = now[k]
        result["consumers"].append(row)
    scored = [c for c in result["consumers"] if "candidate" in c]
    tp = sum(c["candidate"]["passed"] for c in scored)
    tt = sum(c["candidate"]["total"] for c in scored)
    result["average_candidate"] = round(tp / max(1, tt), 4)
    result["average_current"] = round(sum(c["current"]["passed"] for c in scored)
                                      / max(1, sum(c["current"]["total"] for c in scored)), 4)
    result["mean_of_consumer_rates"] = round(sum(c["candidate"]["rate"] for c in scored) / max(1, len(scored)), 4)
    result["decision"] = "pass" if result["consumers"] and all(c["verdict"] == "pass" for c in result["consumers"]) \
        else "block"
    return result


def render(r: dict) -> str:
    lines = [f"Remap gate: {r['capability']} from {r['current']} to {r['candidate']}"
             + (f" with {r['candidate_params']}" if r["candidate_params"] else ""), ""]
    for c in r["consumers"]:
        if "candidate" not in c:
            lines.append(f"  {c['consumer']:<18} NO EVIDENCE  {c['reason']}")
            continue
        n, k = c["current"], c["candidate"]
        lines.append(f"  {c['consumer']:<18} {c['verdict'].upper():<5} {c['measure']} {k['passed']}/{k['total']} = "
                     f"{k['rate']:.3f} (minimum {c['minimum']}); today {n['passed']}/{n['total']} = {n['rate']:.3f}; "
                     f"cost US${k['cost_usd']:.4f} vs US${n['cost_usd']:.4f} today")
        if k.get("unexpected_changes") is not None:
            lines.append(f"  {'':<18} unexpected changes in the database: {k['unexpected_changes']} "
                         f"(today {n['unexpected_changes']})")
        if k.get("inexact_replays"):
            lines.append(f"  {'':<18} warning: {k['inexact_replays']} answers come from recordings made with another "
                         "reasoning_effort: the real model may answer differently")
        if c["changed"]:
            lines.append(f"  {'':<18} items that changed: {', '.join(c['changed'][:12])}"
                         + (" ..." if len(c["changed"]) > 12 else ""))
    lines += ["", f"Average over every item: {r['average_candidate']:.3f} with the candidate, "
                  f"{r['average_current']:.3f} today (mean of the consumers' rates: {r['mean_of_consumer_rates']:.3f})",
              f"Decision: {r['decision'].upper()}" + ("" if r["decision"] == "pass" else
                                                     " - every consumer must pass its own evaluation")]
    return "\n".join(lines)
