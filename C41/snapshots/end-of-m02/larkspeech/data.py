"""The Larkfield call set: labels, audio files, slices and file checks. Every call is synthetic."""
import hashlib
import json
from pathlib import Path

from larkspeech import audio

SLICES = ("language", "line", "noise", "accent", "channels")


def load_calls(data, split=None, with_audio=False):
    rows = [json.loads(x) for x in (Path(data) / "calls/calls.jsonl").read_text(encoding="utf-8").splitlines() if x]
    if split:
        splits = split.split(",")
        rows = [r for r in rows if r["split"] in splits]
    if with_audio:
        rows = [r for r in rows if (Path(data) / "calls/phone" / f"{r['call_id']}.wav").exists()]
    return rows


def call(data, call_id):
    for r in load_calls(data):
        if r["call_id"] == call_id:
            return r
    raise FileNotFoundError(f"no call {call_id} in {data}/calls/calls.jsonl")


def audio_path(data, call_id, kind="phone"):
    p = Path(data) / "calls" / kind / (f"{call_id}.wav" if kind == "phone" else f"{call_id}.flac")
    if not p.exists():
        raise FileNotFoundError(f"{p} not found (only the validation and test calls have audio)")
    return p


def load_audio(data, call_id, kind="phone", sr=16000, channel=None):
    return audio.read(audio_path(data, call_id, kind), sr, channel)


def reference(c, speaker=None):
    """The reference transcript of a call (all turns, or one speaker's turns), in time order."""
    return " ".join(t["text"] for t in c["turns"] if speaker in (None, t["speaker"]))


def slice_of(c, name, kind="phone"):
    if name == "line":
        return "wideband" if kind == "wideband" else c["line"]
    if name == "channels":
        return "stereo" if c["channels"] == 2 else "mono"
    return c[name]


def load_ivr(data, split=None):
    rows = [json.loads(x) for x in (Path(data) / "ivr/calls.jsonl").read_text(encoding="utf-8").splitlines() if x]
    return [r for r in rows if split in (None, r["split"])]


def orders(data):
    return {o["order"]: o for o in json.loads((Path(data) / "orders.json").read_text())}


def check_files(data):
    """Compare every data file with SHA256SUMS. Returns (number of files, problems)."""
    data = Path(data)
    lines = (data / "SHA256SUMS").read_text().splitlines()
    problems = []
    for line in lines:
        digest, name = line.split(maxsplit=1)
        p = data / name
        if not p.exists():
            problems.append(f"missing: {name}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            problems.append(f"changed: {name}")
    return len(lines), problems
