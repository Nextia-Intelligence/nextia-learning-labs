"""Build the fine-tuning course's data files from the labs data of two earlier courses (no network).

    python reference/c12/data/build_data.py LABS_DIR OUT_DIR

LABS_DIR is a clone of nextia-learning-labs. OUT_DIR gets data/ for the project (and for labs C12/data):
- source/tickets.csv            the deep learning course's TRAINING split (C06/data/train.csv), unchanged
- source/needs_human.csv        the needs_human labels for those tickets (Grace's rule H1, read by the course author)
- source/known_wrong_labels.txt the 70 training rows whose team the deep learning course made wrong on purpose
- eval/cases.jsonl              the evaluation course's 271 labelled cases (C11/data/cases.jsonl), the fields
                                this course uses
- eval/policy.md                Grace's policy (C11/data/policy.md), unchanged
- SHA256SUMS

Every input is checked against its SHA-256 first. The same inputs give the same bytes.
"""

import csv
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

INPUTS = {
    "C06/data/train.csv": "98487169346f8b0d9bc55a3844849ab95d012b75f01d7083605a6a1cea57aa39",
    "C06/data/split_manifest.json": "d043cf720697054fb16e6cfff72ecb49b471d75038308ad5836779a0dd0bf8a5",
    "C11/data/cases.jsonl": "d4c96eaa10c003d4d734858a4e95791002c6a9619d807f3cc329b3c0780996bb",
    "C11/data/policy.md": "d6aa46d540a1f172cf9e497d5e8e9934046e26ef7252bb04d7210d361ac89db2",
}

# The evaluation course's word list for safety tickets (reference/c11/data/build_data.py, SAFETY).
SAFETY = re.compile(r"(?i)(unsafe|dangerous|danger\b|caught fire|on fire|flames?\b|smok(e|ing)|burning smell|"
                    r"smell of burning|burn(t|ed)? (my|his|her)|scorch|sparks?\b|sparked|sparking|electric shock|"
                    r"shocked|tingl|injur|hurt (my|him|her)|cut (my|his|her)|bleed|melt(ed|ing)|overheat|too hot|"
                    r"hazard|safe to use|safety)")

# The 98 training tickets that match SAFETY were read by the course author with rule H1
# ("a safety concern or an injury, even as a worry"). These 9 match a word but meet no rule:
NOT_H1 = {
    "T-60253": "a burner flame that will not stay lit: a fault, no worry about safety",
    "T-61513": "the pump of the trampoline's safety enclosure stopped: a fault",
    "T-61526": "asks whether the guarantee covers the safety net",
    "T-61756": "chose a trampoline with a good safety net; the ticket is about delivery",
    "T-62808": "a torn safety net on arrival: damaged in transit, no worry about safety",
    "T-63165": "the box with the safety net poles is missing",
    "T-63343": "says the chest is safe to use for now",
    "T-63759": "asks what the guarantee covers, including the safety mat",
    "T-64202": "the box with the safety net is missing",
}

CASE_FIELDS = ("case_id", "split", "slice", "language", "source", "style", "text", "attachments", "critical")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    labs, out = Path(sys.argv[1]), Path(sys.argv[2]) / "data"
    for name, digest in INPUTS.items():
        if sha256(labs / name) != digest:
            raise SystemExit(f"{name}: SHA-256 differs from the expected file")
    (out / "source").mkdir(parents=True, exist_ok=True)
    (out / "eval").mkdir(parents=True, exist_ok=True)

    shutil.copyfile(labs / "C06/data/train.csv", out / "source/tickets.csv")
    rows = list(csv.DictReader(io.StringIO((labs / "C06/data/train.csv").read_text(encoding="utf-8"))))
    matched = [r for r in rows if SAFETY.search(r["text"])]
    assert len(matched) == 98, len(matched)
    assert NOT_H1.keys() <= {r["ticket_id"] for r in matched}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["ticket_id", "needs_human", "rule", "how"])
    for r in rows:
        tid = r["ticket_id"]
        if tid in NOT_H1:
            w.writerow([tid, "false", "", f"read: {NOT_H1[tid]}"])
        elif r in matched:
            w.writerow([tid, "true", "H1", "read: a safety concern or an injury (H1)"])
        else:
            w.writerow([tid, "false", "", "not read: no safety word"])
    (out / "source/needs_human.csv").write_text(buf.getvalue(), encoding="utf-8")

    noisy = json.loads((labs / "C06/data/split_manifest.json").read_text(encoding="utf-8"))["noisy_train_ids"]
    (out / "source/known_wrong_labels.txt").write_text("\n".join(sorted(noisy)) + "\n", encoding="utf-8")

    lines = []
    for line in (labs / "C11/data/cases.jsonl").read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        row = {k: c[k] for k in CASE_FIELDS}
        row["team"] = c["expected"]["team"]
        row["needs_human"] = c["expected"]["needs_human"]
        row["rule"] = c["expected"]["rule"]
        lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    (out / "eval/cases.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copyfile(labs / "C11/data/policy.md", out / "eval/policy.md")

    files = ["source/tickets.csv", "source/needs_human.csv", "source/known_wrong_labels.txt",
             "eval/cases.jsonl", "eval/policy.md"]
    (out / "SHA256SUMS").write_text("".join(f"{sha256(out / f)}  {f}\n" for f in files), encoding="utf-8")
    print(f"Wrote {out}: {len(rows)} training tickets ({len(matched) - len(NOT_H1)} need a person), "
          f"{len(noisy)} known wrong labels, {len(lines)} evaluation cases")


if __name__ == "__main__":
    main()
