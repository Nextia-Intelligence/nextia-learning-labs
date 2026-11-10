"""A tiny fake shop (no download): 48 products in 4 categories, 80 customers, events over the course's dates."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

SUBS = [("Garden furniture", "Garden chairs", "summer"), ("Garden furniture", "Parasols", "summer"),
        ("Bedding and linen", "Duvets", "autumn"), ("Bedding and linen", "Pillows", "all"),
        ("Pets", "Pet food", "all"), ("Pets", "Dog beds", "all"),
        ("Health and personal care", "Continence care", "all"), ("Bar and wine", "Wine", "gifts")]


def make_data(root):
    rng = np.random.default_rng(1)
    rows = []
    for i in range(48):
        cat, sub, season = SUBS[i % len(SUBS)]
        rows.append({"product_id": f"P{10001 + i}", "title": f"Test {sub} {i}", "description": f"A test {sub.lower()}.",
                     "category": cat, "subcategory": sub, "style": "Nordic" if i % 3 == 0 else "",
                     "range": "", "colour": "grey", "price": float(10 + i), "margin": 0.1 + 0.01 * (i % 20),
                     "added": "2026-05-01" if i >= 44 else "2024-01-01", "season": season,
                     "repeat_days": 30 if sub == "Pet food" else 0, "age_restricted": sub == "Wine",
                     "sensitive": sub == "Continence care", "in_stock": i != 3, "stock": 0 if i == 3 else 10})
    products = pd.DataFrame(rows)
    customers = pd.DataFrame({"customer_id": [f"C{100001 + i}" for i in range(80)],
                              "first_seen": "2025-02-01", "region": "ON",
                              "shared_email": [i % 10 == 0 for i in range(80)], "opted_out": [i == 7 for i in range(80)]})
    ev = []
    days = pd.date_range("2025-02-01", "2026-07-05", freq="D")
    sid = 0
    for c in range(80):
        fav = rng.choice(48, 6, replace=False)
        for _ in range(int(rng.integers(3, 12))):
            sid += 1
            d = days[int(rng.integers(0, len(days)))]
            for j, p in enumerate(rng.choice(fav, 2, replace=False)):
                t = d + pd.Timedelta(hours=12, minutes=j)
                ev.append((t, c, sid, p, "view", 0))
                if rng.random() < 0.6:
                    ev.append((t + pd.Timedelta(seconds=20), c, sid, p, "basket", 0))
                    ev.append((t + pd.Timedelta(seconds=40), c, sid, p, "order", 1))
    events = pd.DataFrame(ev, columns=["t", "c", "s", "p", "event", "quantity"]).sort_values("t")
    events = pd.DataFrame({"timestamp": events.t.dt.strftime("%Y-%m-%d %H:%M:%S"),
                           "customer_id": customers.customer_id.to_numpy()[events.c],
                           "session_id": [f"S{s:07d}" for s in events.s], "product_id": products.product_id.to_numpy()[events.p],
                           "event": events.event, "quantity": events.quantity,
                           "price": np.where(events.event == "order", products.price.to_numpy()[events.p], np.nan)})
    root.mkdir(parents=True, exist_ok=True)
    products.to_csv(root / "products.csv", index=False)
    customers.to_csv(root / "customers.csv", index=False)
    events.to_csv(root / "events.csv.gz", index=False)
    (root / "splits.json").write_text(json.dumps({
        "log_start": "2025-02-01", "launch": ["2026-05-01", "2026-05-14"], "validation": ["2026-06-08", "2026-06-21"],
        "test": ["2026-06-22", "2026-07-05"], "stock_day": "2026-06-15"}))
    (root / "embeddings").mkdir(exist_ok=True)
    emb = rng.normal(size=(48, 8)).astype(np.float32)
    np.save(root / "embeddings" / "products.npy", (emb / np.linalg.norm(emb, axis=1, keepdims=True)).astype(np.float16))
    (root / "online").mkdir(exist_ok=True)
    pd.DataFrame([{"customer_id": f"C{100001 + i}", "arm": ["trending", "als", "two-stage"][i % 3], "visits": 2,
                   "clicks": i % 2, "orders": i % 3 == 0, "revenue_from_suggestions": 10.0 * (i % 3 == 0),
                   "added_revenue": 8.0 * (i % 3 == 0), "returns": 0, "emails": 2, "email_clicks": 0,
                   "unsubscribed": int(i == 5)} for i in range(30)]).to_csv(root / "online" / "ab_test.csv", index=False)
    pd.DataFrame([{"week": w, "week_start": "2026-04-06", "learner": lr, "exploration": s, "visits": 10,
                   "click_rate": 0.1, "orders_per_1000_visits": 20.0, "revenue_per_visit": 1.0,
                   "products_shown_this_week": 10, "products_shown_so_far": 10, "top10_same_as_week1": 10}
                  for lr, s in (("clicks", 0.0), ("ctr", 0.1)) for w in range(1, 13)]).to_csv(
        root / "online" / "feedback_loop.csv", index=False)
    (root / "recorded").mkdir(exist_ok=True)
    test_buyers = events[(events.timestamp >= "2026-06-22") & (events.event == "order")].customer_id.unique()
    cand = [{"id": f"P{10001 + i}", "title": f"Test {i}", "price": 10.0} for i in range(20)]
    rr = [{"customer": c, "history": [{"id": "P10001", "title": "Test Garden chairs 0", "did": "view", "date": "2026-06-01"}],
           "candidates": cand, "answer": {"ranking": [x["id"] for x in cand[::-1]][:10], "reasons": {"P10020": "test"}},
           "usd": 0.0003, "seconds": 4.0} for c in test_buyers[:3]]
    rr.append({"customer": test_buyers[0], "history": [], "candidates": cand, "answer": None, "error": "filtered", "seconds": 0.5})
    (root / "recorded" / "llm_rerank.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rr))
    ff = [{"customer": c, "history": [{"id": "P10001", "title": "Test Garden chairs 0", "did": "view", "date": "2026-06-01"}],
           "answer": {"products": ["Test Garden chairs 0", "A made-up lamp"]}, "usd": 0.0002, "seconds": 3.0}
          for c in test_buyers[:2]]
    (root / "recorded" / "llm_freeform.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ff))
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "expected.json"))
    (root / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  "
                                             f"{p.relative_to(root).as_posix()}\n" for p in files))
    return root


@pytest.fixture(scope="session")
def data_root(tmp_path_factory):
    return make_data(tmp_path_factory.mktemp("data"))


@pytest.fixture(autouse=True)
def env(data_root, tmp_path, monkeypatch):
    monkeypatch.setenv("LARKFIELD_DATA", str(data_root))
    monkeypatch.setenv("LARKFIELD_OUTPUTS", str(tmp_path / "outputs"))
    monkeypatch.chdir(tmp_path)
    yield
