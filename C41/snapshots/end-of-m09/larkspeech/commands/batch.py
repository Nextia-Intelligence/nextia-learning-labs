"""`speech batch`: transcribe a folder of recorded calls with the queue worker, and print the cost per audio hour."""
import json
from pathlib import Path

from larkspeech import compare as C
from larkspeech import queue as Q
from larkspeech.paths import data_dir, outputs_dir


def register(sub):
    p = sub.add_parser("batch", help="transcribe a folder of calls (a queue), with cost per audio hour")
    p.add_argument("inbox", help="a folder of .wav or .flac calls")
    p.add_argument("--model", default="base")
    p.add_argument("--language", choices=["en", "fr"], default="en")
    p.set_defaults(run=run)


def run(args):
    costs = json.loads((Path(data_dir(args.data)) / "costs.json").read_text())
    out = outputs_dir() / "batch-results.jsonl"
    s = Q.run_worker(args.inbox, out, args.model, args.language)
    if not s["calls"]:
        print(f"Nothing new in {args.inbox} ({s['skipped']} done before). Results: {out}")
        return 0
    r = C.rtf(s["compute_seconds"], s["audio_seconds"])
    price = costs["cpu_server_usd_per_hour"]
    print(f"{s['calls']} calls ({s['audio_seconds'] / 60:.1f} min of audio) in {s['compute_seconds']:.1f} s: "
          f"real-time factor {r:.3f}; {s['skipped']} done before")
    print(f"Cost per audio hour on a CPU server at US${price}/hour (assumption): "
          f"US${C.cost_per_audio_hour(r, price):.4f}")
    print(f"Wrote {out} (card numbers removed from the text)")
    return 0
