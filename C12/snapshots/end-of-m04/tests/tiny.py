"""A tiny random model with the real tokenizer, so that the training code can be tested in seconds."""

import json
import shutil
from pathlib import Path

from adapt.records import messages

ROOT = Path(__file__).resolve().parents[1]


def tiny_model(seed: int = 0):
    import torch
    from transformers import LlamaConfig, LlamaForCausalLM

    torch.manual_seed(seed)
    config = LlamaConfig(vocab_size=49152, hidden_size=16, intermediate_size=32, num_hidden_layers=2,
                         num_attention_heads=2, num_key_value_heads=1, max_position_embeddings=512,
                         tie_word_embeddings=True, pad_token_id=2, bos_token_id=1, eos_token_id=2)
    return LlamaForCausalLM(config)


def tiny_project(tmp: Path, records: int = 24) -> Path:
    """A project folder with a few training and validation records and a short config."""
    (tmp / "data").mkdir(parents=True)
    rows = [json.dumps({"id": f"R-{i}", "messages": messages(f"ticket number {i} about my order",
                                                             ["delivery", "payment"][i % 2], i % 5 == 0)})
            for i in range(records)]
    (tmp / "data/train.jsonl").write_text("\n".join(rows[: records - 4]) + "\n")
    (tmp / "data/val.jsonl").write_text("\n".join(rows[records - 4:]) + "\n")
    shutil.copytree(ROOT / "model", tmp / "model")
    (tmp / "tiny.toml").write_text("""name = "tiny"
seed = 1
threads = 1
[data]
train = "data/train.jsonl"
val = "data/val.jsonl"
max_tokens = 128
[lora]
rank = 2
alpha = 4
dropout = 0.1
targets = ["q_proj", "v_proj"]
[train]
learning_rate = 1e-3
batch_size = 4
epochs = 2
eval_every = 2
checkpoint_every = 2
gradient_checkpointing = false
""")
    return tmp
