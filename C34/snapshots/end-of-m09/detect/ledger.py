"""Remember which alerts were sent, so that a rerun of the same day sends nothing twice (idempotent runs)."""
import json
import os
from pathlib import Path


def _ids(path: Path) -> set:
    if not path.exists():
        return set()
    return {json.loads(x)["alert_id"] for x in path.read_text().splitlines() if x.strip()}


def sent_ids(state_dir: Path, alerts_dir: Path, day) -> set:
    """The alerts already sent: from the ledger, and from the day's alert file (if a run stopped between the
    two writes, the alert file is the truth)."""
    return _ids(Path(state_dir) / "sent.jsonl") | _ids(Path(alerts_dir) / f"{day}.jsonl")


def send(alerts, day, state_dir: Path, alerts_dir: Path):
    """Write the new alerts to alerts/<day>.jsonl (the "send"), then add them to the ledger. Returns
    (new alerts, number already sent)."""
    state_dir, alerts_dir = Path(state_dir), Path(alerts_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    alerts_dir.mkdir(parents=True, exist_ok=True)
    done = sent_ids(state_dir, alerts_dir, day)
    new = [a for a in alerts if a["alert_id"] not in done]
    if new:
        out = alerts_dir / f"{day}.jsonl"
        old = out.read_text() if out.exists() else ""
        tmp = out.with_suffix(".tmp")
        tmp.write_text(old + "".join(json.dumps(a) + "\n" for a in new))
        os.replace(tmp, out)                          # all the new alerts appear at once, or none
        with open(state_dir / "sent.jsonl", "a") as f:
            for a in new:
                f.write(json.dumps({"alert_id": a["alert_id"], "day": a["day"]}) + "\n")
    return new, len(alerts) - len(new)
