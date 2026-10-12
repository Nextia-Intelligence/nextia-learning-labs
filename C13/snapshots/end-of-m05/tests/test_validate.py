from datetime import date

from doc_extract import validate

GOOD = {"vendor": "Larkfield", "order_number": "LK-547562", "date": "2026-08-22", "currency": "CAD",
        "subtotal": "189.00", "shipping": None, "tax": "22.68", "total": "211.68", "payment_method": "Cash"}
TODAY = date(2026, 10, 10)


def rules(values, items=None):
    return [(p.field, p.rule, p.severity) for p in validate.validate(values, items, TODAY)]


def test_a_good_receipt_has_no_problem():
    assert rules(GOOD) == []


def test_a_total_that_does_not_add_up_is_an_error():
    out = validate.validate(GOOD | {"total": "221.68"}, None, TODAY)
    assert [(p.field, p.rule) for p in out] == [("total", "adds_up")]
    assert "difference +10.00" in out[0].message


def test_dates_formats_and_codes():
    assert ("date", "future", "error") in rules(GOOD | {"date": "2026-12-01"})
    assert ("order_number", "format", "error") in rules(GOOD | {"order_number": "0693-220"})
    assert ("currency", "foreign", "warning") in rules(GOOD | {"currency": "USD"})
    assert ("total", "required", "error") in rules(GOOD | {"total": None})


def test_an_unusual_tax_rate_is_a_warning():
    assert ("tax", "rate", "warning") in rules(GOOD | {"tax": "30.00", "total": "219.00"})


def test_item_lines_must_add_up():
    items = [{"description": "x", "quantity": 2, "unit_price": "50.00", "line_total": "100.00"}]
    assert ("items", "adds_up", "warning") in rules(GOOD, items)


def test_the_same_receipt_twice_is_found_by_its_content():
    recs = {"D001": GOOD, "D002": GOOD | {"order_number": None}, "D003": GOOD | {"order_number": "LK-000001", "total": "1.00"}}
    assert validate.duplicates(recs) == {"D002": "D001"}
