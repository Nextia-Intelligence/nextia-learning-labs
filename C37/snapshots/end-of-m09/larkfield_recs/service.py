"""The recommendation service (FastAPI): reads the batch files, answers in milliseconds, falls back to trending.

    recs batch two-stage      # each night
    recs serve --port 8037    # then open http://127.0.0.1:8037/recommend/C100123
"""

import time

from fastapi import FastAPI, HTTPException

from .serving import Server


def create_app(server=None):
    app = FastAPI(title="Larkfield recommendations")
    state = {"server": server}

    def srv():
        if state["server"] is None:
            state["server"] = Server()
        return state["server"]

    @app.get("/health")
    def health():
        s = srv()
        return {"status": "ok", "model": (s.meta or {}).get("method"), "customers_with_lists": len(s.lists),
                "fallback_only": s.meta is None}

    @app.get("/recommend/{customer_id}")
    def recommend(customer_id: str, k: int = 10, surface: str = "home"):
        t0 = time.perf_counter()
        items, source, reason = srv().recommend(customer_id, k, surface)
        return {"customer_id": customer_id, "surface": surface, "source": source, "reason": reason,
                "products": srv().describe(items), "ms": round(1000 * (time.perf_counter() - t0), 3)}

    @app.get("/similar/{product_id}")
    def similar(product_id: str, k: int = 10):
        if product_id not in srv().shop.product_index:
            raise HTTPException(404, f"no product {product_id}")
        items, source = srv().similar(product_id, k)
        return {"product_id": product_id, "source": source, "products": srv().describe(items)}

    return app
