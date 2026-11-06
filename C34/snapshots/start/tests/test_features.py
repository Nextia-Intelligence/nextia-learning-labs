import pandas as pd

from detect import features


def test_one_row_per_payment_in_the_same_order(payments):
    X = features.behaviour(payments)
    assert len(X) == len(payments)
    assert list(X.columns) == features.BEHAVIOUR


def test_no_feature_looks_into_the_future(payments):
    """A payment's features must not change when later payments are removed (a live job does not know them)."""
    cut = payments.ts.iloc[len(payments) // 2]
    full = features.behaviour(payments)
    early = features.behaviour(payments[payments.ts <= cut])
    pd.testing.assert_frame_equal(full.iloc[: len(early)].reset_index(drop=True), early)


def test_the_stolen_card_looks_unusual(payments):
    X = features.behaviour(payments)
    burst = (payments.device_id == "D-bad0001").to_numpy()
    assert X.new_device[burst].eq(1).all()
    assert X.new_country[burst].eq(1).all()
    assert X.payments_last_hour[burst].max() == 8
    assert X.night[burst].eq(1).all()
    assert X.new_device[~burst & (payments.device_id != "D-test0001").to_numpy()].eq(0).all()


def test_card_testing_shows_on_the_device(payments):
    X = features.behaviour(payments)
    test = (payments.device_id == "D-test0001").to_numpy()
    assert X.device_payments_last_hour[test].max() == 5
