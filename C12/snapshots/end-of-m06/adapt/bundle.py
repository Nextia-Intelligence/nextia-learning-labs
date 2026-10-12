"""Package an adapter with everything it depends on, and verify a package (Module 6).

A bundle is a folder:
- adapter/        the LoRA weights and adapter_config.json (it names the base model)
- bundle.json     the base model ID and revision, the tokenizer's SHA-256, the run configuration, the data
                  manifest, the evaluation results, the library versions
- MODEL_CARD.md   what the adapter does, how it was trained and evaluated, its limits
- checks.jsonl    the fixed checks that verify runs
The base model's weights are NOT in the bundle: they are named, by ID and revision.
"""

import json
import shutil
from pathlib import Path

from .answer import parse_answer
from .cases import load_cases, version
from .model import MODEL_ID, REVISION, file_sha256, tokenizer_sha256
from .predictions import load_predictions
from .scoring import score

ROOT = Path(__file__).resolve().parents[1]


def evaluation(system: str = "adapter") -> dict:
    out = {"cases_version": version()}
    for split in ("dev", "holdout"):
        out[split] = score(load_cases((split,)), load_predictions(system)).line()
    return out


def model_card(info: dict) -> str:
    c, s = info["config"], info["training"]
    return f"""# Model card: {info['name']}

A LoRA adapter for **{MODEL_ID}** (revision `{REVISION[:12]}`). It reads one Larkfield support ticket and
answers with one JSON object: `{{"team": ..., "needs_human": ...}}`. It was made in the course
*Fine-Tuning and Adapting AI Models* to learn the method. It is not a production model.

## Training
- Data: {s['train_records']} training and {s['val_records']} validation records made from made-up tickets
  (CC0); manifest `{info['data_manifest']['train']['sha256_12']}` (train). No French tickets, and no
  examples of the needs-a-person rules H2 to H5.
- LoRA rank {c['rank']}, alpha {c['alpha']}, dropout {c['dropout']} on {', '.join(c['targets'])};
  learning rate {c['learning_rate']}, batch {c['batch_size']}, {c['epochs']} epochs, seed {c['seed']}, CPU.
- Trainable parameters: {s['trainable_parameters']:,} of {s['all_parameters']:,}.
- Best validation loss {s['best_val_loss']} at step {s['best_step']}; final {s['final_val_loss']}.

## Evaluation (the evaluation course's cases, version {info['evaluation']['cases_version']})
- dev: {info['evaluation']['dev']}
- holdout: {info['evaluation']['holdout']}

## Use and limits
- Use it only for this task, with the instruction it was trained with. It was not trained or checked for
  anything else (`python -m adapt regressions` asks it 20 general questions).
- Read "needs a person: caught" above before any use: a ticket that needs a person and is not sent to one
  is the failure that matters most. The training data has no French ticket and no example of rules H2 to
  H5: see the evaluation by slice (`python -m adapt compare --by slice`).
- Load it only on the base revision above, with the tokenizer whose SHA-256 is in bundle.json.

## Licences
Base model: Apache-2.0. Training data: CC0 1.0. The adapter is a derived work of the base model.
"""


def make_bundle(run_dir: Path, out: Path, adapter_name: str = "adapter", system: str = "adapter") -> Path:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(run_dir / adapter_name, out / "adapter")
    shutil.copyfile(ROOT / "data/checks.jsonl", out / "checks.jsonl")
    info = {
        "name": summary["name"],
        "base_model": {"id": MODEL_ID, "revision": REVISION,
                       "config_sha256": file_sha256(ROOT / "model/config.json")},
        "tokenizer_sha256": tokenizer_sha256(),
        "config": summary["config"],
        "training": {k: summary[k] for k in ("steps", "train_records", "val_records", "trainable_parameters",
                                             "all_parameters", "best_val_loss", "best_step", "final_val_loss",
                                             "train_seconds", "peak_mb")},
        "data_manifest": json.loads((ROOT / "data/prepared/manifest.json").read_text(encoding="utf-8")),
        "evaluation": evaluation(system),
        "versions": summary["versions"],
    }
    (out / "bundle.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "MODEL_CARD.md").write_text(model_card(info), encoding="utf-8")
    return out


def compatible(info: dict) -> list[str]:
    """The reasons this bundle cannot be loaded here ([] = compatible)."""
    problems = []
    if info["base_model"]["id"] != MODEL_ID or info["base_model"]["revision"] != REVISION:
        problems.append(f"base model {info['base_model']['id']}@{info['base_model']['revision'][:12]} "
                        f"is not {MODEL_ID}@{REVISION[:12]}")
    if info["base_model"]["config_sha256"] != file_sha256(ROOT / "model/config.json"):
        problems.append("the base model's config.json differs")
    if info["tokenizer_sha256"] != tokenizer_sha256():
        problems.append("the tokenizer differs")
    return problems


def verify(bundle: Path, merged: bool = False, base_only: bool = False, say=print) -> bool:
    import torch

    from .model import load_adapted, load_model, load_tokenizer
    from .predict import generate, short_messages

    info = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    problems = compatible(info)
    if problems:
        for p in problems:
            say(f"INCOMPATIBLE: {p}")
        return False
    torch.set_num_threads(2)
    tokenizer = load_tokenizer()
    if base_only:
        model, what = load_model(), "the base model only (rollback)"
    else:
        model = load_adapted(bundle / "adapter", merge=merged)
        what = "base + adapter, merged" if merged else "base + adapter, loaded at runtime"
    checks = [json.loads(x) for x in (bundle / "checks.jsonl").read_text(encoding="utf-8").splitlines()]
    say(f"{info['name']} on {MODEL_ID}@{REVISION[:12]}: {what}")
    passed = 0
    for c in checks:
        raw = generate(model, tokenizer, short_messages(c["text"]))
        answer, problem = parse_answer(raw)
        ok = answer == {"team": c["team"], "needs_human": c["needs_human"]}
        passed += ok
        say(f"  {'pass' if ok else 'FAIL'}  {c['id']}  expected {c['team']}/{str(c['needs_human']).lower()}  "
            f"got {raw.strip()[:60]!r}" + (f" ({problem})" if problem else ""))
    say(f"{passed} of {len(checks)} checks passed")
    return passed == len(checks)
