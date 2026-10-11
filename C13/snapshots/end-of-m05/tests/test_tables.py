from doc_extract import documents, tables


def _price_list():
    return next(d for d in documents.load() if d.kind == "price_list")


def test_one_table_over_two_pages_with_a_two_row_header():
    t = tables.recover(_price_list().path)
    assert t.pages == [1, 2] and t.header_rows == 2
    assert t.columns[-2:] == ["Price (CAD) / Each", "Price (CAD) / Case of 6"]
    assert t.units == {"Price (CAD) / Each": "CAD", "Price (CAD) / Case of 6": "CAD"}
    assert len(t.rows) == 41


def test_merged_cells_are_filled_and_keep_the_merged_box():
    t = tables.recover(_price_list().path)
    hr50 = next(r for r in t.rows if r["SKU"].value == "HR-50")
    assert hr50["Category"].value == "Hose reels" and hr50["Category"].filled
    first = next(r for r in t.rows if r["SKU"].value == "HR-30")
    assert hr50["Category"].box == first["Category"].box
    cont = next(r for r in t.rows if r["SKU"].value == "SP-TRV")
    assert cont["Category"].value == "Sprinklers" and cont["Category"].page == 2


def test_every_cell_is_right_and_the_naive_reading_is_not():
    d = _price_list()
    t = tables.recover(d.path)
    ok, total = tables.score([{k: c.value for k, c in r.items()} for r in t.rows], d.truth["rows"])
    assert ok == total == 246
    rows = tables.naive(d.path)
    assert len(rows) == 45  # the header rows of page 2 count as products
