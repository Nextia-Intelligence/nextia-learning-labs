"""Path 3: a vision model reads the page picture and fills the contract.

    python -m doc_extract.vision D035                # replay the course's recorded answer (no key)
    python -m doc_extract.vision D035 --prompt v1    # the plain first prompt
    python -m doc_extract.vision D035 --live         # call a model yourself (your key, your money)

By default nothing is sent anywhere: the course recorded one real answer per page and prompt
(recordings/vision-*.jsonl), and this module replays it. --live needs an OpenAI-compatible
endpoint that reads images: VISION_BASE_URL, VISION_API_KEY and VISION_MODEL (see .env.example).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import time
from pathlib import Path

from doc_extract import contract
from doc_extract.fields import Extraction, Found

RECORDINGS = Path(__file__).resolve().parents[1] / "recordings"
VISION_DPI = 150  # PDF pages are drawn at this resolution before they are sent
MAX_SIDE = 1600  # longer pictures are made smaller first

PROMPT_V1 = """Extract the data from this receipt as JSON with the keys vendor, order_number, date, currency,
subtotal, shipping, tax, total, payment_method and items (a list of objects with description, quantity,
unit_price and line_total)."""

PROMPT_V2 = """You read one page of a document attached to a support ticket. It should be a receipt.
Fill the JSON schema from what is PRINTED on this page only.

Rules:
- Copy each value as printed into "printed", and write the normalised form into "value":
  dates YYYY-MM-DD; money with 2 decimals, a point and no thousands separator (1 011,78 $ -> 1011.78);
  currency as CAD or USD; payment_method as Visa, Mastercard, Amex, Debit or Cash (no card number).
- French receipts from Quebec print the day first: 09/08/2026 is 2026-08-09.
- tax is the sum of all tax lines (GST, HST, PST, QST, TPS, TVQ).
- order_number is the online order number (LK- and 6 digits). A transaction or invoice number is NOT an
  order number.
- If a value is not printed, is cut off, or you cannot read it, set value and printed to null, status
  "absent", and reason "not_printed", "cut_off" or "unreadable". Never guess, compute or complete a value.
- status "inferred" only for currency, when no currency is printed but the shop's address is in Canada
  (reason: say what you saw).
- confidence: your probability, from 0 to 1, that the value is correct.
- If the page cannot be read at all, set readable to false and every field to absent / unreadable."""

FIELD_NAMES = [f.name for f in contract.RECEIPT]


def schema_v2() -> dict:
    fld = {"type": "object", "additionalProperties": False,
           "properties": {"value": {"type": ["string", "null"]}, "printed": {"type": ["string", "null"]},
                          "status": {"type": "string", "enum": ["found", "inferred", "absent"]},
                          "reason": {"type": ["string", "null"]}, "confidence": {"type": "number"}},
           "required": ["value", "printed", "status", "reason", "confidence"]}
    item = {"type": "object", "additionalProperties": False,
            "properties": {"description": {"type": "string"}, "quantity": {"type": "integer"},
                           "unit_price": {"type": "string"}, "line_total": {"type": "string"}},
            "required": ["description", "quantity", "unit_price", "line_total"]}
    return {"type": "object", "additionalProperties": False,
            "properties": {"readable": {"type": "boolean"},
                           "fields": {"type": "object", "additionalProperties": False,
                                      "properties": {n: fld for n in FIELD_NAMES}, "required": FIELD_NAMES},
                           "items": {"type": "array", "items": item}},
            "required": ["readable", "fields", "items"]}


def picture(path: Path, page: int = 1, crop: bool = False) -> tuple[bytes, tuple[int, int]]:
    """The page as a JPEG to send: drawn at VISION_DPI, cropped to the document if asked, at most
    MAX_SIDE pixels on its longer side."""
    from doc_extract import files

    img = files.page_image(path, page, VISION_DPI)
    if crop:
        from doc_extract.prepare import content_box

        img = img.crop(content_box(img))
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue(), img.size


def request(prompt: str, jpeg: bytes) -> dict:
    """The chat request (without the model name) for one page."""
    url = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    body = {"messages": [{"role": "user", "content": [{"type": "text", "text": prompt},
                                                      {"type": "image_url", "image_url": {"url": url, "detail": "high"}}]}]}
    if prompt is PROMPT_V2:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "receipt", "strict": True, "schema": schema_v2()}}
    else:
        body["response_format"] = {"type": "json_object"}
    return body


def call_live(prompt_version: str, path: Path, page: int = 1, crop: bool = False) -> dict:
    """Send one page to the model now. Returns the answer and its usage (as a recording line)."""
    from openai import OpenAI

    base, key, model = os.environ.get("VISION_BASE_URL"), os.environ.get("VISION_API_KEY"), os.environ.get("VISION_MODEL")
    if not (base and key and model):
        raise SystemExit("A live call needs VISION_BASE_URL, VISION_API_KEY and VISION_MODEL (see .env.example).")
    client = OpenAI(base_url=base, api_key=key, default_headers={"api-key": key}, timeout=120, max_retries=2)
    prompt = PROMPT_V2 if prompt_version == "v2" else PROMPT_V1
    jpeg, size = picture(path, page, crop)
    t = time.perf_counter()
    r = client.chat.completions.create(model=model, **request(prompt, jpeg))
    seconds = time.perf_counter() - t
    text = r.choices[0].message.content or ""
    return {"file": path.name, "page": page, "prompt": prompt_version, "crop": crop, "model": r.model,
            "image_px": list(size), "image_bytes": len(jpeg), "seconds": round(seconds, 3),
            "tokens_in": r.usage.prompt_tokens, "tokens_out": r.usage.completion_tokens, "answer": text}


def recorded(file: str, page: int = 1, prompt: str = "v2", crop: bool = False, variant: str = "") -> dict | None:
    """The course's recorded answer for this page, or None."""
    name = f"vision-{prompt}{'-crop' if crop else ''}{'-' + variant if variant else ''}.jsonl"
    p = RECORDINGS / name
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["file"] == file and r["page"] == page:
            return r
    return None


EMPTY = {None, "", "n/a", "na", "none", "null", "unknown", "not available", "not printed", "-"}


def to_extraction(rec: dict) -> Extraction:
    """Turn a model answer (recorded or live) into the same record as the other paths."""
    out = Extraction(rec["file"], "vision", seconds=rec.get("seconds", 0.0),
                     usage={k: rec.get(k) for k in ("model", "tokens_in", "tokens_out", "image_px", "cost_usd")})
    try:
        answer = json.loads(rec["answer"])
    except (json.JSONDecodeError, TypeError):
        out.notes.append("the answer is not valid JSON")
        answer = {}
    fields = answer.get("fields", answer)  # v2 has "fields"; v1 has the keys at the top
    if answer.get("readable") is False:
        out.notes.append("the model said the page cannot be read")
    for name in FIELD_NAMES:
        v = fields.get(name)
        if isinstance(v, dict):  # v2: value, printed, status, reason, confidence
            value = v.get("value")
            value = None if (value is None or str(value).strip().lower() in EMPTY) else str(value)
            status = v.get("status") or ("found" if value else "absent")
            if value is None:
                status = "absent"
            out.fields[name] = Found(name, value, status, v.get("reason") or "", v.get("printed") or "",
                                     [], rec.get("page", 1), v.get("confidence"))
        else:  # v1: just a value
            value = None if (v is None or str(v).strip().lower() in EMPTY) else str(v)
            out.fields[name] = Found(name, value, "found" if value else "absent", "" if value else "not_given",
                                     str(v) if v is not None else "", [], rec.get("page", 1))
    for it in answer.get("items") or []:
        if isinstance(it, dict):
            out.items.append({k: it.get(k) for k in ("description", "quantity", "unit_price", "line_total")}
                             | {"page": rec.get("page", 1), "lines": []})
    return out


def read(file: str, page: int = 1, prompt: str = "v2", crop: bool = False, variant: str = "") -> Extraction | None:
    rec = recorded(file, page, prompt, crop, variant)
    return to_extraction(rec) if rec else None


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents, prices

    ap = argparse.ArgumentParser(description="The vision-model path: recorded answers, or a live call.")
    ap.add_argument("doc")
    ap.add_argument("--prompt", default="v2", choices=["v1", "v2"])
    ap.add_argument("--page", type=int, default=0, help="the page to read (default: the receipt page)")
    ap.add_argument("--crop", action="store_true", help="send only the document's part of the picture")
    ap.add_argument("--live", action="store_true", help="call the model now (needs your key)")
    args = ap.parse_args(argv)
    d = documents.get(args.doc)
    page = args.page or d.truth.get("receipt_page", 1)
    if args.live:
        rec = call_live(args.prompt, d.path, page, args.crop)
        print("live call")
    else:
        rec = recorded(d.file, page, args.prompt, args.crop)
        if rec is None:
            raise SystemExit(f"No recorded answer for {d.file} page {page} (prompt {args.prompt}). Try --live.")
        print("recorded answer (replayed; nothing was sent)")
    ex = to_extraction(rec)
    cost = prices.cost(rec.get("tokens_in", 0), rec.get("tokens_out", 0), "chat-strong")
    print(f"{d.doc_id} {d.file} page {page}, prompt {args.prompt}: {rec.get('model')}, "
          f"{rec.get('tokens_in')} tokens in, {rec.get('tokens_out')} out, {rec.get('seconds')} s, about US${cost:.4f}")
    for name, f in ex.fields.items():
        conf = f" (confidence {f.confidence})" if f.confidence is not None else ""
        shown = f.value if f.value is not None else f"absent ({f.reason or 'no reason given'})"
        print(f"  {name:<15} {shown}{conf}")
    for it in ex.items:
        print(f"    item: {it['quantity']} x {it['description']} @ {it['unit_price']} = {it['line_total']}")
    for n in ex.notes:
        print(f"  note: {n}")


if __name__ == "__main__":
    main()
