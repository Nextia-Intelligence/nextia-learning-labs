"""Run a question set through the assistant and score it (Module 5).

    python -m scripts.evaluate --set dev                        the tuning questions (look at these freely)
    python -m scripts.evaluate --set heldout                    the held-out questions (once per version!)
    python -m scripts.evaluate --set dev --retrieval-only       no answers: only what the search finds
    python -m scripts.evaluate --set heldout --config RETRIEVAL_MODE=dense --label baseline
    python -m scripts.evaluate --set dev --out reports/dev.json --show-failures

Each question is asked by a member of its shop (Sam at Larkfield, Ines at Bramble Books), on the
question's date, through the same pipeline as the API. Answers come from ANSWER_PROVIDER: the
course team's recordings by default, so the numbers repeat without a key. The held-out file is
checked against its lock first.
"""

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

from doc_assistant import retrieve
from doc_assistant.config import settings as load_settings
from doc_assistant.context import assemble
from doc_assistant.evaluate import hit, score, summarise
from doc_assistant.pipeline import ask

from . import holdout
from .common import READ_ONLY, STAFF, as_member, open_deps

EVAL = Path(__file__).resolve().parent.parent / "evaluation"
FIELDS = {"RETRIEVAL_MODE": "retrieval_mode", "PROMPT_VERSION": "prompt_version", "TOP_K": "top_k",
          "CANDIDATES": "candidates", "ANSWER_PROVIDER": "answer_provider", "ANSWER_MODEL": "answer_model"}


def configured(settings, pairs: list[str]):
    changes = {}
    for pair in pairs:
        name, value = pair.split("=", 1)
        field = FIELDS[name]
        changes[field] = int(value) if field in ("top_k", "candidates") else value
    return replace(settings, **changes)


def load_set(name: str) -> list[dict]:
    if name == "heldout":
        holdout.check()
    path = EVAL / f"{name}.jsonl" if name in ("dev", "heldout", "questions") else Path(name)
    return holdout.load(path)


def retrieval_only(deps, questions: list[dict]) -> list[dict]:
    rows = []
    for q in questions:
        who = as_member(deps, STAFF[q["tenant"]], q["tenant"])
        start = time.monotonic()
        with deps.db.tenant(q["tenant"]) as conn:
            found = retrieve.search(conn, q["question"], q["tenant"], who.access_levels, q["as_of"], deps.embedder,
                                    deps.settings, deps.reranker)
        ms = round((time.monotonic() - start) * 1000, 1)
        passages = [{"doc_key": p.doc_key, "version": p.version, "section": p.section, "chunk_id": p.chunk_id}
                    for p in assemble(found).passages]
        rows.append({"id": q["id"], "tenant": q["tenant"], "kind": q["kind"], "hit": hit(q, passages),
                     "retrieval_ms": ms, "passages": passages})
    return rows


def answers(deps, questions: list[dict], users: dict = STAFF) -> list[dict]:
    rows = []
    for q in questions:
        who = as_member(deps, users[q["tenant"]], q["tenant"])
        result = ask(deps, who, q["question"], q["as_of"])
        answer = {"answer": result.answer, "answerable": result.answerable, "claims": result.claims,
                  "passages": result.passages}
        rows.append({**score(q, answer), "latency_ms": result.latency_ms, "generation_ms": result.generation_ms,
                     "cost_usd": result.cost_usd, "input_tokens": result.input_tokens,
                     "output_tokens": result.output_tokens, "provider": result.provider, "note": result.note,
                     "answer": result.answer, "claims": result.claims,
                     "passages": [p["chunk_id"] for p in result.passages]})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.evaluate")
    parser.add_argument("--set", default="dev", help="dev, heldout, or a .jsonl file")
    parser.add_argument("--tenant", choices=["all", "larkfield", "bramble"], default="all")
    parser.add_argument("--config", action="append", default=[], help="NAME=value, e.g. RETRIEVAL_MODE=dense")
    parser.add_argument("--label", default="")
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--as", dest="role", choices=["staff", "read-only"], default="staff",
                        help="read-only: ask as Omar (Larkfield) and Camille (Bramble Books)")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--show-failures", action="store_true")
    parser.add_argument("--min-correct", type=float, help="exit 1 if the share of correct answers is lower (CI)")
    args = parser.parse_args(argv)
    questions = [q for q in load_set(args.set) if args.tenant in ("all", q["tenant"])]
    s = configured(load_settings(), args.config)
    deps = open_deps(s)
    label = args.label or f"{s.retrieval_mode}, {s.prompt_version}, {s.answer_provider}"
    if args.retrieval_only:
        rows = retrieval_only(deps, questions)
        scored = [r["hit"] for r in rows if r["hit"] is not None]
        ms = sorted(r["retrieval_ms"] for r in rows)
        summary = {"questions": len(rows), "with_relevant_passages": len(scored),
                   "retrieval_hit": round(sum(scored) / len(scored), 3),
                   "retrieval_ms_median": ms[len(ms) // 2]}
        print(f"{label}: retrieval hit {summary['retrieval_hit']:.3f} ({sum(scored)} of {len(scored)} questions "
              f"with relevant passages), median search time {summary['retrieval_ms_median']} ms")
        if args.show_failures:
            for r in rows:
                if r["hit"] is False:
                    print(f"  missed {r['id']} ({r['tenant']}, {r['kind']})")
    else:
        rows = answers(deps, questions, READ_ONLY if args.role == "read-only" else STAFF)
        summary = summarise(rows)
        print(f"{label}: {summary['questions']} questions | correct {summary['correct']:.3f} | retrieval hit "
              f"{summary['retrieval_hit']:.3f} | citations valid {summary['citations_valid']:.3f} | abstained when it "
              f"should {summary['abstained_when_it_should']} | injection obeyed {summary['injection_obeyed']} of "
              f"{summary['injection_questions']} | median {summary['latency_ms_median']} ms | "
              f"US${summary['cost_usd_per_question']:.6f} per question")
        for kind, v in summary["by_kind"].items():
            print(f"  {kind:<15} {v['n']:>3}  correct {v['correct']}  hit {v['hit']}")
        if args.show_failures:
            for r in rows:
                if not r["correct"]:
                    print(f"  WRONG {r['id']} ({r['tenant']}, {r['kind']}, hit {r['hit']}): {r['answer'][:150]}")
    deps.db.close()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"set": args.set, "label": label, "config": args.config, "summary": summary,
                                        "rows": rows}, indent=1, ensure_ascii=False, default=str) + "\n")
        print(f"Wrote {args.out}")
    if args.min_correct is not None and not args.retrieval_only and summary["correct"] < args.min_correct:
        print(f"FAILED: correct {summary['correct']:.3f} is below {args.min_correct}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
