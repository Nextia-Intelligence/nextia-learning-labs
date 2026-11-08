"""`speech check`: the setup check. Transcribe one call with Whisper tiny, print its WER and real-time factor."""
from larkspeech import asr
from larkspeech import compare as C
from larkspeech import data as D
from larkspeech.paths import data_dir

FIRST_CALL = "C-0225"


def register(sub):
    p = sub.add_parser("check", help="transcribe one call with Whisper tiny: WER and real-time factor")
    p.add_argument("--call", default=FIRST_CALL)
    p.add_argument("--kind", choices=["phone", "wideband"], default="phone")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    c = D.call(d, args.call)
    x, sr = D.load_audio(d, c["call_id"], args.kind)
    seconds = len(x) / sr
    print(f"Call {c['call_id']} ({c['language']}, {c['line']} line, {args.kind} audio, {seconds:.1f} s, synthetic)")
    asr.transcribe(x[: sr], c["language"], "tiny")  # load the model before timing
    text, _, dt = asr.transcribe(x, c["language"], "tiny")
    ref = D.reference(c)
    w = C.wer(C.normalise(ref, "full", c["language"]), C.normalise(text, "full", c["language"]))
    print(f"Model:     {text[:160]}{' ...' if len(text) > 160 else ''}")
    print(f"Reference: {ref[:160]}{' ...' if len(ref) > 160 else ''}")
    print(f"WER {w:.1%} after the normalisation guide; real-time factor {C.rtf(dt, seconds):.3f} "
          f"({dt:.1f} s of compute for {seconds:.1f} s of audio)")
    print("Setup check passed." if w < 0.5 else "The WER is high: run `speech reset` and try again.")
    return 0
