"""Turn a run's scores into probabilities that mean what they say (calibration on the validation pairs).

A classifier trained on the labelled pairs (one in three is a true pair) gives scores that are far too high for
candidate pairs (one in forty is a true pair). Isotonic regression on the validation pairs maps each score to the
share of true pairs among validation pairs with a similar score. See the machine learning course for calibration.
"""

import numpy as np

from . import evaluate


def fit(scored, dataset="customers"):
    from . import torch_first
    torch_first()
    from sklearn.isotonic import IsotonicRegression
    lab = evaluate.label_pairs(evaluate.ordered(scored), dataset)
    v = lab[lab.split == "validation"]
    return IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(v.score.to_numpy(), v.same.to_numpy())


def calibrated(scored, dataset="customers"):
    """The same pairs with a `probability` column (calibrated on the validation pairs)."""
    iso = fit(scored, dataset)
    return scored.assign(probability=np.clip(iso.predict(scored.score.to_numpy()), 0.0, 1.0))
