"""Module 7: cluster measures, safe clustering, golden records and undo."""

import pandas as pd

from larkfield_match import clustermeasures, golden, safecluster


def _pairs(rows):
    return pd.DataFrame(rows, columns=["record_id_l", "record_id_r", "score", "match"])


def test_bcubed_by_hand():
    cl = pd.DataFrame({"record_id": ["S-000001", "L-000001", "G-000001", "S-000002", "L-000002"],
                       "cluster_id": ["a", "a", "b", "b", "c"]})
    m = clustermeasures.measures(cl, "customers", "all")
    # B-cubed precision: S1 1, L1 1, G1 1/2, S2 1/2, L2 1 -> 0.8
    assert abs(m["bcubed_precision"] - 0.8) < 1e-9


def test_safe_clustering_cuts_the_weakest_link():
    # S-000003 (born 1985) and S-000004 (born 1987) are brothers: the weak link between them is cut
    p = _pairs([("L-000003", "S-000003", 0.99, 1), ("L-000003", "S-000004", 0.6, 1), ("S-000003", "S-000004", 0.5, 1)])
    log = []
    cl = safecluster.safe_components(p, "customers", log=log).set_index("record_id").cluster_id
    assert cl["L-000003"] == cl["S-000003"] != cl["S-000004"]
    assert log and "two dates of birth" in log[0]["why"]


def test_golden_record_keeps_the_source_of_each_field():
    ents = pd.DataFrame({"record_id": ["S-000001", "L-000001", "G-000001"], "entity_id": "LK-G-000001"})
    g = golden.build(ents).iloc[0]
    assert g.records == 3 and g.email == "mc.tremblay@example.com" and g.email_from == "L-000001"
    assert g.dob == "1980-03-14"
    # any records table with the prepared columns, for example another company's records
    from larkfield_match import prepared
    other = prepared.customers().head(2).assign(source="another shop", record_id=["X-1", "X-2"])
    g = golden.build(pd.DataFrame({"record_id": ["X-1", "X-2"], "entity_id": "E-X"}), records=other).iloc[0]
    assert g.records == 2 and g.sources == "another shop"


def test_undo_splits_and_remembers():
    ents = pd.DataFrame({"record_id": ["L-000003", "S-000003", "S-000004"], "entity_id": "LK-L-000003"})
    ents, new_id, old = golden.undo(ents, "S-000004")
    assert new_id == "LK-S-000004" and old == "LK-L-000003"
    assert ("S-000003", "S-000004") in safecluster.cannot_link()
    assert golden.history()[-1]["event"] == "split"
    # the cannot-link links go first, so the weak but right link L-000003 - S-000003 stays
    p = _pairs([("L-000003", "S-000004", 0.99, 1), ("S-000003", "S-000004", 0.9, 1), ("L-000003", "S-000003", 0.4, 1)])
    cl = safecluster.safe_components(p, "customers").set_index("record_id").cluster_id
    assert cl["L-000003"] == cl["S-000003"] != cl["S-000004"]
    # a forgotten record (match forget) stays out of the entities
    pd.DataFrame({"record_id": ["S-000004"]}).to_csv(golden.out("forgotten.csv"), index=False)
    assert golden.without_forgotten(ents).record_id.tolist() == ["L-000003", "S-000003"]

