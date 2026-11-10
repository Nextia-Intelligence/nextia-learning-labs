"""Module 1: the data, the exact baseline, the measures and the setup check."""

import pandas as pd

from larkfield_match import cli, cluster, data, evaluate, pairs


def test_records_have_the_shared_columns():
    r = data.records()
    assert list(r.columns) == ["record_id", "source", "name", "email", "phone", "address", "postcode",
                               "date_of_birth", "created"]
    assert len(r) == 16 and set(r.source) == {"shop", "loyalty", "garden"}


def test_true_pairs_and_their_split():
    t = evaluate.true_pairs()
    assert len(t) == 3 + 1 + 1 + 1 + 1   # E-1 has 3 records (3 pairs), E-2, E-3, E-5, E-9 one pair each
    assert set(t[t.entity_id == "E-1"].split) == {"test"}


def test_a_pair_with_a_test_record_is_a_test_pair():
    df = pd.DataFrame({"record_id_l": ["G-000003"], "record_id_r": ["S-000001"]})
    assert evaluate.pair_split(df).iloc[0] == "test"


def test_pair_measures_by_hand():
    df = pd.DataFrame({"record_id_l": ["L-000002", "S-000003"], "record_id_r": ["S-000002", "S-000004"],
                       "score": 1.0, "match": 1})
    m = evaluate.pair_measures(df, "customers", "test")
    assert (m["tp"], m["fp"], m["true"]) == (1, 1, 5)
    assert m["precision"] == 0.5 and m["recall"] == 0.2


def test_connected_components_are_transitive():
    df = pd.DataFrame({"record_id_l": ["A", "B"], "record_id_r": ["B", "C"], "match": [1, 1]})
    c = cluster.components(df, ["A", "B", "C", "D"])
    assert c.set_index("record_id").cluster_id.to_dict() == {"A": "A", "B": "A", "C": "A", "D": "D"}


def test_exact_needs_the_same_text():
    p = pairs.get("exact", quiet=True)
    found = set(zip(p.record_id_l, p.record_id_r))
    assert ("L-000002", "S-000002") in found
    assert ("L-000001", "S-000001") not in found   # spaces and capitals: not the same text


def test_exact_measures_and_entities():
    p = pairs.get("exact", quiet=True)
    m = evaluate.pair_measures(p, "customers", "test")
    assert (m["precision"], m["recall"]) == (0.5, 0.4)
    assert evaluate.entity_count(p, pairs.record_ids("customers")) == 12


def test_check_passes(capsys):
    cli.main(["check"])
    assert "Setup check passed." in capsys.readouterr().out


def test_info_and_show(capsys):
    cli.main(["info"])
    cli.main(["show", "S-000001"])
    out = capsys.readouterr().out
    assert "16 in 3 sources" in out and "Entity E-1" in out and "saint_town" in out


def test_reset_removes_outputs(capsys):
    pairs.get("exact", quiet=True)
    cli.main(["reset"])
    assert "all files are right" in capsys.readouterr().out


def test_help_lists_the_commands(capsys):
    cli.main([])
    out = capsys.readouterr().out
    for name in ("info", "show", "score", "cluster", "eval", "check", "reset"):
        assert name in out
