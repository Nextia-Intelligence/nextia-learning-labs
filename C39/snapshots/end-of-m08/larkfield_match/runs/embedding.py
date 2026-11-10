"""Embeddings as a score, and a language model for the unsure pairs (Module 6, lessons 3 and 4)."""

import numpy as np

from .. import blocking, calibrate, embed, evaluate, llm, pairs, thresholds


def _embed(dataset):
    c = blocking.candidates(blocking.DEFAULT[dataset])
    scored = c.assign(score=embed.cosine_pairs(c, dataset))
    return thresholds.decide(scored, thresholds.best_f1(scored, dataset))


def with_llm(base, dataset="customers"):
    """The base run's decisions, except in the unsure band (calibrated 0.1 <= p < 0.9), where the recorded answer
    decides: 'same' -> match, 'different' or 'unsure' -> no match. Pairs with no recorded answer keep the base
    run's decision."""
    s = calibrate.calibrated(pairs.get(base, quiet=True), dataset)
    s = evaluate.ordered(s)
    rec = llm.recorded(dataset)
    band = (s.probability >= llm.LOWER) & (s.probability < llm.UPPER)
    answers = np.array([rec.get((a, b), {}).get("answer", "") for a, b in zip(s.record_id_l, s.record_id_r)])
    match = s["match"].to_numpy().copy()
    has = band.to_numpy() & (answers != "")
    match[has] = (answers[has] == "same").astype(int)
    return s.assign(match=match)[["record_id_l", "record_id_r", "score", "match"]]


RUNS = {
    "embed": ("customers", lambda: _embed("customers"), ("cosine of the name-and-address embeddings; best F1 "
              "threshold on validation")),
    "p-embed": ("products", lambda: _embed("products"), ("cosine of the title embeddings; best F1 threshold on "
                "validation")),
    "lgbm+llm": ("customers", lambda: with_llm("lgbm"), ("lgbm, with chat-small's recorded answer deciding the "
                 "unsure band (calibrated 0.1 to 0.9)")),
    "p-lgbm+llm": ("products", lambda: with_llm("p-lgbm", "products"), ("p-lgbm, with chat-small's recorded answer "
                   "deciding the unsure band")),
}
