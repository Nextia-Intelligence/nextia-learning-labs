import pandas as pd

from larkroute.commands.corrections import to_check


def test_quick_or_unlikely_moves_are_checked():
    corr = pd.DataFrame({"to_route": ["billing", "billing", "delivery"], "seconds": [5, 40, 40]})
    proba = pd.DataFrame({"billing": [0.5, 0.6, 0.0], "delivery": [0.5, 0.4, 0.01]})
    assert list(to_check(corr, proba)) == [True, False, True]
