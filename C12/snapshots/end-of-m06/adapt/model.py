"""The base model at one pinned revision, its tokenizer, and the adapter (Module 4).

The tokenizer and config are in model/ (small files from the same revision). Only the weights are
downloaded, once, into the Hugging Face cache (python -m adapt download).
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
WEIGHTS = ("config.json", "generation_config.json", "model.safetensors")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tokenizer_sha256() -> str:
    return file_sha256(MODEL_DIR / "tokenizer.json")


def set_threads(threads: int) -> None:
    import torch

    torch.set_num_threads(threads)


def load_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_DIR)


def download() -> Path:
    """Gets the weights at the pinned revision (about 270 MB) and checks the config against model/."""
    from huggingface_hub import snapshot_download

    folder = Path(snapshot_download(MODEL_ID, revision=REVISION, allow_patterns=list(WEIGHTS)))
    ours = json.loads((MODEL_DIR / "config.json").read_text(encoding="utf-8"))
    theirs = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    if ours != theirs:
        raise SystemExit("The downloaded config.json differs from model/config.json: wrong revision?")
    return folder


def load_model(dtype: str = "float32"):
    """The base model in evaluation mode, from the cache (download it first)."""
    import torch
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION, dtype=getattr(torch, dtype),
                                                 attn_implementation="sdpa")
    model.eval()
    return model


def load_adapted(adapter_dir: Path, merge: bool = False):
    """The base model with a LoRA adapter on top; merge=True folds the adapter into the weights."""
    from peft import PeftModel

    model = PeftModel.from_pretrained(load_model(), str(adapter_dir))
    if merge:
        model = model.merge_and_unload()
    model.eval()
    return model


def peak_memory_mb() -> float | None:
    """The process's peak memory so far, in MB (None on Windows)."""
    try:
        import resource
        import sys
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / 1e6 if sys.platform == "darwin" else peak / 1e3, 1)
