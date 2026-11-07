"""The settings of the forecasting job. Every cost here is an assumption of the course, not a measured value."""

HORIZON_DAYS = 14            # the stock order covers the next 14 days
TICKET_HORIZON_HOURS = 168   # the roster covers the next week
SEASON_DAYS = 7
LEVELS = [80, 90]            # the forecast ranges that the job keeps

# Stock (assumptions): a lost sale costs the margin (35% of the price); a left-over item is sold at a 60%
# discount at the end of the season, so it costs 25% of the price.
LOST_SALE_SHARE = 0.35
LEFT_OVER_SHARE = 0.25

# Help desk (assumptions): one agent answers 6 tickets an hour; agents work from 07:00 to 21:59; an extra
# agent hour costs 28 dollars; an hour that is one agent short costs 72 dollars (6 tickets that wait about a
# day longer, at 12 dollars each).
TICKETS_PER_AGENT_HOUR = 6
OPEN_HOURS = range(7, 22)
AGENT_HOUR_USD = 28.0
SHORT_HOUR_USD = 72.0
TICKET_HISTORY_HOURS = 2016  # the job fits the ticket model on the last 12 weeks

# Data checks
MAX_STOCK_OUT_SHARE = 0.05   # warn when more than 5% of the last week's rows are stock-outs


def critical_ratio(short_cost, over_cost):
    """The newsvendor quantile: the share of the time you want enough."""
    return short_cost / (short_cost + over_cost)


STOCK_QUANTILE = critical_ratio(LOST_SALE_SHARE, LEFT_OVER_SHARE)    # 0.583
ROSTER_QUANTILE = critical_ratio(SHORT_HOUR_USD, AGENT_HOUR_USD)     # 0.72
