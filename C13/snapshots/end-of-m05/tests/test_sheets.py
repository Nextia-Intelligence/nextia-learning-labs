from doc_extract import documents, sheets


def _sheet():
    return next(d for d in documents.load() if d.kind == "spreadsheet")


def test_the_header_is_found_below_the_title_with_its_units():
    names, units, recs = sheets.read(_sheet().path)
    assert names[0] == "Category" and recs[0]["SKU"].cell == "B5"
    assert units == {"Price each (CAD)": "CAD", "Price per case (CAD)": "CAD", "Pack weight (kg)": "kg"}
    assert len(recs) == 41


def test_merged_cells_keep_their_range_and_numbers_stay_numbers():
    _, _, recs = sheets.read(_sheet().path)
    hr50 = next(r for r in recs if r["SKU"].value == "HR-50")
    assert hr50["Category"].value == "Hose reels" and hr50["Category"].merged == "A5:A8"
    assert hr50["Price each (CAD)"].value == 119
    cut = next(r for r in recs if r["SKU"].value == "HS-CUT")
    assert cut["Price per case (CAD)"].value is None  # "n/a" in the sheet


def test_without_the_merged_cells_the_category_is_lost():
    _, _, recs = sheets.read(_sheet().path, fill_merged=False)
    assert sum(r["Category"].value is None for r in recs) == 41 - 7
