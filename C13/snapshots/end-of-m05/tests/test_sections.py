from doc_extract import documents, sections, textlayer


def _blocks(file):
    d = next(d for d in documents.load() if d.file == file)
    return d, *sections.parse(textlayer.read(d.path))


def test_the_running_header_and_footer_are_dropped():
    _, blocks, dropped = _blocks("returns-policy-v4.pdf")
    assert "Page 1" in dropped and "Page 2" in dropped
    assert not any("Page 1" == b.text for b in blocks)


def test_every_block_knows_its_section_path():
    _, blocks, _ = _blocks("returns-policy-v4.pdf")
    window = next(b for b in blocks if b.text.startswith("The 45 days start"))
    assert window.path == ["Returns policy", "Return window"]
    items = [b for b in blocks if b.kind == "list_item"]
    assert len(items) == 7


def test_footnotes_are_linked_to_their_mark():
    _, blocks, _ = _blocks("returns-policy-v4.pdf")
    notes = [b for b in blocks if b.kind == "footnote"]
    assert len(notes) == 2
    linked = next(b for b in blocks if "12.95 dollars" in b.text and b.kind == "paragraph")
    assert linked.notes and linked.notes[0].startswith("²")


def test_paragraphs_are_found_word_for_word():
    d, blocks, _ = _blocks("returns-policy-v4.pdf")
    truth = [s["text"] for s in d.truth["sections"] if s["kind"] in ("p", "li")]
    got = {b.text for b in blocks}
    assert sum(t in got for t in truth) == len(truth)


def test_a_claim_file_holds_two_parts():
    assert sections.parts([(1, "text", "Larkfield · Warranty claim form"), (2, "ocr", "")]) == [(1, 1, "text"), (2, 2, "ocr")]
