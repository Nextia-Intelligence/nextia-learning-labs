from doc_extract import compare, documents


def test_correct_compares_normalised_values():
    assert compare.correct("total", "1 011,78 $", "1011.78")
    assert compare.correct("vendor", "LARKFIELD", "Larkfield")
    assert compare.correct("shipping", None, None)
    assert compare.correct("shipping", "0.00", None)  # not printed counts as 0.00
    assert not compare.correct("order_number", "0693-220", None)


def test_the_paths_read_what_they_can():
    digital = documents.get("D011")
    photo = next(d for d in documents.receipts() if d.source == "photo")
    assert compare.run(digital, "text") is not None
    assert compare.run(photo, "text") is None  # a photo has no text layer
    assert compare.run(photo, "vision").path == "vision"
