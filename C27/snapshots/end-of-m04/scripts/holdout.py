"""Reserve the held-out questions BEFORE any tuning, and prove later that they did not change.

    python -m scripts.holdout reserve            split evaluation/questions.jsonl into
                                                 heldout.jsonl (about 40%) and dev.jsonl (the rest)
    python -m scripts.holdout check              the held-out file still matches its lock
    python -m scripts.holdout reserve --seed 27 --share 0.4 --questions my-questions.jsonl

The split is stratified: every shop and every kind of question (answerable, version, table,
unanswerable, ...) keeps the same share in both files, so the held-out set tests every kind.
heldout.lock keeps the SHA-256 of heldout.jsonl: the evaluation refuses a held-out file that
changed. Tune and inspect errors on dev.jsonl only. Look at the held-out answers once, at the end.
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent / "evaluation"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def split(questions: list[dict], seed: int, share: float) -> tuple[list[dict], list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for q in questions:
        groups.setdefault((q.get("tenant", ""), q.get("kind", "")), []).append(q)
    rng = random.Random(seed)
    held, dev = [], []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda q: q["id"])
        rng.shuffle(group)
        n = round(len(group) * share)
        if len(group) >= 2:
            n = min(max(n, 1), len(group) - 1)   # both sets get at least one of each kind
        held += group[:n]
        dev += group[n:]
    order = {q["id"]: i for i, q in enumerate(questions)}
    return sorted(held, key=lambda q: order[q["id"]]), sorted(dev, key=lambda q: order[q["id"]])


def write(path: Path, questions: list[dict]) -> None:
    path.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in questions), encoding="utf-8")


def summary(questions: list[dict]) -> str:
    shops = Counter(q.get("tenant", "") for q in questions)
    return f"{len(questions)} questions ({', '.join(f'{k} {v}' for k, v in sorted(shops.items()))})"


def check(folder: Path = EVAL) -> str:
    """Raises SystemExit if the held-out file is missing or changed. Returns a one-line summary."""
    lock, held = folder / "heldout.lock", folder / "heldout.jsonl"
    if not lock.exists() or not held.exists():
        raise SystemExit("No held-out set yet. Run: python -m scripts.holdout reserve")
    expected = json.loads(lock.read_text(encoding="utf-8"))["sha256"]
    if sha256(held) != expected:
        raise SystemExit("heldout.jsonl changed after it was reserved. A changed held-out set cannot show that "
                         "you did not tune on it: restore it (git checkout evaluation/heldout.jsonl).")
    return f"Held-out set: {summary(load(held))}. SHA-256 matches the lock ({expected[:12]}...)."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.holdout")
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("reserve")
    r.add_argument("--questions", type=Path, default=EVAL / "questions.jsonl")
    r.add_argument("--seed", type=int, default=27)
    r.add_argument("--share", type=float, default=0.4)
    r.add_argument("--force", action="store_true", help="reserve again (only before any tuning!)")
    sub.add_parser("check")
    args = parser.parse_args(argv)
    if args.command == "check":
        print(check())
        dev = EVAL / "dev.jsonl"
        if dev.exists():
            print(f"Tuning set (dev.jsonl): {summary(load(dev))}.")
        return 0
    if (EVAL / "heldout.lock").exists() and not args.force:
        print("A held-out set is already reserved. Reserving again after you have seen results would let "
              "tuning leak into it. Use --force only if you have not tuned anything yet.", file=sys.stderr)
        return 1
    held, dev = split(load(args.questions), args.seed, args.share)
    write(EVAL / "heldout.jsonl", held)
    write(EVAL / "dev.jsonl", dev)
    (EVAL / "heldout.lock").write_text(json.dumps({"sha256": sha256(EVAL / "heldout.jsonl"), "seed": args.seed,
                                                   "share": args.share, "questions": len(held)}, indent=1) + "\n",
                                       encoding="utf-8")
    kinds = Counter(q.get("kind", "") for q in held)
    print(f"Held out: {summary(held)}. Kinds: {', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}.")
    print(f"Tuning set: {summary(dev)}.")
    print("Wrote evaluation/heldout.jsonl, dev.jsonl and heldout.lock. Commit them now, before any tuning.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
