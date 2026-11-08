"""Probabilistic linkage with Splink on DuckDB (Module 5, lesson 2).

Splink learns the m and u probabilities of each comparison level without labels: u from random pairs, the share
of true matches from pairs that agree on email, and m with expectation maximisation on pairs blocked by the date
of birth, then by the full name. It then scores the candidate pairs of the same blocking rules as the project's
`keys` blocking.

The project uses the match weight as the score, not the match probability: on these records the probabilities
are far too sure (people in one household share a postcode, a phone, a street and a surname, and Splink adds
these as if they were separate evidence), and many pairs get a probability of exactly 1.0.
"""

import json
import logging
import time

import duckdb
import pandas as pd

from . import prepared
from .paths import out

COLUMNS = ["first", "last", "email", "phone", "postcode", "street", "town", "dob"]
THREADS = 4
MEMORY_LIMIT = "4GB"


def EM_RULES():
    from splink import block_on
    return [block_on("dob"), block_on("first", "last")]


def settings():
    import splink.comparison_library as cl
    from splink import SettingsCreator, block_on
    return SettingsCreator(
        link_type="dedupe_only",
        unique_id_column_name="record_id",
        comparisons=[
            cl.JaroWinklerAtThresholds("first", [0.92, 0.8]),
            cl.JaroWinklerAtThresholds("last", [0.92]).configure(term_frequency_adjustments=True),
            cl.EmailComparison("email"),
            cl.ExactMatch("phone"),
            cl.ExactMatch("postcode"),
            cl.JaroWinklerAtThresholds("street", [0.9]),
            cl.ExactMatch("town"),
            cl.DateOfBirthComparison("dob", input_is_string=True, datetime_format="%Y-%m-%d"),
        ],
        blocking_rules_to_generate_predictions=[
            block_on("postcode"), block_on("email"), block_on("phone"),
            block_on("substr(last, 1, 4)", "substr(first, 1, 2)"), block_on("dob", "substr(first, 1, 1)"),
        ],
        retain_intermediate_calculation_columns=True,
    )


def table(df=None):
    """The prepared customers in Splink's form: empty values become NULL (Splink treats NULL as missing)."""
    df = prepared.customers() if df is None else df
    t = df[["record_id"] + COLUMNS].copy()
    t["last"] = t["last"].str.replace(" ", "")
    return t.replace("", None)


def _api():
    from splink.backends.duckdb import DuckDBAPI
    con = duckdb.connect()
    con.execute(f"SET threads = {THREADS}; SET memory_limit = '{MEMORY_LIMIT}'")
    return DuckDBAPI(connection=con)


def train(df=None, seed=1, quiet=True):
    """Trains a Splink model without labels; returns the linker and the seconds it took."""
    from splink import Linker, block_on
    if quiet:
        logging.getLogger("splink").setLevel(logging.WARNING)
    t0 = time.perf_counter()
    api = _api()
    linker = Linker(api.register(table(df)), settings())
    linker.training.estimate_probability_two_random_records_match([block_on("email")], recall=0.45)
    linker.training.estimate_u_using_random_sampling(max_pairs=2e6, seed=seed)
    for rule in EM_RULES():
        linker.training.estimate_parameters_using_expectation_maximisation(rule)
    return linker, time.perf_counter() - t0


def predict(linker, threshold=0.001):
    """Every candidate pair with match probability >= threshold, with match weights and Bayes factors."""
    df = linker.inference.predict(threshold_match_probability=threshold).as_pandas_dataframe()
    df = df.rename(columns={"record_id_l": "record_id_l", "record_id_r": "record_id_r"})
    return df


def model_path():
    return out("models", "splink.json")


def save(linker):
    p = model_path()
    if p.exists():
        p.unlink()
    linker.misc.save_model_to_json(str(p), overwrite=True)
    return p


def load():
    from splink import Linker
    logging.getLogger("splink").setLevel(logging.WARNING)
    api = _api()
    return Linker(api.register(table()), str(model_path()))


def weights_table(path=None):
    """Every comparison level of the saved model: its m, u and match weight log2(m / u)."""
    import math
    m = json.loads((path or model_path()).read_text())
    rows = []
    for c in m["comparisons"]:
        for lvl in c["comparison_levels"]:
            if lvl.get("is_null_level"):
                continue
            mp, up = lvl.get("m_probability"), lvl.get("u_probability")
            w = math.log2(mp / up) if mp and up else None
            rows.append({"field": c["output_column_name"], "level": lvl["label_for_charts"], "m": mp, "u": up,
                         "weight": w})
    return pd.DataFrame(rows), m["probability_two_random_records_match"]


def explain(linker, record_l, record_r):
    """The waterfall of one pair: the prior weight, then each field's match weight, then the total."""
    import math
    t = table().set_index("record_id")
    rec = [{k: (None if pd.isna(v) else str(v)) for k, v in t.loc[r].to_dict().items()} | {"record_id": r}
           for r in (record_l, record_r)]
    row = linker.inference.score_pair(rec[0], rec[1]).as_pandas_dataframe().iloc[0]
    prior = linker._settings_obj._probability_two_random_records_match
    steps = [("prior (two random records)", math.log2(prior / (1 - prior)), "")]
    for c in COLUMNS:
        w = float(row.get(f"mw_{c}", 0.0) or 0.0) + float(row.get(f"mw_tf_adj_{c}", 0.0) or 0.0)
        steps.append((c, w, f"{row.get(f'{c}_l')} / {row.get(f'{c}_r')}"))
    return steps, float(row["match_weight"]), float(row["match_probability"])
