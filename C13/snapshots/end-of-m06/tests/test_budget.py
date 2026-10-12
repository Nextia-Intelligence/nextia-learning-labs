from doc_extract import budget, prices


def test_cost_uses_the_list_price():
    assert prices.cost(1_000_000, 0, "chat-strong") == 2.0
    assert round(prices.cost(3000, 500), 4) == 0.011


def test_measure_reports_every_path(monkeypatch):
    monkeypatch.setattr(budget, "SAMPLE", ["D011"])
    m = budget.measure(["D011"])
    assert m["text_seconds_per_page"] < 1
    assert m["vision"]["usd_per_page"] > 0 and m["vision"]["recorded_calls"] >= 54
