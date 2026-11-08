"""Latency and cost (Module 8, lesson 1): the time of each stage of a search, measured on this computer.

Every stage runs live here (no recorded answer): the query is encoded by the bi-encoder and the candidates are
scored by the cross-encoder on the CPU. The first query of each model is not counted (loading the model).

Cost per 1,000 queries = CPU-seconds per query x the price of one vCPU-second (a server's price per hour / its
vCPUs / 3,600). CPU-seconds = seconds x threads that the stage uses. The price is an assumption (data/costs.json).
"""

import json
import os
import time

import numpy as np

from . import data, dense, index, ltr, rerank, spell
from .paths import data_dir
from .runs.dense import rrf
from .runs.understand import with_synonyms


def stages(queries, rerank_n=50, threads=None):
    """{stage: [ms per query]} for the hybrid pipeline with a cross-encoder, and for the LTR pipeline."""
    if threads:
        os.environ["LARKFIELD_THREADS"] = str(threads)
        import torch
        torch.set_num_threads(threads)
    dense.encode("warm up")
    if rerank_n:
        rerank.live("warm up", list(data.catalogue()["product_id"][:2]))
    ltr.booster("judgments")
    out = {k: [] for k in ("understand", "lexical", "encode", "dense search", "fusion", f"rerank {rerank_n}",
                           "ltr features and model")}
    for q in queries:
        t0 = time.perf_counter()
        fixed = spell.correct(q)[0]
        t1 = time.perf_counter()
        lex = index.top(with_synonyms(fixed), 100)
        t2 = time.perf_counter()
        v = dense.encode(q)
        t3 = time.perf_counter()
        den = dense.top(dense.products() @ v, 100)
        t4 = time.perf_counter()
        fused = rrf([[p for p, _ in lex], [p for p, _ in den]])
        t5 = time.perf_counter()
        for stage, a, b in (("understand", t0, t1), ("lexical", t1, t2), ("encode", t2, t3),
                            ("dense search", t3, t4), ("fusion", t4, t5)):
            out[stage].append((b - a) * 1000)
        if rerank_n:
            t0 = time.perf_counter()
            rerank.live(q, [p for p, _ in fused[:rerank_n]])
            out[f"rerank {rerank_n}"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        ltr.rank(q, None)
        out["ltr features and model"].append((time.perf_counter() - t0) * 1000)
    return {k: v for k, v in out.items() if v}


def usd_per_1000(ms, threads=1):
    price = json.loads((data_dir() / "costs.json").read_text())["cpu_server_usd_per_hour"]["value"]
    per_vcpu_second = price / 4 / 3600
    return 1000 * (ms / 1000) * threads * per_vcpu_second


def summary(times, threads=1):
    rows = {}
    for k, v in times.items():
        a = np.asarray(v)
        rows[k] = {"p50": float(np.percentile(a, 50)), "p95": float(np.percentile(a, 95))}
    return rows


def sizes():
    def mb(p):
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6 if p.exists() else 0.0
    return {"index (FTS5 and BM25)": mb(index.index_dir()), "product embeddings": mb(data_dir() / "embeddings")}
