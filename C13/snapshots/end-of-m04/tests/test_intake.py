from doc_extract import documents, intake


def _all():
    reg = intake.Registry()
    return {d.doc_id: (d, intake.check(d.path, reg)) for d in documents.load()}


def test_every_file_gets_the_expected_decision():
    for doc_id, (d, r) in _all().items():
        assert r.status == d.expected_intake, (doc_id, d.file, r.status, r.reason)


def test_the_reasons_say_what_is_wrong():
    res = {d.file: r for d, r in _all().values()}
    assert "same bytes as receipt-lk-" in res["receipt-lk-986875 (1).pdf"].reason
    assert "password" in res["receipt-protected.pdf"].reason
    assert "over the limit" in res["scan-raw.tif"].reason
    assert res["receipt-scan.pdf"].accepted and res["receipt-scan.pdf"].format == "jpeg"


def test_a_smaller_limit_stops_more_files(monkeypatch):
    monkeypatch.setenv("MAX_FILE_MB", "0.2")
    statuses = [r.status for _, r in _all().values()]
    assert statuses.count("too_large") > 10


def test_the_first_copy_wins_the_order_matters():
    d1 = documents.get("D001")
    copy = next(d for d in documents.load() if d.truth.get("duplicate_of") == "D001")
    reg = intake.Registry()
    assert intake.check(copy.path, reg).status == "accepted"
    assert intake.check(d1.path, reg).status == "duplicate"


def test_image_fingerprints_also_match_different_receipts():
    docs = [d for d in documents.receipts() if d.source == "digital_pdf"][:16]
    pairs = intake.closest_pairs([d.path for d in docs], 3)
    assert pairs[0][0] <= intake.NEAR_DUPLICATE_BITS  # two different receipts look "the same"
