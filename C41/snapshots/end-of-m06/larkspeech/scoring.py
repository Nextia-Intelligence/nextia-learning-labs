"""Score recorded transcripts on the call set: WER and CER by slice, and the important-word errors."""
import json
from collections import defaultdict
from pathlib import Path

from larkspeech import compare as C
from larkspeech import data as D


def load_transcripts(data, method):
    """Recorded transcripts of one method: {(call_id, kind): row}. Files: recordings/asr/<method>.jsonl."""
    p = Path(data) / "recordings/asr" / f"{method}.jsonl"
    if not p.exists():
        names = sorted(q.stem for q in (Path(data) / "recordings/asr").glob("*.jsonl"))
        raise FileNotFoundError(f"no recorded transcripts for {method!r}; recorded: {', '.join(names)}")
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
    return {(r["call_id"], r["kind"]): r for r in rows}


def score(data, method, split="test", kind="phone", by=None, level="full", transcripts=None):
    """{slice value: {wer, cer, words, important..., audio_seconds, compute_seconds, rtf}}."""
    rec = transcripts or load_transcripts(data, method)
    groups = defaultdict(list)
    for c in D.load_calls(data, split, with_audio=True):
        r = rec.get((c["call_id"], kind))
        if r is None:
            continue
        key = D.slice_of(c, by, kind) if by else "all"
        groups[key].append((c, r))
    out = {}
    for key, items in sorted(groups.items()):
        s = C.corpus_scores([(D.reference(c), r["text"], c["language"]) for c, r in items], level)
        imp = C.sum_important([C.important_errors(c["important"], r["text"], c["language"]) for c, r in items])
        audio_s = sum(c["duration"] for c, _ in items)
        comp = sum(r.get("seconds", 0) for _, r in items)
        out[key] = {**s, "calls": len(items), "important": imp, "audio_seconds": audio_s, "compute_seconds": comp,
                    "rtf": comp / audio_s if audio_s else None}
    return out
