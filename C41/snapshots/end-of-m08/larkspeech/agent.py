"""The voice agent, replayed: recorded LLM turns (Azure chat-small with tools) on the same test calls as the IVR,
a latency budget for each turn, and the IVR, the agent and a hybrid compared on the same calls."""
import json
from collections import defaultdict
from pathlib import Path

CONTAINED = ("status_given", "hours_given", "return_started")


def load(data):
    """recordings/agent/turns.jsonl (one LLM turn a line) and recordings/agent/calls.jsonl (one call a line)."""
    base = Path(data) / "recordings/agent"
    turns = defaultdict(list)
    for x in (base / "turns.jsonl").read_text(encoding="utf-8").splitlines():
        if x:
            t = json.loads(x)
            turns[t["call_id"]].append(t)
    calls = {c["call_id"]: c for c in (json.loads(x) for x in (base / "calls.jsonl").read_text().splitlines() if x)}
    return calls, turns


def budget(turn, end_of_turn=0.8, streaming=True, asr_key="asr_seconds"):
    """The parts of the wait from "the caller stops talking" to "the first sound back", in seconds."""
    llm = turn["ttft_s"] if streaming else turn["llm_s"]
    tts = turn["tts_first_s"] if streaming else turn["tts_all_s"]
    parts = {"end of turn (VAD wait)": end_of_turn, "recognition": turn[asr_key], "LLM": llm, "first audio": tts}
    return parts, sum(parts.values())


def input_budgets(turns, end_of_turn=0.8, streaming=True, asr_key="asr_base_s"):
    """One budget per caller turn. A caller turn can need several LLM calls (a tool call first, then the answer):
    the caller waits for every call before the one that speaks, and for recognition only once."""
    groups = defaultdict(list)
    for t in turns:
        groups[(t["call_id"], t["input"])].append(t)
    out = []
    for key, ts in groups.items():
        ts = sorted(ts, key=lambda t: t["turn"])
        speak = next((i for i, t in enumerate(ts) if t.get("reply")), None)
        if speak is None:
            continue
        before = sum(t["llm_s"] for t in ts[:speak])  # tool calls: the whole call must finish
        t = ts[speak]
        llm = before + (t["ttft_s"] if streaming else t["llm_s"])
        tts = t["tts_first_s"] if streaming else t["tts_all_s"]
        parts = {"end of turn (VAD wait)": end_of_turn, "recognition": ts[0].get(asr_key, 0.0), "LLM": llm,
                 "first audio": tts}
        out.append((key, parts, sum(parts.values())))
    return out


def design_rows(ivr_rows, agent_calls, costs):
    """Containment, seconds, hand-overs, wrong actions and cost per call for the IVR, the agent and a hybrid
    (the IVR first; the agent only for calls the IVR could not match)."""
    person = costs["call_handled_by_person"]
    wrong_cost = costs["wrong_action"]
    out = {}
    designs = {"IVR (menu)": {}, "voice agent": {}, "hybrid": {}}
    for r in ivr_rows:
        a = agent_calls.get(r["call_id"])
        designs["IVR (menu)"][r["call_id"]] = {"outcome": r["outcome"], "seconds": r["seconds"],
                                               "wrong": r["wrong_intent"], "usd": costs["ivr_call_compute"]}
        if a:
            designs["voice agent"][r["call_id"]] = {"outcome": a["outcome"], "seconds": a["seconds"],
                                                    "wrong": a["wrong_action"], "usd": a["usd"]}
            if r["outcome"] == "handover" and r.get("handoff_reason") == "no_match":
                designs["hybrid"][r["call_id"]] = {"outcome": a["outcome"], "seconds": r["seconds"] + a["seconds"],
                                                   "wrong": a["wrong_action"], "usd": a["usd"]
                                                   + costs["ivr_call_compute"]}
            else:
                designs["hybrid"][r["call_id"]] = designs["IVR (menu)"][r["call_id"]]
    for name, rows in designs.items():
        if not rows:
            continue
        n = len(rows)
        contained = [v for v in rows.values() if v["outcome"] in CONTAINED and not v["wrong"]]
        handed = sum(v["outcome"] == "handover" for v in rows.values())
        wrong = sum(bool(v["wrong"]) for v in rows.values())
        usd = sum(v["usd"] for v in rows.values()) + handed * person + wrong * wrong_cost
        out[name] = {"calls": n, "containment": len(contained) / n, "handover": handed / n, "wrong_actions": wrong,
                     "mean_seconds": sum(v["seconds"] for v in rows.values()) / n, "usd_per_call": usd / n}
    return out
