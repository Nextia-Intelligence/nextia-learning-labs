import pandas as pd

from larkroute import model_store


def test_the_label_version_depends_only_on_the_labels():
    a = pd.DataFrame({"message_id": ["M-1", "M-2"], "route": ["delivery", "billing"]})
    assert model_store.label_version(a) == model_store.label_version(a.iloc[::-1])
    assert model_store.label_version(a) != model_store.label_version(a.assign(route=["delivery", "orders"]))
