import pandas as pd

from larkroute.drift import psi, weekly


def test_psi_is_zero_for_the_same_shares_and_grows_with_change():
    a = pd.Series({"delivery": 0.5, "billing": 0.5})
    assert psi(a, a) == 0
    assert psi(a, pd.Series({"delivery": 0.8, "billing": 0.2})) > 0.2


def test_weekly_table():
    ref = pd.DataFrame({"predicted": ["delivery", "billing"]})
    routed = pd.DataFrame({"created_at": ["2026-02-02T10:00:00", "2026-02-03T10:00:00", "2026-02-10T10:00:00"],
                           "predicted": ["delivery", "billing", "delivery"], "confidence": [0.9, 0.8, 0.4],
                           "zone": ["decide", "decide", "review"]})
    t = weekly(routed, ref)
    assert list(t["messages"]) == [2, 1] and list(t["unsure"]) == [0.0, 1.0]
