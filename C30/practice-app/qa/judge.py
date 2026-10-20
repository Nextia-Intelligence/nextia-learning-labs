"""The judge check: a model scores a reply with a rubric.

Recorded judge (the default): the runner looks up a verdict that the course team
recorded with a real model for exactly this rubric, question and reply. A reply
that was never recorded is "not judged".

Live judge (--judge live): the runner asks a model at an OpenAI-compatible endpoint.
Set QA_JUDGE_URL (ends in /v1), QA_JUDGE_MODEL and QA_JUDGE_KEY. The key is never
printed or saved.
"""

import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path

RECORDINGS = Path(__file__).resolve().parent / "recordings" / "judge.jsonl"

TEMPLATE = """You are a careful reviewer of a customer support assistant. Score the assistant's reply with the rubric.

Rubric:
{rubric}

Customer message:
{question}

Assistant reply:
{reply}

Answer with JSON only: {{"score": <1, 2, 3 or 4>, "reason": "<one sentence>"}}"""

_cache: dict | None = None


def prompt_for(rubric: str, question: str, reply: str) -> str:
    return TEMPLATE.format(rubric=rubric.strip(), question=question.strip(), reply=reply.strip())


def key_for(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:20]


def recordings() -> dict:
    global _cache
    if _cache is None:
        _cache = {}
        if RECORDINGS.exists():
            for line in RECORDINGS.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    _cache[r["key"]] = r
    return _cache


def parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("the judge did not answer JSON")
    data = json.loads(m.group(0))
    return {"score": int(data["score"]), "reason": str(data.get("reason", ""))}


def live(prompt: str) -> dict:
    url, model = os.environ.get("QA_JUDGE_URL", ""), os.environ.get("QA_JUDGE_MODEL", "")
    if not url or not model:
        raise RuntimeError("--judge live needs QA_JUDGE_URL and QA_JUDGE_MODEL")
    body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    key = os.environ.get("QA_JUDGE_KEY", "")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("api-key", key)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    return parse(data["choices"][0]["message"]["content"])


def check(arg: dict, run: dict, case, ctx: dict) -> tuple[bool | None, str]:
    rubric = arg.get("rubric", "")
    path = (case.file.parent / rubric) if rubric and not rubric.strip().count("\n") else None
    if path is not None and path.exists():
        rubric = path.read_text(encoding="utf-8")
    min_score = int(arg.get("min_score", 3))
    prompt = prompt_for(rubric, run["question"], run["reply"] or "")
    if ctx.get("judge") == "live":
        verdict = live(prompt)
    else:
        verdict = recordings().get(key_for(prompt))
        if verdict is None:
            return None, "judge: no recorded verdict for this reply (use --judge live, or read it yourself)"
    ok = verdict["score"] >= min_score
    return ok, f"judge: score {verdict['score']} (minimum {min_score}): {verdict.get('reason', '')}"
