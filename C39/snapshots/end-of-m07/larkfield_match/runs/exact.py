"""The first baseline: two records are the same customer when their emails are exactly the same text."""

from .. import data
from ..pairs import same_value_pairs


def exact():
    """Same email, exactly as typed (no cleaning: spaces and capitals count)."""
    p = same_value_pairs(data.records(), "email")
    return p.assign(score=1.0, match=1)


RUNS = {
    "exact": ("customers", exact, "same email, exactly as typed"),
}
