"""Module 6: classifiers, calibration, embeddings and the recorded language-model answers."""

import numpy as np
import pandas as pd

from larkfield_match import calibrate, classifier, embed, llm


def _toy():
    rng = np.random.default_rng(1)
    x = pd.DataFrame(rng.random((200, 3)), columns=["a", "b", "c"])
    y = (x.a + 0.2 * rng.random(200) > 0.6).astype(int).to_numpy()
    return x, y


def test_both_classifiers_learn():
    x, y = _toy()
    for kind in classifier.MODELS:
        p = classifier.predict(classifier.fit(kind, x, y), kind, x)
        assert ((p > 0.5) == y).mean() > 0.85


def test_calibration_is_monotone():
    s = pd.DataFrame({"record_id_l": ["L-000004", "S-000005", "G-000005"], "record_id_r": ["G-000002", "S-000006",
                      "S-000006"], "score": [0.9, 0.2, 0.8]})
    c = calibrate.calibrated(s)
    assert c.sort_values("score").probability.is_monotonic_increasing


def test_quantized_embeddings_keep_the_cosine():
    e = np.random.default_rng(2).normal(size=(5, 16)).astype("float32")
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    q, s = embed.quantize(e)
    back = q * s
    back /= np.linalg.norm(back, axis=1, keepdims=True)
    assert np.abs((back * e).sum(axis=1) - 1).max() < 1e-3


def test_cosine_pairs_from_shipped_embeddings():
    pairs = pd.DataFrame({"record_id_l": ["S-000001"], "record_id_r": ["S-000001"]})
    assert abs(embed.cosine_pairs(pairs, "customers")[0] - 1) < 1e-5


def test_recorded_answers_and_parsing():
    assert llm.recorded()[("S-000003", "S-000004")]["answer"] == "different"
    assert llm.parse_answer('{"answer": "same", "reason": "x"}') == "same"
    assert llm.parse_answer("I think so") == "unsure"
    assert "family" in llm.messages("S-000003", "S-000004")[0]["content"]
