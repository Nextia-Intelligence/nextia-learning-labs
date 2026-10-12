"""Count what each method trains, from the model's config.json alone (Module 3). No download needed.

A LoRA adapter on one weight matrix of shape (out, in) adds two small matrices: A (rank x in) and
B (out x rank). It trains rank x (in + out) numbers instead of out x in.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEAR = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


def shapes(config: dict) -> dict[str, tuple[int, int]]:
    """(out, in) of each linear layer in one block of a Llama-style model."""
    h, i = config["hidden_size"], config["intermediate_size"]
    head = h // config["num_attention_heads"]
    kv = config["num_key_value_heads"] * head
    return {"q_proj": (h, h), "k_proj": (kv, h), "v_proj": (kv, h), "o_proj": (h, h),
            "gate_proj": (i, h), "up_proj": (i, h), "down_proj": (h, i)}


def total_params(config: dict) -> int:
    h, layers, vocab = config["hidden_size"], config["num_hidden_layers"], config["vocab_size"]
    block = sum(o * i for o, i in shapes(config).values()) + 2 * h  # two RMSNorm weight vectors
    embed = vocab * h
    head = 0 if config.get("tie_word_embeddings") else vocab * h
    return embed + layers * block + h + head


def lora_params(config: dict, rank: int, targets=("q_proj", "v_proj")) -> int:
    per_block = sum(rank * (i + o) for name, (o, i) in shapes(config).items() if name in targets)
    return config["num_hidden_layers"] * per_block


def load_config(path: Path = ROOT / "model/config.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def table(config: dict, ranks=(4, 8, 16, 64), targets=("q_proj", "v_proj")) -> list[tuple[str, int, float, float]]:
    """(method, trainable parameters, share of all, adapter file MB in float32)."""
    total = total_params(config)
    rows = [("full fine-tuning", total, 1.0, total * 4 / 1e6)]
    for r in ranks:
        n = lora_params(config, r, targets)
        rows.append((f"LoRA rank {r} on {', '.join(targets)}", n, n / total, n * 4 / 1e6))
    n = lora_params(config, 8, LINEAR)
    rows.append(("LoRA rank 8 on all 7 linear layers", n, n / total, n * 4 / 1e6))
    return rows
