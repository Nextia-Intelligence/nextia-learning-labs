from doc_extract import combine, documents, review


def test_a_document_with_an_error_always_goes_to_review():
    r = review.Routed("D1", "x.pdf", 1.0, ["total: does not add up"])
    assert r.needs_review(0.0)
    assert not review.Routed("D2", "y.pdf", 0.99, []).needs_review(0.95)
    assert review.Routed("D3", "z.pdf", 0.90, []).needs_review(0.95)


def test_the_printed_wrong_total_goes_to_review():
    d = next(d for d in documents.receipts() if d.truth.get("adds_up") is False and d.source == "digital_pdf")
    r, _ = review.route_doc(d)
    assert any("total" in x for x in r.reasons)


def test_certainty_is_the_lowest_reading_score_of_the_required_fields():
    ex, dec = combine.combine(documents.get("D011"))
    assert review.certainty(ex, dec) == 1.0  # the text layer


def test_the_models_confidence_is_almost_always_high():
    rows = review.calibration()
    high = sum(r["answers"] for r in rows if r["confidence"] in ("1.0", "0.95-0.99"))
    assert high == sum(r["answers"] for r in rows)
