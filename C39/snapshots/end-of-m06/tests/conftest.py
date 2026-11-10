"""A tiny fake course data folder for the tests: 16 customer records of 10 people, 6 products, one day of new
records. Nothing is downloaded. The people are invented, like every record of the course."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SHOP = [
    ("S-000001", "Marie-Claude", "Tremblay", "mc.tremblay@example.com", "5145550101", "12 rue des Érables",
     "Sainte-Anne-des-Prés", "QC", "J0L 1A0", "1980-03-14", "2020-01-01"),
    ("S-000002", "Robert", "Smith", "robert.smith@example.net", "4165550102", "5 Wren St", "Larkmere", "ON", "K1A 0B1",
     "1975-06-01", "2019-05-01"),
    ("S-000003", "Daniel", "Roy", "the.roys@example.org", "4505550103", "7 rue du Moulin", "Val-des-Hérons", "QC",
     "J2B1C3", "1985-01-02", "2018-02-02"),
    ("S-000004", "David", "Roy", "the.roys@example.org", "4505550103", "7 rue du Moulin", "Val-des-Hérons", "QC",
     "J2B 1C3", "1987-05-05", "2021-03-03"),
    ("S-000005", "Sarah", "Smith", "sarah.smith@example.com", "", "2 Heron Rd", "Larkmere", "ON", "K1A 0B2", "",
     "2022-04-04"),
    ("S-000006", "Emma", "Brown", "emma.brown@example.com", "9055550109", "44 Juniper Dr", "Ashbury Falls", "ON",
     "L5C 2D2", "1970-07-07", "2023-06-06"),
]
LOYALTY = [
    ("L-000001", "Marie Claude Tremblay", " MC.Tremblay@Example.com ", "(514) 555-0101", "J0L 1A0", "14/03/1980",
     "2021-01-01", "100"),
    ("L-000002", "Bob Smith", "robert.smith@example.net", "416-555-0102", "K1A 0B1", "01/06/1975", "2020-02-02", "5"),
    ("L-000003", "Daniel Roy", "the.roys@example.org", "4505550103", "J2B 1C3", "02/01/1985", "2019-03-03", "0"),
    ("L-000004", "Tunde Oyelaran", "tunde.o@example.com", "6045550105", "V5K0A1", "10/10/1990", "2022-01-01", "7"),
    ("L-000005", "Luc Gagnon", "luc.gagnon@example.com", "8195550110", "G1A 1A2", "03/03/1960", "2018-08-08", "1"),
]
GARDEN = [
    ("G-000001", "TREMBLAY, MARIE-CLAUDE", "5145550101", "12, R. DES ERABLES, STE-ANNE-DES-PRES QC J0L1A0", "", "",
     "2015-01-01"),
    ("G-000002", "OYELARAN, TUNDE", "6045550105", "88 Fern Lane, Cedarwell BC V5K 0A1", "tunde.o@example.com", "",
     "2016-01-01"),
    ("G-000003", "BROWN, EMMA", "4505550100", "3 Elder Way, Wrenhollow ON L4B 1C1", "", "", "2017-01-01"),
    ("G-000004", "GAGNON, LUC", "4505550100", "9 rue des Pins, Lac-aux-Grives QC G1A 1A1", "", "", "2017-02-02"),
    ("G-000005", "BROWN, EMMA", "", "21 Alder Cres, Briarstead ON L6D 3E3", "", "1970-07-07", "2012-01-01"),
]
TRUTH = {
    "S-000001": ("E-1", "test"), "L-000001": ("E-1", "test"), "G-000001": ("E-1", "test"),
    "S-000002": ("E-2", "test"), "L-000002": ("E-2", "test"),
    "S-000003": ("E-3", "test"), "L-000003": ("E-3", "test"), "S-000004": ("E-4", "test"),
    "L-000004": ("E-5", "validation"), "G-000002": ("E-5", "validation"),
    "S-000005": ("E-6", "validation"), "S-000006": ("E-9", "validation"), "G-000005": ("E-9", "validation"),
    "G-000003": ("E-7", "train"), "G-000004": ("E-8", "train"), "L-000005": ("E-10", "train"),
}
FEED_A = [("NF-00001", "AquaRidge Rubber Garden Hose, 50 ft, Green", "AquaRidge", "39.99", "0123456789012",
           "garden hose"),
          ("NF-00002", "AquaRidge Rubber Garden Hose, 50 ft, Green (Pack of 2)", "AquaRidge", "71.99", "",
           "garden hose"),
          ("NF-00003", "Mossway Ceramic Planter, 12 in, Blue", "Mossway", "24.50", "", "planter")]
FEED_B = [("CL-00001", "gdn hose 15.2 m rubber green - AQUARIDGE", "AQUARIDGE", "41.00", "0123456789012"),
          ("CL-00002", "planter 30.5 cm ceramic blue - Mossway", "Mossway", "23.90", ""),
          ("CL-00003", "LED bulb 9W daylight white - Brightpath", "Brightpath", "6.50", "")]
PTRUTH = [("NF-00001", "P-1", "test"), ("CL-00001", "P-1", "test"), ("NF-00002", "P-2", "test"),
          ("NF-00003", "P-3", "validation"), ("CL-00002", "P-3", "validation"), ("CL-00003", "P-4", "train")]
DAY1 = [("D1-0001", "shop", "Marie-Claude", "Tremblay", "", "mc.tremblay@example.com", "514-555-0101",
         "12 rue des Érables", "Sainte-Anne-des-Prés", "QC", "J0L 1A0", ""),
        ("D1-0002", "loyalty", "", "", "Chloé Bérubé", "chloe.b@example.com", "4185550111", "", "", "", "G5A 1B1",
         "05/05/1995")]


def write_data(root: Path):
    (root / "sources").mkdir(parents=True)
    (root / "products").mkdir()
    (root / "daily").mkdir()
    (root / "embeddings").mkdir()
    (root / "recorded").mkdir()
    pd.DataFrame(SHOP, columns=["record_id", "first_name", "last_name", "email", "phone", "address", "city",
                                "province", "postcode", "date_of_birth", "created"]).to_csv(
        root / "sources/shop_accounts.csv", index=False)
    pd.DataFrame(LOYALTY, columns=["record_id", "full_name", "email", "phone", "postcode", "date_of_birth", "joined",
                                   "points"]).to_csv(root / "sources/loyalty_members.csv", index=False)
    pd.DataFrame(GARDEN, columns=["record_id", "name", "phone", "address", "email", "date_of_birth",
                                  "first_visit"]).to_csv(root / "sources/garden_centres.csv", index=False)
    pd.DataFrame([(r, e, s) for r, (e, s) in TRUTH.items()], columns=["record_id", "entity_id", "split"]).to_csv(
        root / "truth.csv", index=False)
    pd.DataFrame([("S-000003", "brothers"), ("S-000004", "brothers"), ("L-000003", "brothers"),
                  ("G-000003", "placeholder_phone"), ("G-000004", "placeholder_phone"),
                  ("S-000001", "saint_town"), ("G-000001", "saint_town")],
                 columns=["record_id", "problem"]).to_csv(root / "planted.csv", index=False)
    pd.DataFrame([("L-000005", "G-000004", 0, "same surname and region"), ("G-000003", "G-000004", 0, "random")],
                 columns=["record_id_l", "record_id_r", "label", "why_sampled"]).to_csv(root / "labelled_pairs.csv",
                                                                                       index=False)
    pd.DataFrame(FEED_A, columns=["product_id", "title", "brand", "price", "gtin", "category"]).to_csv(
        root / "products/feed_a.csv", index=False)
    pd.DataFrame(FEED_B, columns=["product_id", "title", "supplier_brand", "price", "gtin"]).to_csv(
        root / "products/feed_b.csv", index=False)
    pd.DataFrame(PTRUTH, columns=["product_id", "product_entity", "split"]).to_csv(root / "products/truth.csv",
                                                                                   index=False)
    pd.DataFrame([("NF-00002", "pack_of_2")], columns=["product_id", "problem"]).to_csv(
        root / "products/planted.csv", index=False)
    pd.DataFrame(DAY1, columns=["record_id", "source", "first_name", "last_name", "full_name", "email", "phone",
                                "address", "city", "province", "postcode", "date_of_birth"]).to_csv(
        root / "daily/day-1.csv", index=False)
    pd.DataFrame([("D1-0001", "E-1", 1), ("D1-0002", "E-11", 1)], columns=["record_id", "entity_id", "day"]).to_csv(
        root / "daily/truth.csv", index=False)
    (root / "costs.json").write_text(json.dumps({"review_pairs_per_day": 300, "false_merge_dollars": 150}))
    # exact (same email as typed) on the test split: 4 pairs called the same, 2 right; 5 true pairs; 12 entities
    (root / "expected.json").write_text(json.dumps({"exact": {"precision": 0.5, "recall": 0.4, "entities": 12}}))
    # fake 4-number embeddings in record order (customers: by source file order; products: feed a then b)
    rng = np.random.default_rng(0)
    for ds, ids in (("customers", [r[0] for r in SHOP + LOYALTY + GARDEN]), ("products",
                                                                              [r[0] for r in FEED_A + FEED_B])):
        e = rng.normal(size=(len(ids), 4)).astype("float32")
        e /= np.linalg.norm(e, axis=1, keepdims=True)
        np.save(root / f"embeddings/{ds}_int8.npy", np.round(e * 127).astype("int8"))
        np.save(root / f"embeddings/{ds}_scale.npy", np.full((len(ids), 1), 1 / 127, dtype="float32"))
        pd.DataFrame({"record_id": ids}).to_csv(root / f"embeddings/{ds}_ids.csv", index=False)
    (root / "recorded/llm_pairs.jsonl").write_text(json.dumps({
        "record_id_l": "S-000003", "record_id_r": "S-000004", "answer": "different", "text": "{\"answer\": "
        "\"different\", \"reason\": \"different first names and dates of birth\"}", "true": "different",
        "why_sampled": "unsure band", "model": "fake", "usd": 0.0001, "latency_s": 0.5}) + "\n")
    files = sorted(p for p in root.rglob("*") if p.is_file())
    (root / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n" for p in files))


@pytest.fixture(autouse=True)
def tiny_data(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    write_data(data_dir)
    monkeypatch.setenv("LARKFIELD_DATA", str(data_dir))
    monkeypatch.setenv("LARKFIELD_OUTPUTS", str(tmp_path / "outputs"))
    from larkfield_match import data
    for name in dir(data):
        fn = getattr(data, name)
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()
    yield data_dir
