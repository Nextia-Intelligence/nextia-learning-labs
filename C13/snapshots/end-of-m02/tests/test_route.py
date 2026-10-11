from doc_extract import documents, route


def test_sniff_reads_the_first_bytes_not_the_name():
    assert route.sniff(b"%PDF-1.4 ...") == "pdf"
    assert route.sniff(b"\xff\xd8\xff\xe0....") == "jpeg"
    assert route.sniff(b"\x89PNG\r\n\x1a\n....") == "png"
    assert route.sniff(b"II*\x00....") == "tiff"
    assert route.sniff(b"hello") == "unknown"


def test_each_kind_of_file_gets_its_route():
    by_source = {}
    for d in documents.load():
        if d.kind == "bad":
            continue
        by_source.setdefault(d.source, set()).add(" ".join(route.inspect(d.path).routes))
    assert by_source["digital_pdf"] == {"text", "text text"}
    assert by_source["scan_pdf"] == {"ocr"}
    assert by_source["scan_image"] == {"ocr"}
    assert by_source["photo"] == {"ocr"}
    assert by_source["xlsx"] == {"sheet"}
    assert by_source["mixed_pdf"] == {"text ocr"}


def test_photos_and_scans_are_told_apart():
    wrong = [d.doc_id for d in documents.receipts() if d.source in ("photo", "scan_image")
             and route.inspect(d.path).kind != ("photo" if d.source == "photo" else "scan")]
    assert wrong == []


def test_a_jpeg_with_a_pdf_name_is_found():
    d = documents.get("receipt-scan.pdf")
    i = route.inspect(d.path)
    assert i.format == "jpeg" and not i.extension_ok
