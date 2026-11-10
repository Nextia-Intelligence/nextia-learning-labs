"""recs bench: how fast is a suggestion? Batch lookup through the service against scoring at request time."""

import time

import numpy as np

from .. import data, registry, serving
from ..service import create_app

NAME = "bench"
HELP = "Time suggestions: batch lookup through the service (with and without a model) and scoring at request time."


def add(p):
    p.add_argument("--requests", type=int, default=500)


def pct(ms):
    return f"p50 {np.percentile(ms, 50):.2f} ms, p95 {np.percentile(ms, 95):.2f} ms"


def run(args):
    from fastapi.testclient import TestClient
    shop = data.load()
    srv = serving.Server(shop)
    if srv.meta is None:
        print("No batch files: run `recs batch` first for the model lookup (the fallback is timed anyway).")
    rng = np.random.default_rng(37)
    ids = shop.customer_ids[rng.integers(0, shop.n_customers, args.requests)]
    with TestClient(create_app(srv)) as client:
        client.get("/health")
        ms = []
        for c in ids:
            t0 = time.perf_counter()
            r = client.get(f"/recommend/{c}")
            ms.append(1000 * (time.perf_counter() - t0))
            assert r.status_code == 200
        print(f"service, batch lookup ({(srv.meta or {}).get('method', 'fallback only')}), {args.requests} requests: {pct(ms)}")
    p = serving.now_period(shop)
    users = np.array([shop.customer_index[c] for c in ids[:100]])
    for name in ("als", "two-stage"):
        t0 = time.perf_counter()
        m = registry.make(name, p).fit()
        fit = time.perf_counter() - t0
        ms = []
        for u in users:
            t0 = time.perf_counter()
            m.recommend(np.array([u]), 10)
            ms.append(1000 * (time.perf_counter() - t0))
        print(f"{name} at request time (model in memory, 100 customers): {pct(ms)}; training took {fit:.1f} s")
