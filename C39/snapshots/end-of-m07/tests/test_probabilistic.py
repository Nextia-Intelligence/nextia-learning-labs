"""Module 5: Fellegi–Sunter and Splink."""

import numpy as np
import pandas as pd

from larkfield_match import fs, splinkmodel


def test_levels():
    lv = fs.level_of([1.0, 0.95, 0.5, np.nan], [("same", 1.0), ("close", 0.92)])
    assert list(lv) == ["same", "close", "different", "missing"]


def test_m_and_u_sum_to_one():
    v = pd.DataFrame({c: [1.0, 1.0, 0.0, 0.0] for _, (c, _) in fs.LEVELS.items()})
    t = fs.estimate(v, [1, 1, 0, 0])
    for _, g in t.groupby("field"):
        assert abs(g.m.sum() - 1) < 1e-9 and abs(g.u.sum() - 1) < 1e-9
    assert (t[t.level == "same"].weight > 0).all()


def test_a_rare_surname_weighs_more():
    t = fs.surname_weights(["smith", "oyelaran"]).set_index("surname")
    assert t.loc["oyelaran", "weight"] > t.loc["smith", "weight"]


def test_splink_table_uses_null_for_missing():
    t = splinkmodel.table()
    assert pd.isna(t.set_index("record_id").loc["S-000005", "phone"])
