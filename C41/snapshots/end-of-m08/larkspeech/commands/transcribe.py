"""`speech transcribe`: run Whisper on calls now, score the result, and save the transcripts."""
import json

from larkspeech import asr, scoring
from larkspeech import data as D
from larkspeech.paths import data_dir, outputs_dir


def register(sub):
    p = sub.add_parser("transcribe", help="run Whisper on calls, score them, save outputs/transcripts-<name>.jsonl")
    p.add_argument("--model", choices=list(asr.WHISPER), default="tiny")
    p.add_argument("--split", default="test")
    p.add_argument("--kind", choices=["phone", "wideband"], default="phone")
    p.add_argument("--limit", type=int, default=10, help="only the first N calls (0 for all)")
    p.add_argument("--vad", action="store_true", help="cut the silences first (Silero VAD)")
    p.add_argument("--prompt", action="store_true", help="give Whisper the Larkfield vocabulary")
    p.add_argument("--language", choices=["en", "fr"], help="only calls in this language")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    calls = [c for c in D.load_calls(d, args.split, with_audio=True) if args.language in (None, c["language"])]
    calls = calls[: args.limit] if args.limit else calls
    name = f"whisper-{args.model}" + ("-vad" if args.vad else "") + ("-prompt" if args.prompt else "")
    m = asr.whisper(args.model)
    rows = {}
    for c in calls:
        x, sr = D.load_audio(d, c["call_id"], args.kind)
        text, _, dt = asr.transcribe(x, c["language"], vad=args.vad, prompt=args.prompt, model=m)
        rows[(c["call_id"], args.kind)] = {"call_id": c["call_id"], "kind": args.kind, "text": text, "seconds": dt}
    out = outputs_dir() / f"transcripts-{name}.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows.values()), encoding="utf-8")
    res = scoring.score(d, name, args.split, args.kind, None, transcripts=rows)["all"]
    o = res["important"].get("order", {"items": 0, "missed": 0})
    print(f"{name} on {len(calls)} {args.split} calls ({args.kind}): WER {res['wer']:.1%}, CER {res['cer']:.1%}, "
          f"order numbers wrong {o['missed']} of {o['items']}, real-time factor {res['rtf']:.3f}")
    print(f"Wrote {out}")
    return 0
