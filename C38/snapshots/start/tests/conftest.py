"""A tiny fake Larkfield data folder, so the tests need no download (IDs LK-1000x, queries T-...)."""

import hashlib
import json
import os

import numpy as np
import pandas as pd
import pytest

PRODUCTS = [
    # id, title, class, description, colour, price, on_sale, in_stock, added
    ("LK-10001", "grey outdoor cushion", "Furniture Cushions", "a soft cushion for the garden chair", "grey", 30, 0, 1, "2024-01-01"),
    ("LK-10002", "blue outdoor cushion", "Furniture Cushions", "a blue cushion for outdoor seats", "blue", 28, 1, 0, "2024-02-01"),
    ("LK-10003", "garden hose 50 ft", "Garden Hoses", "a long garden hose with a nozzle", "green", 45, 0, 1, "2024-03-01"),
    ("LK-10004", "hose reel", "Hose Reels", "keeps your water pipe tidy", "black", 60, 1, 1, "2024-03-02"),
    ("LK-10005", "modern sofa", "Sofas", "a three seat sofa in grey fabric", "grey", 700, 0, 1, "2024-04-01"),
    ("LK-10006", "sofa table", "Sofa & Console Tables", "a narrow table to put behind a sofa", "brown", 150, 1, 1, "2024-05-01"),
    ("LK-10007", "light blue throw pillow", "Accent Pillows", "a light blue pillow for the sofa", "blue", 25, 0, 1, "2024-06-01"),
    ("LK-10008", "floor lamp", "Floor Lamps", "a tall lamp with a linen shade", "white", 90, 0, 1, "2025-10-20"),
    ("LK-10009", "table lamp", "Table Lamps", "a small lamp for the bedside table", "white", 40, 0, 1, "2024-07-01"),
    ("LK-10010", "patio bench", "Outdoor Benches", "a wooden seat for the garden", "brown", 210, 0, 1, "2024-08-01"),
    ("LK-10011", "coussin gris", "Furniture Cushions", "un coussin pour la chaise", "grey", 31, 0, 1, "2024-09-01"),
    ("LK-10012", "red rug", "Area Rugs", "a red wool rug", "red", 120, 1, 1, "2024-09-02"),
]
QUERIES = [
    # id, query, language, split, source, qtype
    ("T-001", "garden hose", "en", "train", "wands", "specific"),
    ("T-002", "grey cushion", "en", "train", "wands", "specific"),
    ("T-003", "sofa", "en", "train", "wands", "broad"),
    ("T-004", "outdoor cushion", "en", "validation", "wands", "specific"),
    ("T-005", "lamp", "en", "validation", "wands", "broad"),
    ("T-006", "garden hose", "en", "test", "wands", "specific"),
    ("T-007", "sofa", "en", "test", "wands", "broad"),
    ("T-008", "coussin gris", "fr", "test", "translated", "specific"),
    ("T-009", "lk 10012", "en", "test", "code", "known-item"),
]
JUDGMENTS = {
    "T-001": {"LK-10003": 2, "LK-10004": 1}, "T-002": {"LK-10001": 2, "LK-10002": 1, "LK-10011": 2},
    "T-003": {"LK-10005": 2, "LK-10006": 0, "LK-10007": 0}, "T-004": {"LK-10001": 2, "LK-10002": 2},
    "T-005": {"LK-10008": 2, "LK-10009": 2}, "T-006": {"LK-10003": 2, "LK-10004": 1},
    "T-007": {"LK-10005": 2, "LK-10006": 0}, "T-008": {"LK-10001": 2, "LK-10011": 2}, "T-009": {"LK-10012": 2},
}


def make(d):
    (d / "log").mkdir(parents=True)
    (d / "embeddings").mkdir()
    (d / "recorded").mkdir()
    cat = pd.DataFrame(PRODUCTS, columns=["product_id", "title", "product_class", "description", "colour", "price",
                                          "on_sale", "in_stock", "added"])
    cat["title_fr"] = ["coussin gris extérieur"] + [""] * (len(cat) - 1)
    cat["category"] = cat["product_class"]
    cat["attributes"] = "colour: " + cat["colour"]
    cat["style"] = ""
    cat["material"] = ""
    cat["on_sale"] = cat["on_sale"].astype(bool)
    cat["in_stock"] = cat["in_stock"].astype(bool)
    cat["rating_count"] = 3
    cat["average_rating"] = 4.5
    cat["review_count"] = 1
    cat.to_csv(d / "catalogue.csv.gz", index=False)
    q = pd.DataFrame(QUERIES, columns=["query_id", "query", "language", "split", "source", "qtype"])
    q["base_query_id"] = ""
    q["query_class"] = ""
    q["band"] = ["head", "head", "torso", "torso", "tail", "head", "torso", "tail", "tail"]
    q["has_number"] = q["query"].str.contains(r"\d")
    q["planted"] = q["source"].isin(["code"])
    q["log_searches"] = 1
    q.to_csv(d / "queries.csv", index=False)
    rows = [(qid, p, g) for qid, js in JUDGMENTS.items() for p, g in js.items()]
    pd.DataFrame(rows, columns=["query_id", "product_id", "grade"]).to_csv(d / "judgments.csv.gz", index=False)
    s, imp = [], []
    for i, (text, qid, shown, clicked) in enumerate([
            ("garden hose", "T-001", ["LK-10003", "LK-10004"], [1, 0]),
            ("grey cushion", "T-002", ["LK-10002", "LK-10001"], [0, 1]),
            ("sofa", "T-003", ["LK-10006", "LK-10005", "LK-10007"], [1, 1, 0]),
            ("garden hose", "T-001", ["LK-10003", "LK-10004"], [1, 0]),
            ("outdor cushion", "", [], [])], 1):
        s.append({"search_id": f"S-{i:05d}", "session_id": f"V-{i:05d}", "date": "2025-09-0" + str(i),
                  "time": "10:00:00", "query": text, "query_id": qid, "results": len(shown),
                  "clicks": sum(clicked), "added_to_cart": 0, "reformulated": False})
        imp += [{"search_id": f"S-{i:05d}", "position": k, "product_id": p, "clicked": c, "added_to_cart": 0}
                for k, (p, c) in enumerate(zip(shown, clicked), 1)]
    pd.DataFrame(s).to_csv(d / "log" / "searches.csv.gz", index=False)
    pd.DataFrame(imp).to_csv(d / "log" / "impressions.csv.gz", index=False)
    pd.DataFrame([("couch, sofa", "two-way", ""), ("light, lamp", "two-way", "planted"),
                  ("sectional => sofa", "one-way", "")], columns=["rule", "kind", "note"]).to_csv(
        d / "synonyms.csv", index=False)
    rng = np.random.default_rng(0)
    pv = rng.normal(size=(len(cat), 8)).astype(np.float32)
    pv /= np.linalg.norm(pv, axis=1, keepdims=True)
    qv = np.stack([pv[cat.index[cat["product_id"] == next(iter(JUDGMENTS[qid]))][0]] for qid in q["query_id"]])
    np.save(d / "embeddings" / "products.npy", pv.astype(np.float16))
    np.save(d / "embeddings" / "queries.npy", qv.astype(np.float16))
    (d / "embeddings" / "model.json").write_text(json.dumps({"model": "fake", "revision": "0", "max_tokens": 16}))
    rr = [(qid, p, float(g)) for qid, js in JUDGMENTS.items() for p, g in js.items()]
    pd.DataFrame(rr, columns=["query_id", "product_id", "score"]).to_csv(d / "recorded" / "rerank.csv.gz", index=False)
    (d / "recorded" / "llm_rewrites.jsonl").write_text(
        json.dumps({"query_id": "T-008", "query": "coussin gris", "rewrite": "grey cushion"}) + "\n")
    (d / "recorded" / "llm_judgments.jsonl").write_text("".join(json.dumps(
        {"query_id": "T-003", "product_id": p, "human_grade": g, "llm_grade": min(2, g + (p == "LK-10006"))}) + "\n"
        for p, g in JUDGMENTS["T-003"].items()))
    (d / "costs.json").write_text(json.dumps({"cpu_server_usd_per_hour": {"value": 0.17}}))
    (d / "expected.json").write_text(json.dumps({"bm25_validation_ndcg10": 0.0}))
    files = sorted(p for p in d.rglob("*") if p.is_file())
    (d / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  "
                                          f"{p.relative_to(d).as_posix()}\n" for p in files))


@pytest.fixture(scope="session", autouse=True)
def fake_data(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    make(d)
    os.environ["LARKFIELD_DATA"] = str(d)
    os.environ["LARKFIELD_OUTPUTS"] = str(tmp_path_factory.mktemp("outputs"))
    return d
