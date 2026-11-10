"""`speech inspect`: sample rate, channels, length, loudness and silence of calls."""
from larkspeech import audio
from larkspeech import data as D
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("inspect", help="sample rate, channels, length, loudness and silence of calls")
    p.add_argument("calls", nargs="*", help="call IDs (default: the first five test calls)")
    p.add_argument("--kind", choices=["phone", "wideband"], default="phone")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    ids = args.calls or [c["call_id"] for c in D.load_calls(d, "test", with_audio=True)[:5]]
    print(f"{'call':8} {'rate':>6} {'ch':>3} {'seconds':>8} {'loudness':>9} {'silence':>8}  format")
    for cid in ids:
        p = D.audio_path(d, cid, args.kind)
        i = audio.info(p)
        x, sr = audio.read(p, i["sample_rate"])
        print(f"{cid:8} {i['sample_rate']:>6} {i['channels']:>3} {i['seconds']:>8.1f} {audio.dbfs(x):>7.1f} dB "
              f"{audio.silence_share(x, sr):>7.0%}  {i['format']}")
    return 0
