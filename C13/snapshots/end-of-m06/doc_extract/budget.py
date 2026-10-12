"""Operational constraints: what a page costs in time, money, tokens and storage, per path.

    python -m doc_extract.budget                                  # measured on this computer
    python -m doc_extract.budget --pages 300 --model-share 0.25   # a day of 300 pages

Time is measured now on a small sample (the text layer and OCR run on your CPU). The vision
model's tokens and time come from the course's recorded calls, and its cost from the list price
(prices.py). Retries and the share of pages that need the model are your assumptions: the command
prints them as assumptions.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time

from doc_extract import documents, ocr, prices, textlayer, vision

SAMPLE = ["D011", "D036", "D021", "D029", "D040", "D017"]


def measure(sample: list[str] = SAMPLE) -> dict:
    docs = [documents.get(x) for x in sample]
    text_s, ocr_s = [], []
    for d in docs:
        if d.source == "digital_pdf":
            t = time.perf_counter()
            textlayer.read(d.path)
            text_s.append(time.perf_counter() - t)
        t = time.perf_counter()
        ocr.read(d.path, prepare=True, cache=False)
        ocr_s.append(time.perf_counter() - t)
    recs = [json.loads(x) for x in (vision.RECORDINGS / "vision-v2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    v_in = statistics.median(r["tokens_in"] for r in recs)
    v_out = statistics.median(r["tokens_out"] for r in recs)
    v_s = statistics.median(r["seconds"] for r in recs)
    sizes = [d.bytes for d in documents.receipts()]
    return {
        "text_seconds_per_page": round(statistics.median(text_s), 4) if text_s else None,
        "ocr_seconds_per_page": round(statistics.median(ocr_s), 3),
        "vision": {"recorded_calls": len(recs), "tokens_in_median": v_in, "tokens_out_median": v_out,
                   "seconds_median": round(v_s, 2), "usd_per_page": round(prices.cost(v_in, v_out), 5)},
        "original_kb_median": round(statistics.median(sizes) / 1000, 1),
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Cost, time and storage per page and per day.")
    ap.add_argument("--pages", type=int, default=300, help="pages per day (assumption)")
    ap.add_argument("--model-share", type=float, default=0.25, help="share of pages sent to the model (assumption)")
    ap.add_argument("--retry-rate", type=float, default=0.02, help="share of model calls repeated (assumption)")
    args = ap.parse_args(argv)
    m = measure()
    v = m["vision"]
    print("Measured on this computer (sample of", len(SAMPLE), "documents):")
    if m["text_seconds_per_page"] is not None:
        print(f"  text layer   {m['text_seconds_per_page'] * 1000:.0f} ms per page, US$0")
    print(f"  OCR          {m['ocr_seconds_per_page']:.2f} s per page (with preparation), US$0 (your CPU)")
    print(f"From the course's {v['recorded_calls']} recorded vision calls (median):")
    print(f"  vision model {v['seconds_median']} s per page, {v['tokens_in_median']:.0f} tokens in, "
          f"{v['tokens_out_median']:.0f} out = US${v['usd_per_page']:.4f} per page at list price")
    calls = args.pages * args.model_share * (1 + args.retry_rate)
    day_usd = calls * v["usd_per_page"]
    cpu_min = args.pages * m["ocr_seconds_per_page"] / 60
    print(f"\nAssumptions: {args.pages} pages a day, {args.model_share:.0%} of them sent to the model, "
          f"{args.retry_rate:.0%} of model calls repeated")
    print(f"  model calls per day   {calls:.0f}  -> US${day_usd:.2f} a day, about US${day_usd * 30:.0f} a month")
    print(f"  OCR time per day      {cpu_min:.1f} CPU minutes if every page needs OCR")
    print(f"  all pages to the model instead: US${args.pages * (1 + args.retry_rate) * v['usd_per_page']:.2f} a day")
    print(f"  storage: originals about {m['original_kb_median']:.0f} kB each (median); keep them, they are the evidence")


if __name__ == "__main__":
    main()
