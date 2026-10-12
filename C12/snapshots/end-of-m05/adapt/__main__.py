"""The course's command line: python -m adapt COMMAND [options]. python -m adapt --help lists the commands."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS: dict = {}


def command(name: str, help: str, *arguments):
    def wrap(func):
        COMMANDS[name] = (func, help, arguments)
        return func
    return wrap


def arg(*names, **options):
    return names, options


def split_arg(default="dev"):
    return arg("--split", default=default, help="dev, holdout or contaminated; several with commas (dev,holdout)")


def splits_of(args) -> tuple[str, ...]:
    splits = tuple(args.split.split(","))
    if "holdout" in splits:
        print("Note: the holdout cases are for the final decision only. Read them once, at the end.")
    return splits


# Start: the evaluation cases

@command("cases", "count the evaluation cases by split and slice")
def cmd_cases(args):
    from .cases import SPLITS, load_cases, version

    cases = load_cases(SPLITS)
    print(f"{len(cases)} cases, version {version()} (the evaluation course's set)")
    for split in SPLITS:
        part = [c for c in cases if c.split == split]
        slices = {}
        for c in part:
            slices[c.slice] = slices.get(c.slice, 0) + 1
        needs = sum(c.needs_human for c in part)
        print(f"  {split:13s} {len(part):3d}  needs a person {needs:2d}  "
              + ", ".join(f"{k} {v}" for k, v in sorted(slices.items())))


@command("show", "show one evaluation case", arg("case_id"))
def cmd_show(args):
    from .cases import SPLITS, load_cases, model_input

    case = next((c for c in load_cases(SPLITS) if c.case_id == args.case_id), None)
    if case is None:
        raise SystemExit(f"No case {args.case_id}")
    print(f"{case.case_id} ({case.split}, {case.slice}, {case.language})")
    print(f"expected: team {case.team or '(none)'}, needs_human {str(case.needs_human).lower()}"
          + (f" (rule {case.rule})" if case.rule else ""))
    print()
    print(model_input(case))


# Module 1, lesson 1: what fails

@command("systems", "list the systems whose replies are saved")
def cmd_systems(args):
    from .predictions import systems

    for name, info in systems().items():
        print(f"{name:14s} {info['what']}")


@command("failures", "sort a system's mistakes into kinds", arg("system"), split_arg(),
         arg("--examples", type=int, default=2, help="examples to show for each kind"))
def cmd_failures(args):
    from .cases import load_cases
    from .failures import KINDS, failures
    from .predictions import load_predictions

    cases = load_cases(splits_of(args))
    preds = load_predictions(args.system)
    found = failures(cases, preds)
    wrong = len({c.case_id for kind in found.values() for c in kind})
    print(f"{args.system} on {args.split}: {wrong} of {len(cases)} cases have at least one mistake")
    for kind, label in KINDS.items():
        print(f"  {len(found[kind]):3d}  {label}")
    for kind, items in found.items():
        for case in items[:args.examples]:
            p = preds.get(case.case_id)
            raw = (p.raw if p else "").replace("\n", " ")
            print(f"\n[{kind}] {case.case_id}: expected team {case.team or '(none)'}, needs_human "
                  f"{str(case.needs_human).lower()}\n  reply: {raw[:110]}" + ("..." if len(raw) > 110 else ""))


# Module 1, lesson 3: targets before training

@command("score", "score a system on evaluation cases", arg("system"), split_arg(),
         arg("--by", choices=["slice"], help="one line per slice"))
def cmd_score(args):
    from .cases import load_cases
    from .predictions import load_predictions
    from .scoring import by_slice, score

    cases = load_cases(splits_of(args))
    preds = load_predictions(args.system)
    print(f"{args.system} on {args.split}: {score(cases, preds).line()}")
    if args.by:
        for name, s in by_slice(cases, preds).items():
            print(f"  {name:13s} {s.line()}")


@command("targets", "check a system against targets.toml", arg("system"), split_arg())
def cmd_targets(args):
    from .cases import load_cases
    from .predictions import load_predictions
    from .scoring import score
    from .targets import check, load_targets

    s = score(load_cases(splits_of(args)), load_predictions(args.system))
    rows = check(s, load_targets())
    print(f"{args.system} on {args.split} against targets.toml:")
    for name, target, measured, met in rows:
        print(f"  {'met    ' if met else 'NOT MET'}  {name:27s} target {target:8s} measured {measured}")
    print(f"{sum(r[3] for r in rows)} of {len(rows)} targets met")


# Module 2, lesson 1: training examples and where they come from

@command("sources", "where each data file comes from and what it may be used for")
def cmd_sources(args):
    from .records import sources

    for name, s in sources().items():
        print(f"{name}: {s['file']}\n  {s['what']}\n  licence {s['licence']}; permitted use: {s['permitted_use']}")


@command("record", "show one training ticket as a training example", arg("ticket_id"))
def cmd_record(args):
    import json

    from .records import load_source, to_record

    row = next((r for r in load_source() if r["id"] == args.ticket_id), None)
    if row is None:
        raise SystemExit(f"No training ticket {args.ticket_id}")
    print(json.dumps(to_record(row), indent=1, ensure_ascii=False))


# Module 2, lesson 3: clean, split, check for leakage

def describe_uncovered(missing: list[str]) -> str:
    """["French", "H2", "H3", "H4", "H5"] -> "French tickets, and needs-a-person rules H2 to H5"."""
    nums = [int(x[1:]) for x in missing if x.startswith("H")]
    runs = []
    for n in nums:
        if runs and n == runs[-1][1] + 1:
            runs[-1][1] = n
        else:
            runs.append([n, n])
    words = [w for a, b in runs for w in ([f"H{a} to H{b}"] if b > a + 1 else [f"H{n}" for n in range(a, b + 1)])]
    rules = " and ".join([", ".join(words[:-1]), words[-1]] if len(words) > 1 else words)
    parts = (["French tickets"] if "French" in missing else []) + (
        [f"needs-a-person rule{'s' if len(nums) > 1 else ''} {rules}"] if nums else [])
    return ", and ".join(parts) if parts else "nothing (French and every rule have a record)"


@command("prepare", "clean the training tickets and write data/prepared/",
         arg("--per-team", type=int, default=200, help="records per team before the split (0 = all)"),
         arg("--extra", help="a JSONL file of extra records to add before cleaning"),
         arg("--show", type=int, default=3, help="rejected records to show for each reason"))
def cmd_prepare(args):
    from .prepare import prepare

    m = prepare(per_team=args.per_team or None, extra=Path(args.extra) if args.extra else None)
    print(f"{m['source_records']} source records")
    for reason, n in m["rejected"].items():
        print(f"  rejected {n:3d}  {reason}")
        rows = [r for r in m["rejected_rows"] if r["reason"] == reason]
        rows.sort(key=lambda r: r["source"] == "tickets")  # extra records first
        for r in rows[:args.show]:
            print(f"               {r['id']}: {r['detail']}")
    print(f"{m['clean_records']} clean records")
    for part in ("train", "val"):
        p = m[part]
        teams = ", ".join(f"{k} {v}" for k, v in p["teams"].items())
        print(f"{part:5s} {p['records']:4d} records  ({teams}; needs a person {p['needs_human']})")
    print(f"Not covered by any training record: {describe_uncovered(m['uncovered'])}")
    print("Wrote data/prepared/train.jsonl, val.jsonl, rejected.jsonl and manifest.json")


# Module 3, lesson 1: what each method trains

@command("params", "count trainable parameters for full tuning and LoRA (no download)",
         arg("--rank", type=int, nargs="*", default=[4, 8, 16, 64]),
         arg("--targets", nargs="*", default=["q_proj", "v_proj"]))
def cmd_params(args):
    from .params import load_config, shapes, table

    config = load_config()
    print(f"SmolLM2-135M-Instruct: {config['num_hidden_layers']} blocks, hidden size {config['hidden_size']}")
    print("Linear layers in one block (out x in): "
          + ", ".join(f"{k} {o}x{i}" for k, (o, i) in shapes(config).items()))
    print(f"{'method':42s} {'trainable':>12s} {'share':>8s} {'file (MB)':>10s}")
    for method, n, share, mb in table(config, tuple(args.rank), tuple(args.targets)):
        print(f"{method:42s} {n:12,d} {100 * share:7.2f}% {mb:10.1f}")


# Module 3, lesson 2: memory before you train

@command("memory", "estimate training memory for four methods and four model sizes")
def cmd_memory(args):
    from .memory import BUDGETS, METHODS, MODELS, estimate_gb, fits

    print("ESTIMATE: weights + gradients + AdamW states. Activations are not included (measure them).")
    print(f"{'model':14s} {'method':28s} {'GB':>8s}  " + "  ".join(f"{b:>12s}" for b in BUDGETS))
    for model, n in MODELS.items():
        for method in METHODS:
            gb = estimate_gb(n, method)
            ok = ["fits" if fits(gb, b) else "no" for b in BUDGETS.values()]
            print(f"{model:14s} {method:28s} {gb:8.2f}  " + "  ".join(f"{x:>12s}" for x in ok))
    print("fits = the estimate uses at most 70% of the memory (the rest: activations, the system).")
    print("QLoRA needs a GPU library (bitsandbytes); on a laptop CPU it is not an option.")


# Module 4, lesson 1: plan and configure the run

@command("download", "download the base model's weights at the pinned revision (about 270 MB)")
def cmd_download(args):
    from .model import MODEL_ID, REVISION, download

    folder = download()
    size = sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
    print(f"{MODEL_ID} at revision {REVISION[:12]}: {size / 1e6:.0f} MB in {folder}")


@command("plan", "show the steps, checkpoints and validations of a run before it starts", arg("config"))
def cmd_plan(args):
    from .config import load_config, plan

    cfg = load_config(args.config)
    p = plan(cfg)
    print(f"{cfg.name}: {p['train_records']} training records, {p['val_records']} validation records")
    print(f"  batch {cfg.batch_size}, {cfg.epochs} epochs = {p['steps_per_epoch']} steps per epoch, "
          f"{p['steps']} steps ({p['examples_seen']} examples seen)")
    print(f"  validation loss every {cfg.eval_every} steps ({p['validations']} times), "
          f"checkpoint every {cfg.checkpoint_every} steps ({p['checkpoints']})")
    print(f"  LoRA rank {cfg.rank}, alpha {cfg.alpha}, dropout {cfg.dropout}, on {', '.join(cfg.targets)}; "
          f"learning rate {cfg.learning_rate}; at most {cfg.max_tokens} tokens per example; {cfg.threads} threads")


# Module 4, lesson 3: train, monitor and recover

@command("train", "train a LoRA adapter (CPU)", arg("config"),
         arg("--resume", action="store_true", help="continue from the newest checkpoint"),
         arg("--stop-after", type=int, help="stop after this step (to practise a resume)"))
def cmd_train(args):
    from .config import load_config
    from .train import train

    train(load_config(args.config), resume=args.resume, stop_after=args.stop_after)


@command("curves", "show a run's training and validation loss", arg("run", help="a folder in runs/"),
         arg("--every", type=int, default=25, help="steps per line"))
def cmd_curves(args):
    import json

    run = ROOT / "runs" / args.run if not Path(args.run).exists() else Path(args.run)
    rows = [json.loads(x) for x in (run / "log.jsonl").read_text(encoding="utf-8").splitlines()]
    train_rows = [r for r in rows if "train_loss" in r]
    vals = {r["step"]: r["val_loss"] for r in rows if "val_loss" in r}
    best = min(vals, key=vals.get) if vals else None
    print(f"{'step':>5s} {'epoch':>6s} {'train loss':>11s} {'validation':>11s}")
    for i in range(0, len(train_rows), args.every):
        window = train_rows[i:i + args.every]
        step = window[-1]["step"]
        mean = sum(r["train_loss"] for r in window) / len(window)
        v = vals.get(step)
        mark = "  <- lowest validation loss" if step == best else ""
        print(f"{step:5d} {window[-1]['epoch']:6.2f} {mean:11.4f} {'' if v is None else f'{v:11.4f}'}{mark}")
    print("train loss = the mean over the steps of each line; validation = at that step")


# Module 5, lesson 1: compare on the same held-out cases

@command("predict", "run a local system on evaluation cases and save its replies", arg("system"), split_arg(),
         arg("--adapter", help="the adapter folder (system adapter)"), arg("--name", help="save under this name"),
         arg("--limit", type=int), arg("--merge", action="store_true", help="merge the adapter into the weights"))
def cmd_predict(args):
    from .predict import run

    splits_of(args)
    run(args.system, args.split, Path(args.adapter) if args.adapter else None, args.name, args.limit,
        merge=args.merge)


@command("compare", "compare every saved system on the same cases", split_arg(),
         arg("--by", choices=["slice"], help="decisions per slice"),
         arg("--systems", nargs="*", help="only these systems"))
def cmd_compare(args):
    from .cases import load_cases
    from .predictions import load_predictions, systems
    from .scoring import by_slice, score

    cases = load_cases(splits_of(args))
    names = args.systems or list(systems())
    print(f"{len(cases)} cases ({args.split})")
    print(f"{'system':14s} {'answers':>8s} {'team':>8s} {'caught':>7s} {'false':>6s} {'decisions':>10s} "
          f"{'s/answer':>9s}")
    for name in names:
        p = load_predictions(name)
        s = score(cases, p)
        print(f"{name:14s} {s.answers:4d}/{s.cases:<3d} {s.team_right:4d}/{s.team_cases:<3d} "
              f"{s.caught:3d}/{s.needs_person:<3d} {s.false_alarms:6d} {s.decisions:6d}/{s.cases:<3d} "
              f"{s.median_seconds:9.3f}")
        if args.by:
            for sl, t in by_slice(cases, p).items():
                print(f"    {sl:13s} decisions {t.decisions}/{t.cases}")
    print("caught = needs a person, sent to one; false = sent to a person without a rule; s/answer = median")


# Module 5, lesson 2: regressions and operational value

@command("regressions", "check general questions: the base model vs each adapter",
         arg("--run", choices=["base", "adapter"], help="ask again with the model instead of the saved replies"),
         arg("--adapter", default=str(ROOT / "runs/lora-r8-long/adapter")),
         arg("--name", help="save the replies under this name (default: base, or the adapter's run name)"))
def cmd_regressions(args):
    import json

    from .regressions import ask, load_prompts, summary

    prompts = load_prompts()
    saved = ROOT / "runs/general"
    if args.run:
        from .model import load_adapted, load_model, load_tokenizer, set_threads

        set_threads(2)
        model = load_adapted(Path(args.adapter)) if args.run == "adapter" else load_model()
        rows = ask(model, load_tokenizer(), prompts)
        saved.mkdir(parents=True, exist_ok=True)
        name = args.name or ("base" if args.run == "base" else Path(args.adapter).parent.name)
        (saved / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    for path in sorted(saved.glob("*.jsonl"), key=lambda p: (p.stem != "base", p.stem)):
        name = path.stem
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
        s = summary(rows, prompts)
        print(f"{name:8s} right {s['right']:2d}/{s['questions']}   "
              f"replied with ticket JSON {s['ticket_json']:2d}/{s['questions']}")
        for r in rows[:3]:
            print(f"         {r['id']}: {r['reply'][:70]!r}")


@command("cost", "compare running costs: the hosted model, the local adapter, a hosted fine-tune",
         arg("--tickets-per-day", type=int, default=822))
def cmd_cost(args):
    from .costs import report

    for line in report(args.tickets_per_day):
        print(line)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m adapt", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (func, help_text, arguments) in COMMANDS.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        for names, options in arguments:
            p.add_argument(*names, **options)
        p.set_defaults(func=func)
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
