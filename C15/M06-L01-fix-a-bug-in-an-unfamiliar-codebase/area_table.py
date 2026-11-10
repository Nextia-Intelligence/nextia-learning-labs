"""The area table: one measure for every fix of issue 12 in delivery-slots.

Put this file next to the project folder, then run it from inside the project:

    python -m pytest -q --rootdir=. ../area_table.py

Twelve postal codes, each with the zone that data/zones.csv gives it, or "refused" where
Larkfield does not deliver. The expected zones come from the data file, the README's rule and
the two issues, not from any fix. The README's rule says that the row of a whole FSA wins
"wherever the rows are in data/zones.csv", so each postal code is checked twice: with the rows
in the order of the file, and in the reverse order. Written for the course by Nextia Learning
(MIT).
"""

from pathlib import Path

import pytest

from delivery_slots.zones import UnknownPostcode, load_zones, zone_for

TABLE = [
    ("H3Z 2Y7", "west", "the customer of issue 12: the row H3Z must win over H3"),
    ("h3z2y7", "west", "issue 12 typed as in issue 3: small letters, no space"),
    ("H3Y 1K5", "west", "another west FSA that starts with H3"),
    ("H3T 1J4", "west", "another west FSA that starts with H3"),
    ("H3N 2L8", "north", "a north FSA that starts with H3"),
    ("H3A 0G4", "city", "an FSA without its own row: the row H3"),
    ("H2Y 1C6", "city", "a city FSA with its own row: it must win over H2"),
    ("H2W 1Y6", "north", "an FSA without its own row: the row H2"),
    ("H4A1B2", "west", "issue 3: no space"),
    (" h2t  1s4 ", "north", "spaces and small letters"),
    ("H1A 0A1", "refused", "a part of Montréal that Larkfield does not serve"),
    ("K1A 0B1", "refused", "another city"),
]


def lookup(postcode, zones):
    try:
        return zone_for(postcode, zones)
    except UnknownPostcode:
        return "refused"


@pytest.fixture(scope="module")
def zones():
    return load_zones(Path("data") / "zones.csv")


@pytest.mark.parametrize("postcode, expected, why", TABLE, ids=[row[0].strip() for row in TABLE])
def test_area_table(zones, postcode, expected, why):
    backwards = dict(reversed(zones.items()))
    got = {"file order": lookup(postcode, zones), "reverse order": lookup(postcode, backwards)}
    assert got == {"file order": expected, "reverse order": expected}, why
