"""Choose a threshold on the validation pairs (never on the test pairs)."""

import numpy as np

from . import evaluate


def curve(scored, dataset, split="validation"):
    """Precision and recall of `score >= t` for every threshold t, on one split.

    Recall counts every true pair of the split, also those that blocking lost (they can never be found).
    """
    s = evaluate.label_pairs(evaluate.ordered(scored), dataset)
    s = s[s.split == split].sort_values("score", ascending=False)
    n_true = int((evaluate.true_pairs(dataset).split == split).sum())
    tp = np.cumsum(s.same.to_numpy())
    k = np.arange(1, len(s) + 1)
    scores = s.score.to_numpy()
    last = np.r_[scores[1:] != scores[:-1], True]   # one point per distinct score
    return scores[last], (tp / k)[last], (tp / max(n_true, 1))[last]


def best_f1(scored, dataset, split="validation"):
    t, p, r = curve(scored, dataset, split)
    f1 = np.where(p + r > 0, 2 * p * r / np.maximum(p + r, 1e-12), 0)
    i = int(np.argmax(f1))
    return float(t[i])


def for_precision(scored, dataset, target, split="validation"):
    """The lowest threshold whose precision is at least target (the most recall at that precision)."""
    t, p, _ = curve(scored, dataset, split)
    ok = np.where(p >= target)[0]
    return float(t[ok[-1]]) if len(ok) else float(t[0])


def decide(scored, threshold):
    return scored.assign(match=(scored.score >= threshold).astype(int))
