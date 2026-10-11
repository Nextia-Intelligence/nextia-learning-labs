"""A training run's settings, in one TOML file under configs/ (Module 4).

Every setting that changes the result is in the file, so the file IS the record of the run.
"""

import math
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RunConfig:
    name: str
    seed: int
    threads: int
    train: str
    val: str
    max_tokens: int
    rank: int
    alpha: int
    dropout: float
    targets: tuple[str, ...]
    learning_rate: float
    batch_size: int
    epochs: int
    eval_every: int
    checkpoint_every: int
    gradient_checkpointing: bool
    keep_checkpoints: int = 2
    train_limit: int = 0  # 0 = every training record; N = the first N (a small-data experiment)
    notes: str = ""
    path: str = field(default="", compare=False)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["targets"] = list(self.targets)
        d.pop("path")
        return d


def load_config(path) -> RunConfig:
    path = Path(path)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    data, lora, train = raw["data"], raw["lora"], raw["train"]
    cfg = RunConfig(
        name=raw["name"], seed=raw["seed"], threads=raw.get("threads", 2), notes=raw.get("notes", ""),
        train=data["train"], val=data["val"], max_tokens=data["max_tokens"], train_limit=data.get("train_limit", 0),
        rank=lora["rank"], alpha=lora["alpha"], dropout=lora["dropout"], targets=tuple(lora["targets"]),
        learning_rate=train["learning_rate"], batch_size=train["batch_size"], epochs=train["epochs"],
        eval_every=train["eval_every"], checkpoint_every=train["checkpoint_every"],
        gradient_checkpointing=train["gradient_checkpointing"], keep_checkpoints=train.get("keep_checkpoints", 2),
        path=str(path),
    )
    problems = []
    if cfg.rank < 1 or cfg.batch_size < 1 or cfg.epochs < 1:
        problems.append("rank, batch_size and epochs must be at least 1")
    if not 0 < cfg.learning_rate < 1:
        problems.append("learning_rate must be between 0 and 1")
    if cfg.max_tokens < 64:
        problems.append("max_tokens must be at least 64 (the instruction alone takes about 60)")
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return cfg


def count_lines(path: Path) -> int:
    return sum(1 for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())


def plan(cfg: RunConfig, root: Path = ROOT) -> dict:
    """Steps, checkpoints and validation points of a run, before it starts."""
    n_train, n_val = count_lines(root / cfg.train), count_lines(root / cfg.val)
    if cfg.train_limit:
        n_train = min(n_train, cfg.train_limit)
    per_epoch = math.ceil(n_train / cfg.batch_size)
    steps = per_epoch * cfg.epochs
    return {"train_records": n_train, "val_records": n_val, "steps_per_epoch": per_epoch, "steps": steps,
            "validations": steps // cfg.eval_every, "checkpoints": steps // cfg.checkpoint_every,
            "examples_seen": steps * cfg.batch_size}
