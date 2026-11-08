"""`speech info`: what is in the call set."""
from collections import Counter

from larkspeech import data as D
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("info", help="what is in the call set")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    calls = D.load_calls(d)
    split = Counter(c["split"] for c in calls)
    audio = D.load_calls(d, with_audio=True)
    hours = sum(c["duration"] for c in audio) / 3600
    print(f"Calls: {split['train']} train (transcripts only), {split['validation']} validation, "
          f"{split['test']} test; audio for {len(audio)} calls ({hours:.2f} hours, phone and wideband)")
    lang = Counter(c["language"] for c in audio)
    line = Counter(c["line"] for c in audio)
    print(f"Languages: {lang['en']} English, {lang['fr']} French; lines: "
          + ", ".join(f"{n} {k}" for k, n in sorted(line.items())))
    print(f"Stereo (agent and caller apart): {sum(c['channels'] == 2 for c in audio)}; "
          f"mono: {sum(c['channels'] == 1 for c in audio)}")
    ivr = D.load_ivr(d)
    print(f"IVR test calls: {len(ivr)}; orders in the fake order system: {len(D.orders(d))}")
    print("Every call is synthetic: open text-to-speech voices read invented scripts. "
          "The hidden test calls are not here.")
    return 0
