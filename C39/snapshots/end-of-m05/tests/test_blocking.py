"""Module 3: blocking."""

import pandas as pd

from larkfield_match import blocking


def test_keys_keep_true_pairs():
    m = blocking.measure("keys")
    assert m["pair_completeness"] >= 0.8 and m["reduction_ratio"] > 0.5


def test_postcode_misses_the_moved_customer():
    c = blocking.candidates("postcode")
    assert ("G-000005", "S-000006") not in set(zip(c.record_id_l, c.record_id_r))


def test_sorted_neighbourhood_window():
    df = pd.DataFrame({"record_id": list("ABCDE"), "key": ["a", "b", "c", "d", "e"]})
    p = blocking.sorted_neighbourhood(df, "key", 2)
    assert len(p) == 4 and ("A", "B") in set(zip(p.record_id_l, p.record_id_r))


def test_minhash_estimates_jaccard():
    a, b = blocking.shingles("rubber garden hose green"), blocking.shingles("rubber garden hose grey")
    sa, sb = blocking.minhash_signature(a, 256), blocking.minhash_signature(b, 256)
    assert abs((sa == sb).mean() - blocking.jaccard(a, b)) < 0.12


def test_lsh_pairs_products_across_feeds():
    c = blocking.candidates("p-minhash-0.3")
    assert all(a[:2] != b[:2] for a, b in zip(c.record_id_l, c.record_id_r))
