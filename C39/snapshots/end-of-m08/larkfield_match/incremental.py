"""New records every day (Module 8, lesson 1): match them against the existing entities.

For each new record: make candidate pairs with the same keys as the `keys` blocking (against every known record
and the other new records), score them with the trained LightGBM model, calibrate, then decide:
- probability >= UPPER: a link; the record joins that entity;
- LOWER <= probability < UPPER: the pair goes to the review queue;
- links to two or more different entities: the record joins the entity of its strongest link, and the other
  links go to the review queue ("would join two entities"): a new record never merges two old entities alone;
- no link: the record starts a new entity, LK-<record id>.
Entity IDs never change when a record joins; the history file says what happened.
"""

import pandas as pd

from . import blocking, calibrate, classifier, data, golden, llm, pairs, prepared, vectors
from .paths import data_dir, out
from .runs import learned

LOWER, UPPER = llm.LOWER, llm.UPPER


def day_file(day):
    p = data_dir() / "daily" / f"day-{day}.csv"
    if not p.exists():
        raise SystemExit(f"No file for day {day} (days 1 to 7).")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def prepare_day(df):
    parts = []
    for src in ("shop", "loyalty"):
        sub = df[df.source == src].drop(columns=["source"])
        if len(sub):
            parts.append(prepared.prepare_source(sub, src))
    return pd.concat(parts, ignore_index=True)


def known_records():
    """The course records and every daily record added so far (prepared)."""
    base = prepared.customers()
    p = out("daily_records.pkl")
    return pd.concat([base, pd.read_pickle(p)], ignore_index=True) if p.exists() else base


def _model():
    p = out("models", "lgbm.pkl")
    if not p.exists():
        pairs.get("lgbm")   # trains and saves the model
    return learned.load("lgbm"), calibrate.fit(pairs.get("lgbm", quiet=True))


def run_day(day):
    ents = golden.load_entities()
    if ents is None:
        raise SystemExit("No entities yet: run match golden first.")
    new = prepare_day(day_file(day))
    already = set(ents.record_id)
    new = new[~new.record_id.isin(already)]
    if new.empty:
        raise SystemExit(f"Day {day} is already matched.")
    allrec = pd.concat([known_records(), new], ignore_index=True)
    keys = blocking.customer_keys(allrec)
    cand = blocking.key_pairs(keys, ["postcode", "email", "phone", "surname4", "dob"])
    newset = set(new.record_id)
    cand = cand[cand.record_id_l.isin(newset) | cand.record_id_r.isin(newset)].reset_index(drop=True)
    model, iso = _model()
    v = vectors.customer_vectors(cand, allrec)
    prob = iso.predict(classifier.predict(model, "lgbm", classifier.features(v)))
    scored = cand.assign(probability=prob)
    ent = dict(zip(ents.record_id, ents.entity_id))
    links = scored[scored.probability >= UPPER].sort_values("probability", ascending=False)
    review = [scored[(scored.probability >= LOWER) & (scored.probability < UPPER)].assign(reason="unsure")]
    report = {"day": day, "records": len(new), "joined": 0, "new_entities": 0, "two_entities": 0}
    for rid in sorted(newset):
        mine = links[(links.record_id_l == rid) | (links.record_id_r == rid)]
        others = [b if a == rid else a for a, b in zip(mine.record_id_l, mine.record_id_r)]
        targets = [ent[o] for o in others if o in ent]
        if not targets:
            ent[rid] = f"LK-{rid}"
            report["new_entities"] += 1
            golden.log("new", record=rid, entity=ent[rid], day=day)
            continue
        ent[rid] = targets[0]
        report["joined"] += 1
        golden.log("join", record=rid, entity=targets[0], day=day)
        if len(set(targets)) > 1:
            report["two_entities"] += 1
            extra = mine[[ent.get(b if a == rid else a) != targets[0] for a, b in zip(mine.record_id_l,
                                                                                     mine.record_id_r)]]
            review.append(extra.assign(reason="would join two entities"))
            golden.log("two_entities", record=rid, kept=targets[0], others=sorted(set(targets) - {targets[0]}),
                       day=day)
    q = pd.concat(review, ignore_index=True)
    q = q.assign(day=day)[["record_id_l", "record_id_r", "probability", "reason", "day"]]
    qp = out("review_queue.csv")
    q.to_csv(qp, mode="a", header=not qp.exists(), index=False)
    report["review"] = len(q)
    ents = pd.DataFrame({"record_id": list(ent), "entity_id": list(ent.values())})
    golden.save_entities(ents)
    dp = out("daily_records.pkl")
    prev = pd.read_pickle(dp) if dp.exists() else None
    pd.concat([prev, new] if prev is not None else [new], ignore_index=True).to_pickle(dp)
    report.update(accuracy(ents, new.record_id.tolist()))
    return report


def all_truth():
    t = data.truth()[["record_id", "entity_id"]]
    p = data_dir() / "daily" / "truth.csv"
    d = pd.read_csv(p, dtype=str)[["record_id", "entity_id"]]
    return pd.concat([t, d], ignore_index=True)


def accuracy(ents, new_ids):
    """For the new records: right joins, wrong joins, and records that started a new entity although their
    true customer was already known."""
    truth = dict(zip(*all_truth().T.values))
    members = ents.groupby("entity_id").record_id.apply(list).to_dict()
    e = dict(zip(ents.record_id, ents.entity_id))
    known_true = {truth[r] for r in e if r not in new_ids and r in truth}
    right = wrong = missed = 0
    for r in new_ids:
        others = [o for o in members[e[r]] if o != r]
        if others:
            if any(truth.get(o) == truth[r] for o in others):
                right += 1
            else:
                wrong += 1
        elif truth[r] in known_true:
            missed += 1
    return {"right_joins": right, "wrong_joins": wrong, "missed_known": missed}
