from pathlib import Path

import pytest

from doc_extract import contract


@pytest.mark.parametrize("raw, want", [
    ("1 011,78 $", "1011.78"), ("CAD 1,011.78", "1011.78"), ("$178.54", "178.54"), ("TVQ 9,975 %  56,86", "56.86"),
    ("2 x 89,00  178,00", "178.00"), ("TPS 5 %", None), (189, "189.00"), ("74.4", "74.40"), (None, None),
])
def test_money(raw, want):
    assert contract.money(raw) == want


@pytest.mark.parametrize("raw, day_first, want", [
    ("Date : 09/08/2026", True, "2026-08-09"), ("09/08/2026", False, "2026-09-08"), ("Date: 2026-08-22", False, "2026-08-22"),
    ("July 25, 2026", False, "2026-07-25"), ("October 1,2026", False, "2026-10-01"), ("Sep 6 2026", False, "2026-09-06"),
    ("14 sept. 2026", True, "2026-09-14"), ("20 juin 2026", True, "2026-06-20"), ("31/02/2026", True, None),
])
def test_dates(raw, day_first, want):
    assert contract.parse_date(raw, day_first) == want


def test_normalise_makes_the_same_value_look_the_same():
    assert contract.normalise("vendor", "LARKFIELD Home & Garden") == contract.normalise("vendor", "Larkfield")
    assert contract.vendor("MAPLE & PINE") == "Maple & Pine Hardware"
    assert contract.normalise("vendor", "MAPLE & PINE") == contract.normalise("vendor", "Maple & Pine Hardware")
    assert contract.normalise("payment_method", "Visa ****4821") == "Visa"
    assert contract.normalise("order_number", "lk - 547562") == "LK-547562"
    assert contract.normalise("total", None) is None


def test_every_field_is_in_the_written_contract():
    doc = (Path(__file__).resolve().parents[1] / "docs" / "extraction-contract.md").read_text(encoding="utf-8")
    for f in contract.RECEIPT:
        assert f"`{f.name}`" in doc
    assert contract.CONTRACT_VERSION in doc
