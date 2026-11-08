"""`speech ivr serve` (the test phone in your browser) and `speech ivr replay` (the recorded test calls)."""
from larkspeech import data as D
from larkspeech.ivr import replay as R
from larkspeech.paths import data_dir, outputs_dir


def register(sub):
    p = sub.add_parser("ivr", help="the Larkfield IVR: serve the test phone, or replay the recorded test calls")
    s = p.add_subparsers(dest="ivr_command", required=True)
    a = s.add_parser("serve", help="start the IVR and the test phone on http://127.0.0.1:PORT")
    a.add_argument("--port", type=int, default=8041)
    a.add_argument("--model", default="base", help="the Whisper size for the callers' words")
    a.add_argument("--end-of-turn", type=float, default=0.8)
    a.set_defaults(run=run_serve)
    b = s.add_parser("replay", help="run the recorded test calls through the IVR and score them")
    b.add_argument("--model", default="base")
    b.add_argument("--end-of-turn", type=float, default=0.8)
    b.add_argument("--by", choices=["kind", "line", "noise", "language"])
    b.add_argument("--calls", help="only these call IDs (comma-separated)")
    b.add_argument("--voice", action="store_true", help="time the prompts with the real voice (slower)")
    b.set_defaults(run=run_replay)


def run_serve(args):
    import uvicorn

    from larkspeech.ivr.app import create_app
    from larkspeech.ivr.engine import Recogniser
    app = create_app(D.orders(data_dir(args.data)), Recogniser(args.model), end_of_turn=args.end_of_turn)
    print(f"Open http://127.0.0.1:{args.port}/ and press Call. Stop with Ctrl+C.")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


def run_replay(args):
    from larkspeech.ivr.engine import Recogniser, speak_seconds
    d = data_dir(args.data)
    calls = D.load_ivr(d, "public")
    if args.calls:
        want = set(args.calls.split(","))
        calls = [c for c in calls if c["call_id"] in want]
    secs = speak_seconds
    if args.voice:
        from larkspeech.ivr import tts
        secs = lambda text: len(tts.say(text, "fr" if any(ch in text for ch in "éèàç") else "en")) / 8000  # noqa: E731
    rows = R.replay(d, Recogniser(args.model), calls, end_of_turn=args.end_of_turn, prompt_seconds=secs)
    for c, r in zip(calls, rows):
        r["language_expected"] = c["language"]
    R.write_records(rows, outputs_dir() / "ivr-replay.jsonl")
    res = R.summary(rows, args.by and ("language_expected" if args.by == "language" else args.by))
    print(f"IVR replay: {len(rows)} recorded test calls, Whisper {args.model}, end of turn {args.end_of_turn} s")
    print(f"{args.by or '':16} {'calls':>5} {'passed':>7} {'contained':>10} {'wrong intent':>13} {'to a person':>12} "
          f"{'s to answer':>12}")
    for k, v in res.items():
        t = f"{v['seconds_to_answer']:.1f}" if v["seconds_to_answer"] else "-"
        print(f"{k:16} {v['calls']:>5} {v['passed']:>7} {v['containment']:>10.0%} {v['wrong_intent']:>13.0%} "
              f"{v['handover']:>12.0%} {t:>12}")
    failed = [r for r in rows if not r["passed"]]
    if failed:
        print("Failed: " + ", ".join(f"{r['call_id']} ({r['kind']}: {r['outcome']}, expected "
                                     f"{r['expected']['outcome']})" for r in failed[:8]))
    print(f"Wrote {outputs_dir() / 'ivr-replay.jsonl'} (one call record per line)")
    return 0
