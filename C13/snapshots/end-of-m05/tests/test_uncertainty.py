from doc_extract import combine, documents, uncertainty
from doc_extract.pages import Line, Page


def test_an_unreadable_photo_is_flagged():
    d = next(d for d in documents.receipts() if d.truth.get("unreadable"))
    ex, _ = combine.combine(d)
    s = uncertainty.page_signals(ex.pages)
    assert any(f.startswith("unreadable") for f in s.flags)
    assert "total: absent (unreadable)" in uncertainty.field_signals(ex)  # the model's reason is kept
    # A photo whose top is cut off: the vendor is absent for a reason the contract does not allow.
    d = next(d for d in documents.receipts() if d.truth.get("printed_but_cut_off") == ["vendor", "date"])
    ex, _ = combine.combine(d)
    assert any(f.startswith("vendor: absent") and "contract allows only" in f for f in uncertainty.field_signals(ex))


def test_pages_that_disagree_are_a_conflict():
    p1 = Page("c.pdf", 1, 600, 800, "pt", "text", [Line("Order number", (0, 0, 80, 10)), Line("LK-111111", (200, 0, 260, 10))])
    p2 = Page("c.pdf", 2, 600, 800, "pt", "text", [Line("Order: LK-222222", (0, 0, 120, 10))])
    out = uncertainty.conflicts([p1, p2])
    assert out and "order_number" in out[0]


def test_a_good_scan_has_no_signal():
    d = next(d for d in documents.receipts() if d.source == "scan_pdf")
    ex, _ = combine.combine(d)
    assert uncertainty.page_signals(ex.pages).flags == []
