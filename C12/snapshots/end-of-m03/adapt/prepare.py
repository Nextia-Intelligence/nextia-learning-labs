"""Turn the source tickets into clean training and validation records (Module 2).

    python -m adapt prepare [--per-team 200] [--extra FILE]

Rules, in this order. A record that breaks one is rejected, and the reason is written down:
1. known wrong label   the deep learning course made 70 team labels wrong on purpose
2. secret              a card number, a password or an email address in the text
3. duplicate           the same words as an earlier record, or a near copy (word 3-gram overlap >= NEAR)
4. evaluation leak     the same or nearly the same text as an evaluation case (any split)
Then: a sample per team (every record that needs a person is kept), and a split into train and validation
that keeps each team and the needs-a-person records in both parts. The evaluation cases are never training data.
"""

import collections
import hashlib
import json
import random
import re
from pathlib import Path

from .cases import SPLITS, load_cases
from .records import load_source, to_record

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "data/prepared"
NEAR = 0.4  # word 3-gram Jaccard overlap at or above this = a near copy
SEED = 12

SECRETS = {
    "card number": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    # A password is a word with a digit or a symbol after "password is" or "password:". The first version
    # of this rule ("password is" + any word) rejected 13 tickets that say "my password is wrong".
    "password": re.compile(r"(?i)\b(password|passcode|pwd)\b\s*(is|was|:|=)\s*[\"']?(?=\S*[\d!@#$%^&*])\S{6,}"),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", text.lower()))


def shingles(text: str, n: int = 3) -> frozenset:
    words = normalize(text).split()
    return frozenset(tuple(words[i:i + n]) for i in range(max(1, len(words) - n + 1)))


def overlap(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def find_secret(text: str) -> str:
    for name, pattern in SECRETS.items():
        if pattern.search(text):
            return name
    return ""


def load_extra(path: Path) -> list[dict]:
    """Extra records (one JSON object per line: id, text, team, needs_human, source)."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows.append({"id": r["id"], "text": r["text"], "team": r["team"], "style": r.get("style", ""),
                         "needs_human": bool(r["needs_human"]), "rule": r.get("rule", ""),
                         "label_how": r.get("label_how", ""), "source": r.get("source", "extra")})
    return rows


def clean(rows: list[dict], known_wrong: set[str], cases) -> tuple[list[dict], list[dict]]:
    kept, rejected = [], []
    case_sh = [(c, shingles(c.text), normalize(c.text)) for c in cases if c.text.strip()]
    seen_exact: dict[str, str] = {}
    index: dict[tuple, list[int]] = collections.defaultdict(list)  # shingle -> kept records
    kept_sh: list[frozenset] = []
    for row in rows:
        reason, detail = "", ""
        norm, sh = normalize(row["text"]), shingles(row["text"])
        if row["id"] in known_wrong:
            reason, detail = "known wrong label", f"team {row['team']} is wrong on purpose"
        elif secret := find_secret(row["text"]):
            reason, detail = "secret", secret
        elif norm in seen_exact:
            reason, detail = "duplicate", f"same words as {seen_exact[norm]}"
        else:
            candidates = collections.Counter(i for g in sh for i in index.get(g, ()))
            near = [(overlap(sh, kept_sh[i]), kept[i]["id"]) for i in candidates]
            near = max(near, default=(0.0, ""))
            if near[0] >= NEAR:
                reason, detail = "duplicate", f"near copy of {near[1]} (overlap {near[0]:.2f})"
            else:
                for case, csh, cnorm in case_sh:
                    if norm == cnorm or overlap(sh, csh) >= NEAR:
                        how = "same words as" if norm == cnorm else f"near copy (overlap {overlap(sh, csh):.2f}) of"
                        reason, detail = "evaluation leak", f"{how} evaluation case {case.case_id} ({case.split})"
                        break
        if reason:
            rejected.append({"id": row["id"], "source": row["source"], "reason": reason, "detail": detail})
            continue
        seen_exact[norm] = row["id"]
        for g in sh:
            index[g].append(len(kept))
        kept_sh.append(sh)
        kept.append(row)
    return kept, rejected


def sample(rows: list[dict], per_team: int | None, seed: int = SEED) -> list[dict]:
    """per_team records of each team; records that need a person are always kept (they are rare)."""
    if not per_team:
        return list(rows)
    rng = random.Random(seed)
    out = []
    for team in sorted({r["team"] for r in rows}):
        group = [r for r in rows if r["team"] == team]
        must = [r for r in group if r["needs_human"]]
        rest = [r for r in group if not r["needs_human"]]
        rng.shuffle(rest)
        out += must + rest[:max(0, per_team - len(must))]
    return sorted(out, key=lambda r: r["id"])


def split(rows: list[dict], val_share: float, seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Validation gets val_share of each (team, needs_human) group, so both parts cover every group."""
    rng = random.Random(seed + 1)
    train, val = [], []
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["team"], r["needs_human"])].append(r)
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda r: r["id"])
        rng.shuffle(group)
        n_val = round(len(group) * val_share)
        val += group[:n_val]
        train += group[n_val:]
    return sorted(train, key=lambda r: r["id"]), sorted(val, key=lambda r: r["id"])


def coverage(rows: list[dict]) -> dict:
    return {
        "teams": dict(sorted(collections.Counter(r["team"] for r in rows).items())),
        "needs_human": sum(r["needs_human"] for r in rows),
        "styles": dict(sorted(collections.Counter(r["style"] for r in rows).items())),
        "french": sum(r.get("language", "en") == "fr" for r in rows),
    }


def sha12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def prepare(per_team: int | None = 200, val_share: float = 0.1, seed: int = SEED, extra: Path | None = None,
            out: Path = PREPARED, source_dir: Path | None = None) -> dict:
    root = ROOT if source_dir is None else source_dir
    rows = load_source(root / "data/source")
    if extra:
        rows += load_extra(extra)
    known_wrong = set((root / "data/source/known_wrong_labels.txt").read_text(encoding="utf-8").split())
    cases = load_cases(SPLITS, root / "data/eval/cases.jsonl")
    kept, rejected = clean(rows, known_wrong, cases)
    chosen = sample(kept, per_team, seed)
    train, val = split(chosen, val_share, seed)
    out.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", train), ("val", val)):
        (out / f"{name}.jsonl").write_text(
            "".join(json.dumps(to_record(r), ensure_ascii=False, sort_keys=True) + "\n" for r in part),
            encoding="utf-8")
    (out / "rejected.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rejected), encoding="utf-8")
    manifest = {
        "settings": {"per_team": per_team, "val_share": val_share, "seed": seed, "near": NEAR,
                     "extra": Path(extra).name if extra else None},
        "source_records": len(rows),
        "rejected": dict(sorted(collections.Counter(r["reason"] for r in rejected).items())),
        "clean_records": len(kept),
        "train": {"records": len(train), "sha256_12": sha12(out / "train.jsonl"), **coverage(train)},
        "val": {"records": len(val), "sha256_12": sha12(out / "val.jsonl"), **coverage(val)},
        "evaluation_cases_version": sha12(root / "data/eval/cases.jsonl"),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["rejected_rows"] = rejected
    return manifest
