from PIL import Image

from doc_extract import documents, files, ocr


def test_ocr_reads_a_receipt_picture_with_boxes_and_scores():
    img = files.page_image(documents.get("D011").path, 1, 150)
    lines, seconds = ocr.lines_from_image(img)
    texts = " ".join(ln.text for ln in lines)
    assert "TOTAL" in texts and "LK-" in texts
    assert seconds > 0
    for ln in lines:
        assert 0 <= ln.score <= 1
        assert 0 <= ln.box[0] < ln.box[2] <= img.width + 2


def test_ocr_on_a_pdf_page_records_the_resolution_and_uses_the_cache():
    d = next(d for d in documents.receipts() if d.source == "scan_pdf")
    first = ocr.read(d.path)[0]
    assert first.unit == "px" and first.dpi == ocr.OCR_DPI
    again = ocr.read(d.path)[0]  # from out/cache/ocr
    assert [ln.text for ln in again.lines] == [ln.text for ln in first.lines]


def test_an_empty_picture_gives_no_lines():
    lines, _ = ocr.lines_from_image(Image.new("RGB", (400, 300), "white"))
    assert lines == []
