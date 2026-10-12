"""A small regression check: does the model still answer ordinary questions after adaptation? (Module 5)

    python -m adapt regressions                     the saved replies of the base model and the adapter
    python -m adapt regressions --run adapter       ask the questions again (needs the model)
"""

import json
import time
from pathlib import Path

from .answer import parse_answer

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "data/general/prompts.jsonl"


def load_prompts(path: Path = PROMPTS) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_right(reply: str, expected_any: list[str]) -> bool:
    """Right when the reply contains one expected word (case-sensitive only for an all-capitals word)."""
    for word in expected_any:
        if word.isupper() and len(word) > 1:
            if word in reply:
                return True
        elif word.lower() in reply.lower():
            return True
    return False


def looks_like_ticket_json(reply: str) -> bool:
    answer, problem = parse_answer(reply)
    return answer is not None or reply.strip().startswith("{")


def summary(rows: list[dict], prompts: list[dict]) -> dict:
    by_id = {p["id"]: p for p in prompts}
    right = sum(is_right(r["reply"], by_id[r["id"]]["expected_any"]) for r in rows)
    as_json = sum(looks_like_ticket_json(r["reply"]) for r in rows)
    return {"questions": len(rows), "right": right, "ticket_json": as_json}


def ask(model, tokenizer, prompts: list[dict], max_new_tokens: int = 40) -> list[dict]:
    """Asks each question with no system prompt (an ordinary chat), greedy."""
    import torch

    rows = []
    for p in prompts:
        text = tokenizer.apply_chat_template([{"role": "user", "content": p["prompt"]}], tokenize=False,
                                             add_generation_prompt=True)
        ids = torch.tensor([tokenizer(text, add_special_tokens=False).input_ids])
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=max_new_tokens,
                                 do_sample=False, pad_token_id=tokenizer.pad_token_id)
        reply = tokenizer.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
        rows.append({"id": p["id"], "reply": reply, "seconds": round(time.perf_counter() - t0, 4)})
    return rows
