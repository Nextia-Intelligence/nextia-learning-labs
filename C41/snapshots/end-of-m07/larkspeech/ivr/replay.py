"""Replay the recorded IVR test calls through the same engine as the test phone, and score them."""
import json
from collections import defaultdict
from pathlib import Path

from larkspeech import audio
from larkspeech import data as D
from larkspeech.ivr.engine import CallSession, run_call, speak_seconds


def load_inputs(data, call):
    return [audio.read(Path(data) / "ivr" / i["file"], 8000)[0] for i in call["inputs"]]


def replay(data, asr, calls=None, end_of_turn=0.8, prompt_seconds=speak_seconds, **kw):
    orders = D.orders(data)
    out = []
    for c in calls or D.load_ivr(data, "public"):
        s = CallSession(orders, asr, end_of_turn=end_of_turn, call_id=c["call_id"], **kw)
        r = run_call(s, load_inputs(data, c), prompt_seconds)
        exp = c["expected"]
        ok = r["outcome"] == exp["outcome"] and (exp.get("order") in (None, r["order"]) or r["outcome"] == "handover")
        out.append({**r, "kind": c["kind"], "line": c["line"], "noise": c["noise"], "expected": exp, "passed": ok,
                    "wrong_intent": bool(exp.get("intent") and r["intent"] and r["intent"] != exp["intent"])})
    return out


def summary(rows, by=None):
    groups = defaultdict(list)
    for r in rows:
        groups[r.get(by, "all") if by else "all"].append(r)
    res = {}
    for k, rs in sorted(groups.items()):
        n = len(rs)
        contained = [r for r in rs if r["outcome"] in ("status_given", "hours_given", "return_started")]
        res[k] = {"calls": n, "passed": sum(r["passed"] for r in rs), "containment": len(contained) / n,
                  "wrong_intent": sum(r["wrong_intent"] for r in rs) / n,
                  "handover": sum(r["outcome"] == "handover" for r in rs) / n,
                  "seconds_to_answer": (sum(r["seconds"] for r in contained) / len(contained)) if contained else None}
    return res


def write_records(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
