from larkroute import data
from larkroute.methods import available


def test_recorded_methods_cover_the_test_messages():
    test = data.messages("test")
    found = [n for n, m in available().items() if hasattr(m, "meta")]
    assert len(found) >= 5
    for name in found:
        m = available()[name]()
        pred = m.predict(test)
        assert len(pred) == len(test)
        assert m.meta["label"] in ("measured", "recorded")
