"""`speech redact` (one call: text and audio) and `speech privacy-check` (every text file in a folder)."""
from pathlib import Path

import soundfile as sf

from larkspeech import asr
from larkspeech import data as D
from larkspeech import redact as X
from larkspeech.paths import data_dir, outputs_dir


def register(sub):
    p = sub.add_parser("redact", help="remove card numbers from a call's transcript and beep them in its audio")
    p.add_argument("call")
    p.add_argument("--model", default="base")
    p.set_defaults(run=run_redact)
    q = sub.add_parser("privacy-check", help="look for card numbers in every .txt and .jsonl file of a folder")
    q.add_argument("folder", nargs="?", default="outputs")
    q.set_defaults(run=run_check)


def run_redact(args):
    d = data_dir(args.data)
    c = D.call(d, args.call)
    x, sr = D.load_audio(d, c["call_id"])
    _, segs, _ = asr.transcribe(x, c["language"], args.model, word_timestamps=True)
    words = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    red, spans = X.redact_words(words, c["language"], strict=False)
    text = " ".join(w for w, _, _ in red)
    out = outputs_dir() / "redacted"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{c['call_id']}.txt").write_text(text + "\n", encoding="utf-8")
    sf.write(out / f"{c['call_id']}.wav", X.beep(x, sr, spans), sr, subtype="PCM_16")
    found = len(X.card_numbers(" ".join(w for w, _, _ in words), c["language"], strict=False))
    print(f"{c['call_id']}: {found} card number(s) heard, {len(spans)} beeped "
          + ", ".join(f"{s:.1f}-{e:.1f} s" for s, e in spans))
    print(f"Wrote {out / (c['call_id'] + '.txt')} and {out / (c['call_id'] + '.wav')}")
    if found != len(spans):
        print("Warning: a card number is in the text but its words could not be timed; do not keep this audio.")
        return 1
    return 0


def run_check(args):
    folder = Path(args.folder)
    texts = {str(p): p.read_text(encoding="utf-8", errors="replace") for p in folder.rglob("*")
             if p.suffix in (".txt", ".jsonl", ".json") and p.is_file()}
    problems = X.privacy_check(texts) + X.privacy_check(texts, "fr")  # 12 digits or more in a row
    problems = sorted(set(problems))
    print(f"Privacy check: {len(texts)} text files in {folder}; "
          + ("no card numbers found. Passed." if not problems else f"{len(problems)} card numbers found:"))
    for name, n in problems[:20]:
        print(f"  {name}: {n[:4]}...{n[-4:]}")
    return 1 if problems else 0
