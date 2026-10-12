"""Usage limits per shop (Module 6): a demo that is open to others must not run up a bill.

Before a question: refuse with 429 limit_reached when the shop has asked DAILY_QUESTION_LIMIT
questions today, or spent MONTHLY_BUDGET_USD on the model this month. After an answer: add one
question and its cost to the shop's day (table usage_days, migration 005). 0 turns a limit off.
"""

from .errors import ApiError


def check(conn, tenant: str, day: str, settings) -> None:
    row = conn.execute(
        "SELECT coalesce(sum(questions) FILTER (WHERE day = %(day)s::date), 0) AS today,"
        " coalesce(sum(cost_usd) FILTER (WHERE date_trunc('month', day) = date_trunc('month', %(day)s::date)), 0)"
        " AS month FROM usage_days WHERE tenant_id = %(t)s", {"t": tenant, "day": day}).fetchone()
    if settings.daily_question_limit and row["today"] >= settings.daily_question_limit:
        raise ApiError(429, "limit_reached",
                       f"This shop has asked {row['today']} questions today, the daily limit. Try again tomorrow.",
                       headers={"Retry-After": "3600"})
    if settings.monthly_budget_usd and float(row["month"]) >= settings.monthly_budget_usd:
        raise ApiError(429, "limit_reached",
                       f"This shop has used its model budget for this month (US${settings.monthly_budget_usd:.2f}).",
                       headers={"Retry-After": "86400"})


def record(conn, tenant: str, day: str, cost_usd: float) -> None:
    conn.execute(
        "INSERT INTO usage_days (tenant_id, day, questions, cost_usd) VALUES (%s, %s, 1, %s)"
        " ON CONFLICT (tenant_id, day) DO UPDATE SET questions = usage_days.questions + 1,"
        " cost_usd = usage_days.cost_usd + excluded.cost_usd", (tenant, day, cost_usd))


def usage(conn, tenant: str, day: str, settings) -> dict:
    row = conn.execute(
        "SELECT coalesce(sum(questions) FILTER (WHERE day = %(day)s::date), 0) AS today,"
        " coalesce(sum(cost_usd) FILTER (WHERE date_trunc('month', day) = date_trunc('month', %(day)s::date)), 0)"
        " AS month FROM usage_days WHERE tenant_id = %(t)s", {"t": tenant, "day": day}).fetchone()
    return {"questions_today": row["today"], "daily_question_limit": settings.daily_question_limit,
            "cost_this_month_usd": round(float(row["month"]), 6), "monthly_budget_usd": settings.monthly_budget_usd}
