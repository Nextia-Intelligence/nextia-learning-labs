"""Runs each case N times, each run in a new conversation on fresh test data, and applies its checks."""

import atexit
import importlib
import shutil
import json
import os
import sys
import tempfile
from pathlib import Path

from .checks import run_check


def load_app(app_dir: Path | None):
    """Imports the help desk app from app_dir (default: this folder)."""
    root = (app_dir or Path(__file__).resolve().parents[1]).resolve()
    if not (root / "helpdesk" / "__init__.py").exists():
        raise SystemExit(f"No help desk app in {root} (expected a helpdesk folder there).")
    sys.path.insert(0, str(root))
    for name in list(sys.modules):
        if name == "helpdesk" or name.startswith("helpdesk."):
            del sys.modules[name]
    app = importlib.import_module("helpdesk")
    for sub in ("assistant", "store", "export", "config"):
        importlib.import_module(f"helpdesk.{sub}")
    return app, root


class Runner:
    def __init__(self, app_dir: Path | None = None, mode: str = "sim", judge: str = "recorded"):
        self.app, self.root = load_app(app_dir)
        self.mode = mode
        self.judge = judge
        self.home = tempfile.mkdtemp(prefix="qa-store-")
        atexit.register(shutil.rmtree, self.home, True)
        os.environ["HELPDESK_HOME"] = self.home
        self.assistant = sys.modules["helpdesk.assistant"]
        self.store = sys.modules["helpdesk.store"]
        self.export = sys.modules["helpdesk.export"]

    def versions(self) -> dict:
        a = self.app
        return {"app": getattr(a, "APP_NAME", "?"), "app_version": a.APP_VERSION, "model": a.MODEL_NAME
                if self.mode == "sim" else "live", "prompt_version": a.PROMPT_VERSION, "app_folder": str(self.root)}

    def converse(self, customer: str | None, seed: int, steps: list[str]) -> dict:
        """One run: fresh data, a new conversation, the steps in order."""
        self.store.reset()
        cid = self.assistant.start(customer, seed, self.mode)
        replies, error = [], None
        for text in steps:
            try:
                replies.append(self.assistant.send(cid, text)["reply"])
            except Exception as e:  # the app failed: that is a finding, not a runner error
                error = f"{type(e).__name__}: {e}"
                break
        traces = self.store.traces_of(cid)
        orders = {o["id"]: o["status"] for c in self.store.customers() for o in self.store.orders_of(c["id"])}
        return {"conversation_id": cid, "replies": replies, "traces": traces, "error": error, "orders": orders,
                "export": self.export.export(cid)}

    def run_case(self, case, runs: int, seed_start: int) -> dict:
        results = []
        for i in range(runs):
            seed = seed_start + i
            if case.variants:
                outs = [self._one(case, seed, case.steps[:-1] + [v] if case.steps else [v]) for v in case.variants]
                results.append(self._relate(case, seed, outs))
            else:
                results.append(self._one(case, seed, case.steps))
        passed = sum(r["passed"] is True for r in results)
        not_run = sum(r["passed"] is None for r in results)
        need = case.required(runs)
        if not_run and passed + not_run >= need and passed < need:
            verdict = "not_run"
        else:
            verdict = "pass" if passed >= need else "fail"
        return {"id": case.id, "title": case.title, "file": str(case.file), "status": case.status, "bug": case.bug,
                "runs": runs, "passed_runs": passed, "not_run_runs": not_run, "required": need,
                "rule": case.pass_rule, "result": verdict, "run_results": results}

    def _one(self, case, seed: int, steps: list[str]) -> dict:
        out = self.converse(case.customer, seed, steps)
        turn = case.turn or len(steps)
        out["reply"] = out["replies"][turn - 1] if len(out["replies"]) >= turn else None
        out["trace"] = out["traces"][turn - 1] if len(out["traces"]) >= turn else None
        out["question"] = steps[turn - 1] if steps else ""
        failures, unknown = [], []
        for c in case.checks:
            ok, msg = run_check(c, out, case, {"judge": self.judge})
            if ok is None:
                unknown.append(msg)
            elif not ok:
                failures.append(msg)
        passed = False if failures else (None if unknown else True)
        trace_id = out["trace"]["trace_id"] if out["trace"] else None
        return {"seed": seed, "passed": passed, "failures": failures + unknown, "reply": out["reply"],
                "error": out["error"], "trace_id": trace_id, "conversation_id": out["conversation_id"],
                "export": out["export"]}

    def _relate(self, case, seed: int, outs: list[dict]) -> dict:
        """Metamorphic relation: the variants must give the same check results (or all pass)."""
        if case.relation == "all_pass":
            ok = all(o["passed"] is True for o in outs)
            fails = [f"variant {n}: {f}" for n, o in enumerate(outs, 1) for f in o["failures"]]
        else:
            ok = len({o["passed"] for o in outs}) == 1
            fails = [] if ok else [
                "the variants give different results: " + ", ".join(
                    f"variant {n} {'passes' if o['passed'] else 'fails'}" for n, o in enumerate(outs, 1))
            ] + [f"variant {n}: {f}" for n, o in enumerate(outs, 1) for f in o["failures"]]
        return {"seed": seed, "passed": ok, "failures": fails, "reply": " || ".join(str(o["reply"]) for o in outs),
                "error": next((o["error"] for o in outs if o["error"]), None),
                "trace_id": outs[0]["trace_id"], "conversation_id": outs[0]["conversation_id"],
                "export": [o["export"] for o in outs], "variants": [
                    {"passed": o["passed"], "reply": o["reply"], "failures": o["failures"]} for o in outs]}


def save_exports(result: dict, folder: Path) -> list[str]:
    """Saves the conversation of every failing run, to attach to a bug report."""
    saved = []
    for r in result["run_results"]:
        if r["passed"] is True:
            continue
        folder.mkdir(parents=True, exist_ok=True)
        p = folder / f"{result['id']}-seed{r['seed']}.json"
        p.write_text(json.dumps(r["export"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        saved.append(str(p))
    return saved
