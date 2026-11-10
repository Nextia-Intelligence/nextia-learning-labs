"""A language model for the unsure pairs only (Module 6, lesson 4).

The course data has recorded answers from a small chat model (Azure chat-small) for every unsure pair of the
validation and test splits (data/recorded/llm_pairs.jsonl), so you need no key. A live mode is possible with
your own key (see `ask_live`); it is not needed for any lesson.

The model is never the only judge: its answer decides only pairs in the unsure band, and Module 8 sends its
"same" answers to a person when a merge would join two existing customers.
"""

import json
import os

from . import data
from .paths import data_dir

LOWER, UPPER = 0.1, 0.9   # the unsure band of calibrated probabilities (our choice)

SYSTEM = ("You compare customer records of a home and garden shop. Decide if two records describe the same person. "
          "Records come from different systems, so names, addresses, phone numbers and dates can be written in "
          "different ways, have typing errors or be missing. People in one family often share an address, a phone "
          "number and an email; that alone does not make them the same person. People move, so a different address "
          "alone does not make them different. Answer only with JSON: "
          "{\"answer\": \"same\" | \"different\" | \"unsure\", \"reason\": \"<one short sentence>\"}.")
PRODUCT_SYSTEM = ("You compare product listings from two suppliers of a home and garden shop. Decide if two listings "
                  "are the same product (same brand, type, size, material, colour and pack size). Units can be "
                  "written differently (50 ft is about 15.2 m). A pack of 2 is a different product from one item. "
                  "Answer only with JSON: {\"answer\": \"same\" | \"different\" | \"unsure\", \"reason\": "
                  "\"<one short sentence>\"}.")
FIELDS = ["name", "email", "phone", "address", "postcode", "date_of_birth"]


def describe(record_id, dataset="customers"):
    if dataset == "products":
        f = data.feed("a" if record_id.startswith("NF") else "b").set_index("product_id").loc[record_id]
        return f"title: {f['title']}\nprice: {f['price']}\nbarcode: {f['gtin'] or '(none)'}"
    r = data.records().set_index("record_id").loc[record_id]
    return "\n".join(f"{k}: {r[k] if r[k] else '(missing)'}" for k in FIELDS)


def messages(record_l, record_r, dataset="customers"):
    return [{"role": "system", "content": PRODUCT_SYSTEM if dataset == "products" else SYSTEM},
            {"role": "user", "content": f"Record A\n{describe(record_l, dataset)}\n\nRecord B\n"
                                        f"{describe(record_r, dataset)}\n\nAre A and B the same?"}]


def parse_answer(text):
    """The answer word from the model's text ('same', 'different' or 'unsure'); 'unsure' when it cannot be read."""
    try:
        a = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip()).get("answer", "")
    except (json.JSONDecodeError, AttributeError):
        a = ""
    return a if a in ("same", "different", "unsure") else "unsure"


def recorded(dataset="customers"):
    """(record_id_l, record_id_r) -> the recorded answer row."""
    name = "llm_products.jsonl" if dataset == "products" else "llm_pairs.jsonl"
    p = data_dir() / "recorded" / name
    if not p.exists():
        return {}
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return {(r["record_id_l"], r["record_id_r"]): r for r in rows}


def ask_live(record_l, record_r, dataset="customers"):
    """Ask a model yourself: set LARKFIELD_LLM_BASE_URL, LARKFIELD_LLM_API_KEY and LARKFIELD_LLM_MODEL
    (any service with an OpenAI-compatible chat API), and pip install openai."""
    from openai import OpenAI
    c = OpenAI(base_url=os.environ["LARKFIELD_LLM_BASE_URL"], api_key=os.environ["LARKFIELD_LLM_API_KEY"])
    r = c.chat.completions.create(model=os.environ["LARKFIELD_LLM_MODEL"], messages=messages(record_l, record_r, dataset))
    text = r.choices[0].message.content
    return {"answer": parse_answer(text), "text": text}
