"""Larkfield's synthetic world: customers, the calendar and how customers visit and buy.

Everything here is synthetic: we made it for the course. There are no real people.

The key idea of the simulator is in `simulate_test`: for every visit, it draws the random numbers once and uses
them for both versions of the shop (with and without the change). So it knows what each customer would have
done in both worlds, and the true effect is the difference between the two worlds. A real test sees only one.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

PROVINCES = ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE"]
PROVINCE_SHARE = [0.38, 0.22, 0.14, 0.12, 0.04, 0.03, 0.03, 0.02, 0.01, 0.01]

# Days that change how people shop (Canada). Thanksgiving is the second Monday of October.
HOLIDAYS = {
    date(2024, 9, 2): "Labour Day", date(2024, 10, 14): "Thanksgiving", date(2024, 11, 29): "Black Friday",
    date(2024, 12, 25): "Christmas", date(2025, 1, 1): "New Year", date(2025, 4, 18): "Good Friday",
    date(2025, 5, 19): "Victoria Day", date(2025, 7, 1): "Canada Day", date(2025, 9, 1): "Labour Day",
    date(2025, 10, 13): "Thanksgiving", date(2025, 11, 28): "Black Friday", date(2025, 12, 25): "Christmas",
}
WEEKDAY = np.array([0.92, 0.95, 0.97, 1.0, 1.02, 1.08, 1.06])  # Monday ... Sunday: more visits at the weekend
TEST_START = date(2025, 9, 8)  # a Monday: the A/B tests of the course start here
BASKET_MEAN = 85.0  # dollars, the average order before the customer's own level
RETURN_RATE = 0.08  # share of orders returned


def daterange(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(days)]


def season(d: date) -> float:
    """Home and garden: high in spring and early summer, a second smaller peak before Christmas."""
    doy = d.timetuple().tm_yday
    spring = 0.22 * np.exp(-(((doy - 150) / 45) ** 2))
    winter = 0.12 * np.exp(-(((doy - 340) / 25) ** 2))
    return float(1.0 + spring + winter)


def holiday_lift(d: date) -> float:
    """Shopping rises in the days around a holiday weekend (synthetic values)."""
    for h, name in HOLIDAYS.items():
        gap = (d - h).days
        if name == "Thanksgiving" and -4 <= gap <= 0:
            return 1.12
        if name == "Black Friday" and 0 <= gap <= 3:
            return 1.9
        if name == "Christmas" and -10 <= gap <= -3:
            return 1.3
        if gap == 0:
            return 0.9  # the holiday itself: people are away from screens
    return 1.0


@dataclass
class Population:
    """Customers and their fixed habits. Arrays are indexed by customer."""

    customer_id: np.ndarray
    province: np.ndarray
    device: np.ndarray  # "mobile" or "desktop": the device they use most
    tenure_days: np.ndarray  # days since their first order
    activity: np.ndarray  # how often they visit (1 = average)
    conv: np.ndarray  # chance that a visit ends with an order
    basket: np.ndarray  # their usual order value in dollars
    pre_spend: np.ndarray = field(default=None)  # spending in the 8 weeks before the test
    pre_orders: np.ndarray = field(default=None)

    def __len__(self):
        return len(self.customer_id)

    @property
    def new(self) -> np.ndarray:
        return self.tenure_days < 90

    def table(self, idx=None) -> pd.DataFrame:
        idx = np.arange(len(self)) if idx is None else idx
        return pd.DataFrame({
            "customer_id": self.customer_id[idx], "province": self.province[idx], "device": self.device[idx],
            "new_customer": self.new[idx].astype(int), "tenure_days": self.tenure_days[idx],
            "pre_orders": self.pre_orders[idx], "pre_spend": np.round(self.pre_spend[idx], 2),
        })


def make_population(n: int, rng: np.random.Generator, visits_per_week: float = 0.45) -> Population:
    """n customers with habits that differ from person to person."""
    province = rng.choice(PROVINCES, size=n, p=PROVINCE_SHARE)
    device = np.where(rng.random(n) < 0.58, "mobile", "desktop")
    new = rng.random(n) < 0.3
    tenure = np.where(new, rng.integers(1, 90, n), rng.integers(90, 2200, n))
    activity = rng.gamma(shape=0.55, scale=1 / 0.55, size=n)
    loyal = np.log1p(tenure / 365)
    logit = -2.9 + 0.35 * loyal + 0.25 * np.log(activity + 0.05) - 0.25 * (device == "mobile")
    conv = 1 / (1 + np.exp(-(logit + rng.normal(0, 0.7, n))))
    basket = BASKET_MEAN * rng.lognormal(-0.15, 0.55, n)
    pop = Population(np.array([f"C{i:06d}" for i in range(1, n + 1)]), province, device, tenure, activity,
                     conv, basket)
    pop.visit_rate = visits_per_week / 7 * activity
    # The 8 weeks before the test: the same habits, other days (used by CUPED in Module 3).
    visits = rng.poisson(pop.visit_rate * 56)
    orders = rng.binomial(visits, conv)
    owner = np.repeat(np.arange(n), orders)
    spend = basket * np.bincount(owner, weights=rng.lognormal(-0.1, 0.45, len(owner)), minlength=n)
    pop.pre_orders, pop.pre_spend = orders, spend
    return pop


@dataclass
class Effect:
    """How the change alters one visit of a treated customer. Each value is an array (one per visit).

    conv: multiplies the chance of an order; basket: multiplies the order value; returns: adds to the chance
    that an order is returned."""

    conv: np.ndarray | float = 1.0
    basket: np.ndarray | float = 1.0
    returns: np.ndarray | float = 0.0


def simulate_test(pop: Population, rng: np.random.Generator, days: int, start: date, variant: np.ndarray,
                  effect, lose=None, potentials=False):
    """Simulates `days` days of traffic. `variant` is 0 (control) or 1 (treatment) per customer.

    effect(idx, day, since_first) returns the Effect for the visits of customers `idx` on day number `day`,
    where since_first is the number of days since each customer's first visit in the test.
    lose(idx, first) (optional) returns True for visits that the logging loses (a bug), only for planted problems.
    potentials=True adds the revenue of each visit in both worlds (columns _rev0, _rev1, _since: the truth).

    Returns (visits, outcomes): visits is the log a real test would see (one row per visit, observed version
    only); outcomes has, per customer who visited, the totals in both worlds (y0_*, y1_*): the simulator's truth.
    """
    n = len(pop)
    first = np.full(n, -1)
    tot = {k: np.zeros(n) for k in ("visits", "y0_orders", "y1_orders", "y0_revenue", "y1_revenue",
                                    "y0_returns", "y1_returns")}
    rows = []
    for day, d in enumerate(daterange(start, days)):
        p = np.minimum(pop.visit_rate * WEEKDAY[d.weekday()] * season(d) * holiday_lift(d), 0.9)
        idx = np.nonzero(rng.random(n) < p)[0]
        is_first = first[idx] < 0
        first[idx[is_first]] = day
        since = day - first[idx]
        e = effect(idx, day, since)
        u_order, u_return = rng.random(len(idx)), rng.random(len(idx))
        value = pop.basket[idx] * rng.lognormal(-0.1, 0.45, len(idx))
        p0 = pop.conv[idx]
        p1 = np.minimum(p0 * e.conv, 0.95)
        o0, o1 = u_order < p0, u_order < p1
        r0, r1 = value * o0, value * e.basket * o1
        ret0 = o0 & (u_return < RETURN_RATE)
        ret1 = o1 & (u_return < RETURN_RATE + e.returns)
        np.add.at(tot["visits"], idx, 1)
        for k, a in (("y0_orders", o0), ("y1_orders", o1), ("y0_revenue", r0), ("y1_revenue", r1),
                     ("y0_returns", ret0), ("y1_returns", ret1)):
            np.add.at(tot[k], idx, a)
        v = variant[idx]
        keep = np.ones(len(idx), bool) if lose is None else ~lose(idx, is_first)
        row = pd.DataFrame({
            "date": d.isoformat(), "customer_id": pop.customer_id[idx][keep], "variant": np.where(v, "B", "A")[keep],
            "ordered": np.where(v, o1, o0)[keep].astype(int),
            "revenue": np.round(np.where(v, r1, r0), 2)[keep],
            "returned": np.where(v, ret1, ret0)[keep].astype(int),
        })
        if potentials:
            row["_rev0"], row["_rev1"], row["_since"] = r0[keep], r1[keep], since[keep]
        rows.append(row)
    visits = pd.concat(rows, ignore_index=True)
    seen = np.nonzero(first >= 0)[0]
    out = pop.table(seen)
    out.insert(1, "variant", np.where(variant[seen], "B", "A"))
    out.insert(2, "first_visit", [(start + timedelta(days=int(x))).isoformat() for x in first[seen]])
    for k, a in tot.items():
        out[k] = np.round(a[seen], 2) if "revenue" in k else a[seen].astype(int)
    return visits, out


def per_customer(visits: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """The table a real test has: one row per customer seen in the log, with the observed totals only."""
    g = visits.groupby("customer_id").agg(variant=("variant", "first"), first_visit=("date", "min"),
                                          visits=("date", "size"), orders=("ordered", "sum"),
                                          revenue=("revenue", "sum"), returns=("returned", "sum"))
    g["revenue"] = g["revenue"].round(2)
    keep = ["customer_id", "province", "device", "new_customer", "tenure_days", "pre_orders", "pre_spend"]
    return g.reset_index().merge(outcomes[keep], on="customer_id", how="left")


def truth_of(outcomes: pd.DataFrame) -> dict:
    """The true effects among the customers who visited: the mean of (treated world − control world)."""
    n = len(outcomes)
    rev0, rev1 = outcomes["y0_revenue"].mean(), outcomes["y1_revenue"].mean()
    ord0, ord1 = outcomes["y0_orders"].mean(), outcomes["y1_orders"].mean()
    conv0, conv1 = (outcomes["y0_orders"] > 0).mean(), (outcomes["y1_orders"] > 0).mean()
    ret0 = outcomes["y0_returns"].sum() / max(outcomes["y0_orders"].sum(), 1)
    ret1 = outcomes["y1_returns"].sum() / max(outcomes["y1_orders"].sum(), 1)
    return _plain({
        "customers": n,
        "revenue": {"control_world": round(float(rev0), 4), "treated_world": round(float(rev1), 4), "effect": round(float(rev1 - rev0), 4),
                    "relative": round((rev1 - rev0) / rev0, 4), "unit": "dollars per customer"},
        "orders": {"control_world": round(float(ord0), 5), "treated_world": round(float(ord1), 5), "effect": round(float(ord1 - ord0), 5),
                   "relative": round((ord1 - ord0) / ord0, 4), "unit": "orders per customer"},
        "converted": {"control_world": round(float(conv0), 5), "treated_world": round(float(conv1), 5),
                      "effect": round(float(conv1 - conv0), 5), "relative": round((conv1 - conv0) / conv0, 4),
                      "unit": "share of customers with an order"},
        "return_rate": {"control_world": round(float(ret0), 5), "treated_world": round(float(ret1), 5),
                        "effect": round(float(ret1 - ret0), 5), "relative": round((ret1 - ret0) / ret0, 4),
                        "unit": "returns per order"},
    })


def _plain(x):
    """NumPy numbers to plain Python numbers, for JSON."""
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x.item() if hasattr(x, "item") else x
