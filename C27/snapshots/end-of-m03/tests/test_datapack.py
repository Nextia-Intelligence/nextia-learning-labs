"""The data pack: unchanged, readable, and with the difficulties the evaluation needs."""

from scripts.datapack import DATA, check_sums, report


def test_every_file_matches_its_checksum():
    n, bad = check_sums(DATA)
    assert n == 56 and bad == []


def test_larkfield_is_the_rag_courses_collection():
    r = report(DATA / "larkfield")
    assert r["documents"] == 36 and r["problems"] == []
    assert r["formats"] == {"html": 2, "md": 32, "pdf": 2} and r["staff_only"] == 6
    assert r["with_versions"] == ["returns-policy"] and r["supplier"] == ["supplier-aquaflow-hose-reels"]


def test_bramble_has_the_same_kinds_of_difficulty():
    r = report(DATA / "bramble")
    assert r["documents"] == 15 and r["problems"] == []
    assert r["formats"] == {"html": 1, "md": 13, "pdf": 1}
    assert r["staff_only"] == 3 and r["with_versions"] == ["returns-policy"]
    assert r["supplier"] == ["distributor-northwind-preorders"]


def test_both_shops_have_a_document_with_the_same_key():
    # the same doc_key in two shops: every key and every query must include the shop
    import csv

    keys = {}
    for shop in ("larkfield", "bramble"):
        with open(DATA / shop / "inventory.csv", encoding="utf-8") as f:
            keys[shop] = {r["doc_id"] for r in csv.DictReader(f)}
    assert keys["larkfield"] & keys["bramble"] == {"returns-policy", "gift-cards", "delivery-policy",
                                                   "refund-approval-procedure"}
