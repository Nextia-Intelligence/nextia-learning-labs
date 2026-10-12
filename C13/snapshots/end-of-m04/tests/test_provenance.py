from doc_extract import compare, documents, provenance


def test_every_found_value_has_file_page_and_box():
    d = documents.get("D011")
    rec = provenance.record(compare.run(d, "text"))
    total = rec["fields"]["total"]
    assert total["value"] == d.fields["total"]
    ev = total["evidence"]
    assert ev["file"] == d.file and ev["page"] == 1 and ev["unit"] == "pt" and len(ev["box"]) == 4


def test_ocr_boxes_on_a_scanned_pdf_are_stored_in_points():
    d = next(d for d in documents.receipts() if d.source == "scan_pdf")
    ex = compare.run(d, "ocr")
    ev = provenance.evidence(ex.fields["total"], ex)
    assert ev.unit == "pt" and ev.box[2] <= 612 + 1  # inside a letter page (612 x 792 pt)


def test_absent_values_have_no_evidence_and_boxes_are_drawn(tmp_path):
    d = documents.get("D011")
    ex = compare.run(d, "text")
    rec = provenance.record(ex)
    assert rec["fields"]["shipping"]["evidence"] is None
    written = provenance.draw(d.path, ex, tmp_path / "x.png")
    assert written and written[0].exists()
