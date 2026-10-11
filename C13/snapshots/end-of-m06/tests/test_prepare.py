from doc_extract import documents, files, ocr, prepare


def test_a_page_on_its_side_is_turned_upright_and_boxes_go_back_to_the_original():
    d = next(d for d in documents.receipts() if d.conditions.get("turn") == 90)
    raw = ocr.read(d.path, cache=False)[0]
    prepared = ocr.read(d.path, prepare=True, cache=False)[0]
    assert prepared.prepared["turn"] in (90, 270)
    mean = lambda p: sum(ln.score for ln in p.lines) / len(p.lines)  # noqa: E731
    assert mean(prepared) > mean(raw) + 0.1
    img = files.page_image(d.path, 1, ocr.OCR_DPI)
    for ln in prepared.lines:  # every box is on the original picture
        assert -5 <= ln.box[0] < ln.box[2] <= img.width + 5 and -5 <= ln.box[1] < ln.box[3] <= img.height + 5


def test_point_to_original_undoes_every_step():
    steps = {"original_size": [1000, 800], "crop": [100, 50, 700, 650], "turn": 90, "deskew": 3.0, "scale": 2.0}
    from PIL import Image

    img = Image.new("RGB", (1000, 800), "white")
    img.putpixel((300, 200), (0, 0, 0))
    out = img.crop((100, 50, 700, 650)).rotate(90, expand=True)
    out = out.rotate(3.0, resample=Image.NEAREST, expand=True, fillcolor=(255, 255, 255))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    dark = [(x, y) for x in range(out.width) for y in range(out.height) if out.getpixel((x, y))[0] < 128]
    x, y = dark[0]
    ox, oy = prepare.point_to_original(x, y, steps)
    assert abs(ox - 300) < 3 and abs(oy - 200) < 3


def test_a_small_receipt_on_a_big_page_is_cropped():
    d = next(d for d in documents.receipts() if d.source == "scan_image" and d.conditions.get("layout") == "till")
    img = files.page_image(d.path)
    box = prepare.content_box(img)
    assert (box[2] - box[0]) * (box[3] - box[1]) < 0.5 * img.width * img.height
