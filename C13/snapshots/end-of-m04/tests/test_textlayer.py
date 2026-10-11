from doc_extract import documents, textlayer
from doc_extract.pages import Line, rows


def test_lines_have_boxes_inside_the_page():
    page = textlayer.read(documents.get("D011").path)[0]
    assert page.unit == "pt" and page.path == "text"
    assert any(ln.text == "TOTAL" for ln in page.lines)
    for ln in page.lines:
        x0, top, x1, bottom = ln.box
        assert 0 <= x0 < x1 <= page.width and 0 <= top < bottom <= page.height


def test_a_wide_space_starts_a_new_line():
    page = textlayer.read(documents.get("D011").path)[0]
    texts = [ln.text for ln in page.lines]
    assert "Subtotal" in texts  # the amount is a separate line, as OCR gives it


def test_a_scanned_pdf_has_no_text_layer():
    scanned = next(d for d in documents.receipts() if d.source == "scan_pdf")
    assert textlayer.read(scanned.path)[0].lines == []


def test_rows_pair_a_label_with_its_amount_on_a_crooked_page():
    a = Line("TOTAL", (100, 500, 160, 520), angle=5.0)
    b = Line("CAD 84.07", (400, 526, 480, 546), angle=5.0)  # 300 px to the right, 26 px lower: the same row at 5 degrees
    c = Line("Visa", (100, 560, 150, 580), angle=5.0)
    assert [[ln.text for ln in r] for r in rows([a, b, c])] == [["TOTAL", "CAD 84.07"], ["Visa"]]
