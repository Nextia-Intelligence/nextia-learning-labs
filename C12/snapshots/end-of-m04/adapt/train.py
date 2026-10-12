"""Train a LoRA adapter on the CPU, with validation, checkpoints and resume (Module 4).

    python -m adapt train configs/lora-r8.toml [--resume] [--stop-after STEPS]

What it writes in runs/<name>/:
- log.jsonl       one line per step (training loss, seconds) and per validation (validation loss)
- checkpoints/    step-NNNNN/: the adapter, the optimizer and the random state, so that a stopped run
                  resumes exactly where it stopped (only the newest ones are kept)
- best/           the adapter with the lowest validation loss so far
- adapter/        the adapter after the last step
- summary.json    the configuration, the time, the peak memory, the parameter counts and the sizes

The loss is computed on the answer only (the JSON and the end mark), not on the instruction or the ticket:
the model must learn to answer, not to write tickets.
"""

import json
import math
import platform
import random
import shutil
import time
from pathlib import Path

from .config import RunConfig
from .model import peak_memory_mb, tokenizer_sha256

ROOT = Path(__file__).resolve().parents[1]
END = "<|im_end|>"


def encode(tokenizer, record: dict, max_tokens: int) -> tuple[list[int], list[int]]:
    """Token IDs and labels for one record; labels are -100 (ignored) except on the answer."""
    system, user, assistant = record["messages"]
    answer = tokenizer(assistant["content"] + END, add_special_tokens=False).input_ids

    def prompt_ids(text: str) -> list[int]:
        msgs = [system, {"role": "user", "content": text}]
        return tokenizer(tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True),
                         add_special_tokens=False).input_ids

    prompt = prompt_ids(user["content"])
    if len(prompt) + len(answer) > max_tokens:
        room = max_tokens - len(answer) - len(prompt_ids(""))
        text_ids = tokenizer(user["content"], add_special_tokens=False).input_ids[:max(room, 0)]
        prompt = prompt_ids(tokenizer.decode(text_ids))[: max_tokens - len(answer)]
    return prompt + answer, [-100] * len(prompt) + answer


def batches(n: int, batch_size: int, seed: int, epoch: int) -> list[list[int]]:
    order = list(range(n))
    random.Random(seed * 1000 + epoch).shuffle(order)
    return [order[i:i + batch_size] for i in range(0, n, batch_size)]


def collate(items, pad_id: int):
    import torch

    width = max(len(ids) for ids, _ in items)
    ids = torch.tensor([x + [pad_id] * (width - len(x)) for x, _ in items])
    labels = torch.tensor([y + [-100] * (width - len(y)) for _, y in items])
    mask = torch.tensor([[1] * len(x) + [0] * (width - len(x)) for x, _ in items])
    return ids, labels, mask


def answer_loss(model, ids, labels, mask, reduction: str = "mean"):
    """Cross-entropy on the answer tokens only. The model's output layer runs only where it is needed."""
    import torch.nn.functional as F

    core = model.get_base_model() if hasattr(model, "get_base_model") else model
    hidden = core.model(input_ids=ids, attention_mask=mask).last_hidden_state
    target = labels[:, 1:]
    keep = target != -100
    logits = core.lm_head(hidden[:, :-1][keep])
    return F.cross_entropy(logits.float(), target[keep], reduction=reduction), int(keep.sum())


def validation_loss(model, encoded, pad_id: int, batch_size: int = 16) -> float:
    import torch

    model.eval()
    total, tokens = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(encoded), batch_size):
            loss, n = answer_loss(model, *collate(encoded[i:i + batch_size], pad_id), reduction="sum")
            total, tokens = total + float(loss), tokens + n
    model.train()
    return total / tokens


def read_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def checkpoints(run_dir: Path) -> list[Path]:
    return sorted((run_dir / "checkpoints").glob("step-*"))


def library_versions() -> dict:
    import peft
    import torch
    import transformers

    return {"python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "peft": peft.__version__}


def save_adapter(model, folder: Path) -> None:
    """The adapter's weights and config only (peft also writes an empty model card: removed)."""
    model.save_pretrained(folder)
    (Path(folder) / "README.md").unlink(missing_ok=True)


def dir_bytes(folder: Path) -> int:
    return sum(p.stat().st_size for p in Path(folder).rglob("*") if p.is_file())


def train(cfg: RunConfig, root: Path = ROOT, resume: bool = False, stop_after: int | None = None,
          base_model=None, tokenizer=None, runs_dir: Path | None = None, say=print) -> dict:
    """Runs (or resumes) one training run and returns its summary. base_model/tokenizer: for tests."""
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model

    from .model import load_model, load_tokenizer

    torch.set_num_threads(cfg.threads)
    run_dir = (runs_dir or root / "runs") / cfg.name
    if run_dir.exists() and not resume:
        raise SystemExit(f"{run_dir} exists. Use --resume to continue it, or delete it to start again.")
    run_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = tokenizer or load_tokenizer()
    pad_id = tokenizer.pad_token_id

    train_records = read_records(root / cfg.train)[: cfg.train_limit or None]
    train_enc = [encode(tokenizer, r, cfg.max_tokens) for r in train_records]
    val_enc = [encode(tokenizer, r, cfg.max_tokens) for r in read_records(root / cfg.val)]
    per_epoch = math.ceil(len(train_enc) / cfg.batch_size)
    total_steps = per_epoch * cfg.epochs

    torch.manual_seed(cfg.seed)
    model = base_model if base_model is not None else load_model()
    if cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    found = checkpoints(run_dir) if resume else []
    start_step, best = 0, (math.inf, 0)
    if found:
        last = found[-1]
        model = PeftModel.from_pretrained(model, str(last / "adapter"), is_trainable=True)
        state = torch.load(last / "state.pt", weights_only=False)
        start_step, best = state["step"], tuple(state["best"])
        say(f"Resuming {cfg.name} from {last.name} (step {start_step} of {total_steps}).")
    else:
        lora = LoraConfig(r=cfg.rank, lora_alpha=cfg.alpha, lora_dropout=cfg.dropout,
                          target_modules=list(cfg.targets), task_type="CAUSAL_LM")
        model = get_peft_model(model, lora)
        state = None
        (run_dir / "log.jsonl").write_text("", encoding="utf-8")
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=cfg.learning_rate)
    if state:
        optimizer.load_state_dict(state["optimizer"])
        torch.set_rng_state(state["torch_rng"])
        lines = (run_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
        kept = [ln for ln in lines if json.loads(ln)["step"] <= start_step]
        (run_dir / "log.jsonl").write_text("".join(ln + "\n" for ln in kept), encoding="utf-8")

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    say(f"Training {cfg.name}: {len(train_enc)} records, {total_steps} steps, "
        f"{trainable:,} of {total:,} parameters trainable ({100 * trainable / total:.2f}%).")

    def log(row: dict) -> None:
        with open(run_dir / "log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def save_checkpoint(step: int) -> None:
        folder = run_dir / "checkpoints" / f"step-{step:05d}"
        save_adapter(model, folder / "adapter")
        torch.save({"step": step, "best": list(best), "optimizer": optimizer.state_dict(),
                    "torch_rng": torch.get_rng_state()}, folder / "state.pt")
        for old in checkpoints(run_dir)[:-cfg.keep_checkpoints]:
            shutil.rmtree(old)

    model.train()
    step, started = start_step, time.time()
    stopped = False
    for epoch in range(start_step // per_epoch, cfg.epochs):
        for b, idx in enumerate(batches(len(train_enc), cfg.batch_size, cfg.seed, epoch)):
            if epoch * per_epoch + b < step:
                continue  # done before the checkpoint
            t0 = time.time()
            loss, _ = answer_loss(model, *collate([train_enc[i] for i in idx], pad_id))
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            step += 1
            log({"step": step, "epoch": round(step / per_epoch, 3), "train_loss": round(float(loss), 4),
                 "seconds": round(time.time() - t0, 3)})
            if step % cfg.eval_every == 0 or step == total_steps:
                vl = validation_loss(model, val_enc, pad_id)
                log({"step": step, "val_loss": round(vl, 4), "peak_mb": peak_memory_mb()})
                say(f"step {step:4d}/{total_steps}  train loss {float(loss):.4f}  validation loss {vl:.4f}")
                if vl < best[0]:
                    best = (vl, step)
                    save_adapter(model, run_dir / "best")
            if step % cfg.checkpoint_every == 0 or step == total_steps:
                save_checkpoint(step)
            if stop_after is not None and step >= stop_after and step < total_steps:
                if step % cfg.checkpoint_every:
                    save_checkpoint(step)
                say(f"Stopped after step {step} (as asked). Resume with --resume.")
                stopped = True
                break
        if stopped:
            break

    if stopped:
        return {"stopped_at": step}
    save_adapter(model, run_dir / "adapter")
    rows = [json.loads(ln) for ln in (run_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()]
    vals = [r for r in rows if "val_loss" in r]
    summary = {
        "name": cfg.name, "config": cfg.as_dict(), "steps": total_steps,
        "train_records": len(train_enc), "val_records": len(val_enc),
        "train_tokens": sum(len(ids) for ids, _ in train_enc) * cfg.epochs,
        "trainable_parameters": trainable, "all_parameters": total,
        "adapter_bytes": dir_bytes(run_dir / "adapter"),
        "train_seconds": round(sum(r.get("seconds", 0) for r in rows), 1),
        "wall_seconds_this_session": round(time.time() - started, 1),
        "peak_mb": peak_memory_mb(),
        "first_val_loss": vals[0]["val_loss"] if vals else None,
        "best_val_loss": round(best[0], 4), "best_step": best[1],
        "final_val_loss": vals[-1]["val_loss"] if vals else None,
        "tokenizer_sha256": tokenizer_sha256(), "versions": library_versions(),
        "machine": f"{platform.system()} {platform.machine()}",
        "resumed": bool(found),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    say(f"Done: best validation loss {summary['best_val_loss']} at step {summary['best_step']}; "
        f"adapter {summary['adapter_bytes'] / 1e6:.1f} MB in {run_dir / 'adapter'}")
    return summary
