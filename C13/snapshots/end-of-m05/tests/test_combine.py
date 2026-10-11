from doc_extract import combine, compare, documents
from doc_extract.pages import Line, Page


def test_a_larkfield_receipt_does_not_need_the_model():
    ex, dec = combine.combine(documents.get("D011"))
    assert not dec.used_model and ex.usage == {}


def test_another_shops_receipt_uses_the_model_and_the_values_are_grounded():
    d = next(d for d in documents.receipts() if d.source == "digital_pdf" and d.fields["vendor"] != "Larkfield")
    ex, dec = combine.combine(d)
    assert dec.used_model and any("unknown shop" in w for w in dec.why)
    assert dec.source["total"] == "model" and ex.fields["total"].lines  # found on the page: it has a box
    for name in ("subtotal", "total", "payment_method"):
        assert compare.correct(name, ex.value(name), d.fields[name])


def test_ground_finds_a_value_only_when_the_page_shows_it():
    page = Page("x.jpg", 1, 500, 500, "px", "ocr", [Line("TOTAL", (0, 0, 50, 10)), Line("1 011,78 $", (300, 0, 380, 10))])
    assert combine.ground("total", "1011.78", "", [page]).text == "1 011,78 $"
    assert combine.ground("order_number", "LK-123456", "LK-123456", [page]) is None


def test_a_value_the_page_does_not_show_is_marked_unverified():
    d = next(d for d in documents.receipts() if d.truth.get("printed_but_cut_off") == ["total", "payment_method"])
    ex, dec = combine.combine(d)
    assert ex.value("total") is None  # cut off: nobody invents it
    assert any(f.startswith("unverified") for f in dec.flags.get("currency", []))
