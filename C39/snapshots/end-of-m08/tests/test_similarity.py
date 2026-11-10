"""Module 4: similarity measures and comparison vectors."""

import pandas as pd

from larkfield_match import similarity, vectors
from larkfield_match.runs.weighted import WEIGHTS, weighted_score


def test_levenshtein_by_hand():
    assert similarity.levenshtein_distance("smith", "smyth") == 1
    assert similarity.levenshtein_distance("kitten", "sitting") == 3


def test_measures_on_swapped_names():
    assert similarity.token_set_ratio("bob smith", "smith bob") == 1.0
    assert similarity.jaro_winkler("bob smith", "smith bob") < 1.0


def test_sound_codes():
    assert similarity.soundex("Robert") == similarity.soundex("Rupert")
    assert similarity.metaphone("Thériault") == similarity.metaphone("Theriault")


def test_vectors_mark_missing_values():
    v = vectors.for_pairs(pd.DataFrame({"record_id_l": ["S-000005"], "record_id_r": ["S-000002"]}), "customers")
    assert v.phone_eq.isna().iloc[0] and v.last_jw.iloc[0] == 1.0
    assert weighted_score(v, WEIGHTS)[0] > 0
