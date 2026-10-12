from decimal import Decimal

from doc_extract import documents, generate


def test_the_set_has_every_kind_of_document():
    docs = documents.load()
    kinds = {}
    for d in docs:
        kinds[d.kind] = kinds.get(d.kind, 0) + 1
    assert len(docs) == 65
    assert kinds == {"receipt": 53, "policy": 2, "price_list": 1, "spreadsheet": 1, "claim": 1, "bad": 7}
    assert {d.source for d in docs} >= {"digital_pdf", "scan_pdf", "scan_image", "photo", "xlsx", "mixed_pdf"}
    assert sum(d.language == "fr" for d in docs if d.kind == "receipt") >= 10


def test_the_same_receipt_gives_the_same_bytes():
    import random

    a = generate.make_receipt("X", random.Random(5), "till")
    b = generate.make_receipt("X", random.Random(5), "till")
    assert generate.receipt_pdf(a) == generate.receipt_pdf(b)


def test_true_totals_add_up_except_the_two_printed_wrong():
    wrong = []
    for d in documents.receipts():
        f = d.fields
        if None in (f["subtotal"], f["tax"], f["total"]):
            continue
        total = Decimal(f["subtotal"]) + Decimal(f["shipping"] or "0") + Decimal(f["tax"])
        if total != Decimal(f["total"]):
            wrong.append(d.doc_id)
            assert d.truth["adds_up"] is False
    assert len(wrong) == 2


def test_cut_off_values_are_absent_in_the_truth():
    cut = [d for d in documents.receipts() if d.truth.get("printed_but_cut_off")]
    assert len(cut) == 2
    for d in cut:
        for name in d.truth["printed_but_cut_off"]:
            assert d.fields[name] is None


def test_french_till_receipts_print_the_day_first():
    r = generate.make_receipt("X", __import__("random").Random(1), "till", "fr")
    assert r.date_text() == f"{r.date.day:02d}/{r.date.month:02d}/{r.date.year}"
