"""Module 2: normalising, parsing and rules."""

from larkfield_match import normalise as nz
from larkfield_match import pairs
from larkfield_match.parse import parse_title, split_address, split_name


def test_normalise_values():
    assert nz.phone("+1 (514) 555-0101 ext. 2") == "5145550101"
    assert nz.email(" MC.Tremblay@Example.com ") == "mc.tremblay@example.com"
    assert nz.postcode("j0l-1a0") == "J0L1A0" and nz.postcode("12345") == ""
    assert nz.name("Dr. Hélène O'Brien") == "helene obrien"
    assert nz.town("Sainte-Anne-des-Prés") == nz.town("STE ANNE DES PRES") == "ste anne des pres"
    assert nz.date("14/03/1980") == "1980-03-14"
    assert nz.company("Larkfield Ltée") == "larkfield"


def test_split_names():
    assert split_name("TREMBLAY, MARIE-CLAUDE") == {"first": "marie claude", "last": "tremblay", "ok": True}
    assert split_name("Mme Marie Claude Tremblay")["first"] == "marie claude"


def test_split_address():
    a = split_address("3-12, R. DES ERABLES, STE-ANNE-DES-PRES QC J0L1A0")
    assert (a["number"], a["unit"], a["street"], a["town"], a["postcode"]) == \
        ("12", "3", "rue des erables", "ste anne des pres", "J0L1A0")
    assert not split_address("somewhere")["ok"]


def test_parse_title_units_and_packs():
    a = parse_title("AquaRidge Rubber Garden Hose, 50 ft, Green (Pack of 2)")
    b = parse_title("gdn hose 15.2 m rubber green - AQUARIDGE")
    assert a["pack"] == 2 and b["pack"] == 1
    assert abs(a["size"] - b["size"]) < 0.1 and a["size_kind"] == "length_m"
    assert "garden" in b["words"].split()


def test_normalised_email_finds_more():
    raw = pairs.get("exact", quiet=True)
    norm = pairs.get("exact-norm", quiet=True)
    assert ("L-000001", "S-000001") in set(zip(norm.record_id_l, norm.record_id_r))
    assert len(norm) > len(raw)
