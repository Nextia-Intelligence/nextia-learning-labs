"""Module 8: daily matching, review, privacy and deletion."""

import numpy as np
import pandas as pd

from larkfield_match import cli, golden, incremental, privacy, review


class _EmailModel:
    """A stand-in for the trained model: 'same' when the emails or the phones are equal."""

    def predict_proba(self, x):
        p = np.where((np.nan_to_num(x["email_eq"]) == 1) | (np.nan_to_num(x["phone_eq"]) == 1), 0.95, 0.01)
        return np.c_[1 - p, p]


class _Same:
    def predict(self, p):
        return p


def _entities():
    ids = [r for r in pd.read_csv(incremental.data_dir() / "truth.csv").record_id]
    golden.save_entities(pd.DataFrame({"record_id": ids, "entity_id": [f"LK-{r}" for r in ids]}))


def test_a_day_of_new_records(monkeypatch):
    _entities()
    monkeypatch.setattr(incremental, "_model", lambda: (_EmailModel(), _Same()))
    r = incremental.run_day(1)
    assert r["records"] == 2 and r["joined"] == 1 and r["new_entities"] == 1 and r["right_joins"] == 1


def test_review_decisions_merge_entities():
    _entities()
    q = pd.DataFrame({"record_id_l": ["L-000002"], "record_id_r": ["S-000002"], "probability": [0.5],
                      "reason": ["unsure"], "day": [1]})
    q.to_csv(golden.out("review_queue.csv"), index=False)
    r = review.simulate(capacity=10, error=0.0)
    e = golden.load_entities().set_index("record_id").entity_id
    assert r["same"] == 1 and e["L-000002"] == e["S-000002"]


def test_bloom_filters_keep_similarity_and_hashes_do_not():
    a, b = privacy.bloom("theriault"), privacy.bloom("theriaul")
    assert privacy.dice(a, b) > 0.8 > privacy.dice(a, privacy.bloom("smith"))
    assert privacy.hashed("theriault") != privacy.hashed("theriaul")


def test_forget_removes_the_record(capsys):
    golden.save_entities(pd.DataFrame({"record_id": ["S-000001", "L-000001"], "entity_id": "LK-L-000001"}))
    cli.main(["forget", "S-000001"])
    assert "S-000001" not in set(golden.load_entities().record_id)
    assert golden.history()[-1]["event"] == "forget"
