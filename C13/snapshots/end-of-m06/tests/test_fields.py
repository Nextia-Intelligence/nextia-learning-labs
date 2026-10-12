from doc_extract import compare, documents, fields, textlayer
from doc_extract.pages import Line, Page


def _text(doc_id):
    d = documents.get(doc_id)
    return d, fields.extract(textlayer.read(d.path), "text")


def test_the_rules_fill_every_field_of_a_digital_till_receipt_with_evidence():
    d = next(d for d in documents.receipts() if d.source == "digital_pdf" and d.truth.get("layout") == "till"
             and d.language == "en" and d.fields["order_number"])
    _, ex = _text(d.doc_id)
    for name, want in d.fields.items():
        assert compare.correct(name, ex.value(name), want), name
        if want is not None:
            assert ex.fields[name].lines, f"{name} has no evidence"


def test_a_french_receipt_reads_the_day_first():
    d = next(d for d in documents.receipts() if d.source == "digital_pdf" and d.language == "fr" and d.truth.get("layout") == "till")
    _, ex = _text(d.doc_id)
    assert ex.value("date") == d.fields["date"]
    assert ex.value("total") == d.fields["total"]


def test_no_order_number_on_an_in_store_receipt_stays_absent():
    d = next(d for d in documents.receipts() if d.source == "digital_pdf" and d.fields["order_number"] is None
             and d.truth.get("layout") == "till")
    _, ex = _text(d.doc_id)
    assert ex.value("order_number") is None
    assert ex.fields["order_number"].status == "absent"


def test_the_rules_do_not_know_another_shops_words():
    d = next(d for d in documents.receipts() if d.source == "digital_pdf" and d.fields["vendor"] != "Larkfield")
    _, ex = _text(d.doc_id)
    assert ex.value("total") is None  # "AMOUNT DUE" is not a Larkfield word
    assert ex.fields["vendor"].reason.startswith("unknown shop")


def test_tax_lines_are_added_up():
    lines = [Line("Subtotal", (0, 0, 50, 10)), Line("100.00", (200, 0, 240, 10)),
             Line("GST 5%", (0, 20, 50, 30)), Line("5.00", (200, 20, 240, 30)),
             Line("PST 7%", (0, 40, 50, 50)), Line("7.00", (200, 40, 240, 50)),
             Line("TOTAL", (0, 60, 50, 70)), Line("CAD 112.00", (180, 60, 240, 70))]
    ex = fields.extract([Page("x.pdf", 1, 300, 100, "pt", "text", lines)], "text")
    assert ex.value("tax") == "12.00" and ex.value("total") == "112.00" and ex.value("currency") == "CAD"


def test_a_quantity_line_keeps_the_unit_price():
    # Found by the item check of validate.py: "3 x 24.95  74.85" gave a unit price of 74.85.
    rows = [(1, [Line("Pruning shears", (14, 227, 90, 236))]),
            (1, [Line("3 x 24.95", (25, 239, 74, 248)), Line("74.85", (186, 239, 213, 248))]),
            (1, [Line("Tuyau d'arrosage", (14, 252, 90, 261))]),
            (1, [Line("2 x 1 011,78", (25, 264, 74, 273)), Line("2 023,56", (180, 264, 213, 273))])]
    got = [(i["quantity"], i["unit_price"], i["line_total"]) for i in fields.items(rows)]
    assert got == [(3, "24.95", "74.85"), (2, "1011.78", "2023.56")]
