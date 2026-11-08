"""Two stages: candidates from several sources, then a learned ranker (LightGBM LambdaMART).

Stage 1 (candidates, fast): trending (100), item-item CF (100), ALS (100), content (50) and the customer's own
recent products (viewed or added to the basket in the last 30 days). About 300 different products per customer.
Stage 2 (ranker, careful): features of the customer, the product and the pair; LightGBM with objective
"lambdarank" learns to put the products that were ordered first.

Training without leakage: the ranker learns on the two weeks BEFORE the period (candidates and features from the
events before those two weeks, labels = the orders in them), then ranks the period's candidates (candidates and
features from the events before the period). Negative sampling: for each customer, every ordered candidate and
`negatives` (default 100) random candidates that were not ordered.
"""

import time

import numpy as np
import pandas as pd

from .. import data
from . import Method, fill, top_k
from .content import Content
from .mf import Factorisation
from .neighbours import ItemItem
from .popular import popular_list, popularity

SOURCES = {"trending": 100, "item_cf": 100, "als": 100, "content": 50, "recent": 30}
FEATURES = [
    "trending_rank", "item_cf_score", "item_cf_rank", "als_score", "als_rank", "content_score", "content_rank",
    "recent_rank", "n_sources", "pop_all", "pop_28", "pop_7", "season_ratio", "log_price", "product_age",
    "user_views_30", "user_baskets_30", "user_bought_before", "days_since_user_touch", "cat_share",
    "subcat_share", "style_share", "user_orders", "user_events_30", "user_days_since_last", "repeat_product",
]


def _top(scores, n, allowed):
    rec = top_k(scores, n, allowed)
    sc = np.take_along_axis(scores, np.maximum(rec, 0), axis=1)
    return rec, sc


class Stage:
    """The candidate models and the feature tables for one cut-off (one Period)."""

    def __init__(self, period):
        self.p = period
        shop = period.shop
        self.cf = ItemItem(period, kind="cosine").fit()
        self.als = Factorisation(period, algo="als").fit()
        self.content = Content(period).fit()
        tr = period.train
        t = period.start_day
        self.pop_all = np.log1p(popularity(period))
        self.pop_28 = np.log1p(popularity(period, 28))
        self.pop_7 = np.log1p(popularity(period, 7))
        o = tr[tr.event == "order"]
        last28 = np.bincount(o[o.day >= t - 28].p, minlength=shop.n_products)
        year = np.bincount(o[o.day >= t - 365].p, minlength=shop.n_products) / 13.0
        self.season_ratio = (last28 + 1) / (year + 1)
        self.log_price = np.log(shop.products.price.to_numpy())
        self.age = np.minimum(t - shop.added_day, 999)
        self.repeat = (shop.products.repeat_days.to_numpy() > 0).astype(float)
        _cats, self.cat_of = np.unique(shop.products.category.to_numpy(), return_inverse=True)
        _subs, self.sub_of = np.unique(shop.products.subcategory.to_numpy(), return_inverse=True)
        _styles, self.style_of = np.unique(shop.products["style"].fillna("").to_numpy(), return_inverse=True)
        self.styled = shop.products["style"].fillna("").to_numpy() != ""
        recent = tr[tr.day >= t - 30]
        self.recent = recent
        self.user_orders = period.orders_before
        self.user_events_30 = np.bincount(recent.c, minlength=shop.n_customers)
        last = tr.groupby("c").day.max()
        self.user_last = np.full(shop.n_customers, 9999)
        self.user_last[last.index.to_numpy()] = t - last.to_numpy()
        w = tr.event.map({"view": 1.0, "basket": 3.0, "order": 5.0}).astype(float).to_numpy()
        self.uc = pd.DataFrame({"c": tr.c, "k": self.cat_of[tr.p], "w": w}).groupby(["c", "k"]).w.sum()
        self.us = pd.DataFrame({"c": tr.c, "k": self.sub_of[tr.p], "w": w}).groupby(["c", "k"]).w.sum()
        st = tr[self.styled[tr.p]]
        self.ust = pd.DataFrame({"c": st.c, "k": self.style_of[st.p]}).groupby(["c", "k"]).size()
        self.utot = pd.Series(w).groupby(tr.c.to_numpy()).sum()
        self.ustot = self.ust.groupby(level=0).sum()
        self.touch = tr.groupby(["c", "p"]).day.max()
        self.bought = set(zip(o.c.to_numpy().tolist(), o.p.to_numpy().tolist()))
        self.fallback = popular_list(period, days=28)

    def candidates(self, users):
        _p, allowed = self.p, self.p.available
        parts = []
        trend = top_k(self.pop_28[None, :], SOURCES["trending"], allowed)[0]
        parts.append(pd.DataFrame({"u": np.repeat(users, len(trend)), "p": np.tile(trend, len(users)),
                                   "trending_rank": np.tile(np.arange(1, len(trend) + 1), len(users))}))
        for name, model in (("item_cf", self.cf), ("als", self.als), ("content", self.content)):
            for start in range(0, len(users), 2000):
                u = users[start:start + 2000]
                s = model.scores(u).astype(float)
                if name == "item_cf":
                    s[s <= 0] = -np.inf
                rec, sc = _top(s, SOURCES[name], allowed)
                ok = rec >= 0
                rank = np.tile(np.arange(1, rec.shape[1] + 1), (len(u), 1))
                parts.append(pd.DataFrame({"u": np.repeat(u, rec.shape[1])[ok.ravel()], "p": rec[ok],
                                           f"{name}_score": sc[ok], f"{name}_rank": rank[ok]}))
        r = self.recent[self.recent.c.isin(users)]
        r = r[r.event.isin(["view", "basket"])].groupby(["c", "p"]).day.max().reset_index()
        r = r.sort_values(["c", "day"], ascending=[True, False])
        r["recent_rank"] = r.groupby("c").cumcount() + 1
        r = r[r.recent_rank <= SOURCES["recent"]]
        r = r[allowed[r.p.to_numpy()]]
        parts.append(r.rename(columns={"c": "u"})[["u", "p", "recent_rank"]])
        cand = pd.concat(parts, ignore_index=True).groupby(["u", "p"], sort=True).first().reset_index()
        return cand

    def features(self, cand):
        u, p = cand.u.to_numpy(), cand.p.to_numpy()
        f = cand.copy()
        for name in ("trending", "item_cf", "als", "content", "recent"):
            if f"{name}_rank" not in f:
                f[f"{name}_rank"] = np.nan
            f[f"{name}_rank"] = f[f"{name}_rank"].fillna(999)
        for name in ("item_cf", "als", "content"):
            f[f"{name}_score"] = f[f"{name}_score"].fillna(0.0) if f"{name}_score" in f else 0.0
        f["n_sources"] = sum((f[f"{n}_rank"] < 999).astype(int) for n in ("trending", "item_cf", "als", "content", "recent"))
        f["pop_all"], f["pop_28"], f["pop_7"] = self.pop_all[p], self.pop_28[p], self.pop_7[p]
        f["season_ratio"], f["log_price"], f["product_age"] = self.season_ratio[p], self.log_price[p], self.age[p]
        rc = self.recent[self.recent.c.isin(np.unique(u))]
        views = rc[rc.event == "view"].groupby(["c", "p"]).size()
        baskets = rc[rc.event == "basket"].groupby(["c", "p"]).size()
        key = pd.MultiIndex.from_arrays([u, p])
        f["user_views_30"] = views.reindex(key).fillna(0).to_numpy()
        f["user_baskets_30"] = baskets.reindex(key).fillna(0).to_numpy()
        f["user_bought_before"] = [float((a, b) in self.bought) for a, b in zip(u.tolist(), p.tolist())]
        f["days_since_user_touch"] = (self.p.start_day - self.touch.reindex(key).to_numpy()).astype(float)
        f["days_since_user_touch"] = f["days_since_user_touch"].fillna(999).clip(upper=999)
        tot = self.utot.reindex(u).fillna(0).to_numpy().copy()
        tot[tot == 0] = 1
        f["cat_share"] = self.uc.reindex(pd.MultiIndex.from_arrays([u, self.cat_of[p]])).fillna(0).to_numpy() / tot
        f["subcat_share"] = self.us.reindex(pd.MultiIndex.from_arrays([u, self.sub_of[p]])).fillna(0).to_numpy() / tot
        stot = self.ustot.reindex(u).fillna(0).to_numpy()
        sty = self.ust.reindex(pd.MultiIndex.from_arrays([u, self.style_of[p]])).fillna(0).to_numpy()
        f["style_share"] = np.where(self.styled[p] & (stot > 0), sty / np.maximum(stot, 1), -1.0)
        f["user_orders"] = self.user_orders[u]
        f["user_events_30"] = self.user_events_30[u]
        f["user_days_since_last"] = np.minimum(self.user_last[u], 999)
        f["repeat_product"] = self.repeat[p]
        return f


class TwoStage(Method):
    def fit(self):
        import lightgbm as lgb
        s = self.settings
        t0 = time.perf_counter()
        days = s.get("train_days", 14)
        before = data.Period(self.shop, "ranker-train", start_day=self.period.start_day - days,
                             end_day=self.period.start_day - 1)
        stage = Stage(before)
        rng = np.random.default_rng(s.get("seed", 37))
        cand = stage.candidates(before.users)
        truth = pd.DataFrame({"u": np.repeat(before.users, [len(t) for t in before.truth]),
                              "p": np.concatenate(before.truth) if before.truth else []})
        truth["label"] = 1
        cand = cand.merge(truth, on=["u", "p"], how="left")
        cand["label"] = cand.label.fillna(0).astype(int)
        self.train_candidate_recall = float(cand.label.sum() / max(len(truth), 1))
        neg = s.get("negatives", 100)
        cand["r"] = rng.random(len(cand))
        cand["nr"] = cand[cand.label == 0].groupby("u").r.rank(method="first")
        keep = (cand.label == 1) | (cand.nr <= neg)
        groups_with_pos = cand[cand.label == 1].u.unique()
        cand = cand[keep & cand.u.isin(groups_with_pos)].sort_values("u")
        feats = stage.features(cand.drop(columns=["label", "r", "nr"]))
        self.ranker = lgb.LGBMRanker(objective="lambdarank", n_estimators=s.get("trees", 300),
                                     learning_rate=s.get("learning_rate", 0.05), num_leaves=s.get("leaves", 31),
                                     min_child_samples=20, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                     random_state=s.get("seed", 37), n_jobs=1, verbose=-1)
        group = feats.groupby("u", sort=True).size().to_numpy()
        self.ranker.fit(feats[FEATURES], cand.label.to_numpy(), group=group)
        self.train_rows, self.train_customers = len(feats), len(group)
        self.train_positives = int(cand.label.sum())
        gain = self.ranker.booster_.feature_importance("gain")
        self.importance = sorted(zip(FEATURES, gain / gain.sum()), key=lambda x: -x[1])
        self.stage = Stage(self.period)
        self.fit_seconds = time.perf_counter() - t0
        return self

    def rank(self, users):
        cand = self.stage.candidates(users)
        feats = self.stage.features(cand)
        feats["score"] = self.ranker.predict(feats[FEATURES])
        return feats

    def recommend(self, users, k=10):
        out = np.full((len(users), k), -1)
        pos = {u: i for i, u in enumerate(users)}
        for start in range(0, len(users), 1000):
            f = self.rank(users[start:start + 1000])
            f = f.sort_values(["u", "score"], ascending=[True, False])
            f["r"] = f.groupby("u").cumcount()
            f = f[f.r < k]
            out[[pos[x] for x in f.u.to_numpy()], f.r.to_numpy()] = f.p.to_numpy()
        return fill(out, self.stage.fallback)

    def candidate_recall(self, users, truth):
        """Share of the ordered products that are among the candidates, for each source and for all together."""
        cand = self.stage.candidates(users)
        t = pd.DataFrame({"u": np.repeat(users, [len(x) for x in truth]), "p": np.concatenate(truth)})
        m = t.merge(cand, on=["u", "p"], how="left")
        out = {name: float(m[f"{name}_rank"].notna().mean()) for name in SOURCES}
        out["all"] = float(m.drop(columns=["u", "p"]).notna().any(axis=1).mean())
        out["candidates_per_customer"] = float(len(cand) / len(users))
        return out


METHODS = {
    "two-stage": (TwoStage, {}, "candidates from 5 sources, then a LightGBM LambdaMART ranker"),
}
