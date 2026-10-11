from doc_extract import documents, evaluate


def test_outcomes():
    assert evaluate.outcome("total", "10.00", "10.00") == "correct"
    assert evaluate.outcome("total", None, "10.00") == "missing"
    assert evaluate.outcome("total", "11.00", "10.00") == "wrong"
    assert evaluate.outcome("order_number", "0693-220", None) == "invented"
    assert evaluate.outcome("order_number", None, None) == "correct_absent"
    assert evaluate.outcome("shipping", "0.00", None) == "correct_absent"


def test_evaluate_counts_by_source_and_field():
    docs = [documents.get("D011"), next(d for d in documents.receipts() if d.source == "photo")]
    r = evaluate.evaluate(("vision", "vision_v1"), docs)
    v = r["systems"]["vision"]
    assert v["complete"]["all"]["documents"] == 2
    assert sum(v["cells"]["all|total"].values()) == 2
    s = evaluate.summary(r, "vision")
    assert s["present"] > 10 and 0 <= s["accuracy_present"] <= 1


def test_the_plain_prompt_invents_order_numbers():
    docs = [d for d in documents.receipts() if d.fields["order_number"] is None]
    r = evaluate.evaluate(("vision", "vision_v1"), docs)
    inv = lambda s: r["systems"][s]["cells"]["all|order_number"].get("invented", 0)  # noqa: E731
    assert inv("vision_v1") > inv("vision") == 0
