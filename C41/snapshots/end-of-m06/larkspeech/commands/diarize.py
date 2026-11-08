"""`speech diarize`: who spoke when, by channel or by speaker embeddings, with the diarization error rate;
`--call X --words` also writes who said what and when (Whisper word times joined to the speaker turns)."""
import numpy as np

from larkspeech import asr, audio
from larkspeech import data as D
from larkspeech import diarize as Z
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("diarize", help="who spoke when: DER by method, or one call with word times")
    p.add_argument("--method", choices=["channel", "embeddings"], default="embeddings")
    p.add_argument("--split", default="validation")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--call", help="one call: print its turns (and words with --words)")
    p.add_argument("--words", action="store_true", help="join Whisper tiny word times to the turns")
    p.add_argument("--each-side-alone", action="store_true",
                   help="channel: keep each side's speech as it is (no 'louder wins' when both sides seem to speak)")
    p.set_defaults(run=run)


def turns_for(d, c, method, louder_wins=True):
    if method == "channel":
        if c["channels"] != 2:
            return None
        x, sr = audio.read(D.audio_path(d, c["call_id"]), 16000, channel=0)
        y, _ = audio.read(D.audio_path(d, c["call_id"]), 16000, channel=1)
        return Z.by_channel(np.stack([x, y], axis=1), sr, louder_wins=louder_wins)
    x, sr = D.load_audio(d, c["call_id"])
    return Z.by_embeddings(x, sr)


def run(args):
    d = data_dir(args.data)
    if args.call:
        c = D.call(d, args.call)
        turns = turns_for(d, c, args.method, not args.each_side_alone)
        if turns is None:
            print(f"{c['call_id']} is mono: use --method embeddings")
            return 1
        r = Z.der(turns, Z.truth_turns(c), c["duration"])
        print(f"{c['call_id']} ({'stereo' if c['channels'] == 2 else 'mono'}), {args.method}: DER {r['der']:.1%} "
              f"(missed {r['missed']:.1%}, false {r['false']:.1%}, confusion {r['confusion']:.1%})")
        if args.words:
            x, sr = D.load_audio(d, c["call_id"])
            _, segs, _ = asr.transcribe(x, c["language"], "tiny", word_timestamps=True)
            lines = []
            for s in segs:
                for w in s.words:
                    who = Z.speaker_at(turns, (w.start + w.end) / 2)
                    if lines and lines[-1][0] == who:
                        lines[-1][2].append(w.word.strip())
                    else:
                        lines.append([who, w.start, [w.word.strip()]])
            for who, t, ws in lines:
                print(f"[{t:6.1f} s] {who:7} {' '.join(ws)}")
        else:
            for s, e, w in turns:
                print(f"{s:7.2f} {e:7.2f}  {w}")
        return 0
    calls = D.load_calls(d, args.split, with_audio=True)
    if args.method == "channel":
        calls = [c for c in calls if c["channels"] == 2]
    calls = calls[: args.limit] if args.limit else calls
    rows = []
    for c in calls:
        r = Z.der(turns_for(d, c, args.method, not args.each_side_alone), Z.truth_turns(c), c["duration"])
        rows.append((c, r))
    print(f"{args.method} on {len(rows)} {args.split} calls: mean DER {np.mean([r['der'] for _, r in rows]):.1%}")
    print("  " + ", ".join(f"{k} {np.mean([r[k] for _, r in rows]):.1%}" for k in ("missed", "false", "confusion")))
    sim = [r["der"] for c, r in rows if "similar_voices" in c["planted"]]
    if sim:
        print(f"  calls where the agent and the caller sound alike (planted): {len(sim)}, mean DER {np.mean(sim):.1%}")
    worst = sorted(rows, key=lambda x: -x[1]["der"])[:3]
    print("  worst: " + ", ".join(f"{c['call_id']} {r['der']:.0%}" for c, r in worst))
    return 0
