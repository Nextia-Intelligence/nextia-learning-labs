"""A batch queue for recorded calls: a folder of new calls, a worker that transcribes them one by one, and a
results file. Run the worker again and it skips the calls it has done (results are kept by call ID)."""
import json
import time
from pathlib import Path

from larkspeech import asr, audio
from larkspeech import redact as X


def run_worker(inbox, results, model="base", language="en", vad=True):
    inbox, results = Path(inbox), Path(results)
    done = set()
    if results.exists():
        done = {json.loads(x)["file"] for x in results.read_text().splitlines() if x}
    m = asr.whisper(model)
    stats = {"calls": 0, "audio_seconds": 0.0, "compute_seconds": 0.0, "skipped": 0}
    with results.open("a", encoding="utf-8") as f:
        for p in sorted(inbox.glob("*.wav")) + sorted(inbox.glob("*.flac")):
            if p.name in done:
                stats["skipped"] += 1
                continue
            x, sr = audio.read(p)
            t0 = time.perf_counter()
            text, _, _ = asr.transcribe(x, language, model=m, vad=vad)
            dt = time.perf_counter() - t0
            f.write(json.dumps({"file": p.name, "text": X.redact_text(text, language), "seconds": round(dt, 3),
                                "audio_seconds": round(len(x) / sr, 2)}, ensure_ascii=False) + "\n")
            stats["calls"] += 1
            stats["audio_seconds"] += len(x) / sr
            stats["compute_seconds"] += dt
    return stats
