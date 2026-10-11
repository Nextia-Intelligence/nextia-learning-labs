from doc_extract import documents, layout, textlayer


def _policy():
    return next(d for d in documents.load() if d.file == "returns-policy-v4.pdf")


def test_the_gap_between_the_columns_is_found():
    page = textlayer.read(_policy().path)[0]
    narrow = [ln for ln in page.lines if layout._narrow(ln, page.width)]
    g = layout.find_gutter(narrow, page.width)
    assert g is not None and 290 < g < 320


def test_reading_order_keeps_every_paragraph_whole():
    d = _policy()
    paragraphs = [s["text"] for s in d.truth["sections"] if s["kind"] in ("p", "li")]
    naive, ordered = [], []
    for page in textlayer.read(d.path):
        naive += layout.naive_order(page)
        ordered += layout.reading_order(page)
    assert layout.kept_whole(layout.text_of(ordered), paragraphs) == len(paragraphs) == 25
    assert layout.kept_whole(layout.text_of(naive), paragraphs) < 15


def test_a_receipt_has_one_column():
    page = textlayer.read(documents.get("D011").path)[0]
    assert layout.find_gutter(page.lines, page.width) is None
