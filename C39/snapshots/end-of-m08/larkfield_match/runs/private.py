"""Matching on hashed and encoded values (Module 8, lesson 4).

Blocking: the keys of the `keys` blocking can be hashed with the same secret key; equal values give equal hashes,
so the candidate pairs are the same as `keys`. The runs below read only encoded values.
"""


from .. import blocking, classifier, evaluate, privacy, thresholds
from ..paths import out


def _encoded():
    p = out("encoded_customers.pkl")
    if p.exists():
        import pandas as pd
        return pd.read_pickle(p)
    enc = privacy.encode()
    enc.to_pickle(p)
    return enc


def hashed_rules():
    """The four rules of Module 2 on hashed values: email, or phone and surname, or name and date of birth, or name
    and postcode (a Bloom filter row counts as equal only when it is the same row)."""
    enc = _encoded()
    c = blocking.candidates(blocking.DEFAULT["customers"])
    v = privacy.encoded_vectors(c, enc)
    same_last = v.last_dice == 1.0
    same_name = same_last & (v.first_dice == 1.0)
    m = (v.email_eq == 1) | ((v.phone_eq == 1) & same_last) | (same_name & (v.dob_eq == 1)) | \
        (same_name & (v.postcode_eq == 1))
    return v[["record_id_l", "record_id_r"]].assign(score=m.astype(float), match=m.astype(int))


def bloom_lgbm():
    """LightGBM on the encoded comparison vector (Dice of Bloom filters, equality of hashes), 3,000 labelled pairs."""
    from .. import data
    enc = _encoded()
    lp = evaluate.ordered(data.labelled_pairs())
    xt = privacy.encoded_vectors(lp[["record_id_l", "record_id_r"]].reset_index(drop=True), enc)
    model = classifier.fit("lgbm", xt[privacy.ENCODED_FIELDS], lp.label.to_numpy())
    c = blocking.candidates(blocking.DEFAULT["customers"])
    v = privacy.encoded_vectors(c, enc)
    p = classifier.predict(model, "lgbm", v[privacy.ENCODED_FIELDS])
    scored = v[["record_id_l", "record_id_r"]].assign(score=p)
    return thresholds.decide(scored, thresholds.best_f1(scored, "customers"))


RUNS = {
    "hashed-rules": ("customers", hashed_rules, "the four rules on hashed values only"),
    "bloom-lgbm": ("customers", bloom_lgbm, ("LightGBM on Bloom filter encodings and hashes only; best F1 threshold "
                   "on validation")),
}
