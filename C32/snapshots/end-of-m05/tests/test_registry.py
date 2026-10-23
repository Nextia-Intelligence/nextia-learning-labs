"""Registration: the form, its checks, and the agent lifecycle."""

from datetime import date

import pytest

from conftest import PROJECT
from estate import registry


def form(name):
    return registry.read_form(PROJECT / "registrations" / f"{name}.yaml")


def test_every_form_of_the_estate_is_complete():
    for p in sorted((PROJECT / "registrations").glob("*.yaml")):
        assert registry.check_form(registry.read_form(p), today=date(2026, 10, 22)) == [], p.name


def test_a_short_form_registers_at_once():
    reg = registry.register(form("ticket-triage"), "usr-kwame")
    assert (reg.status, reg.version) == ("active", 1)
    assert registry.events("ticket-triage")[0]["action"] == "register"


def test_high_risk_needs_the_long_form_and_a_review():
    f = form("support-workflow")
    short = {k: v for k, v in f.items() if k != "long_form"}
    with pytest.raises(registry.FormError) as e:
        registry.register(short, "usr-kwame")
    assert "high risk needs the long form" in str(e.value)
    assert registry.register(f, "usr-kwame").status == "pending"
    assert registry.review("support-workflow", "usr-kwame", "2027-01-10").status == "active"


def test_the_form_refuses_what_the_platform_cannot_allow():
    f = dict(form("support-workflow"), autonomy="acts")
    assert "a high-risk agent may not act without a person's approval (autonomy: acts-with-approval)" in \
        registry.check_form(f)
    f = dict(form("ticket-triage"), owner="usr-lee")
    assert any("left the company" in p for p in registry.check_form(f))
    f = dict(form("ticket-triage"), data_classes=["payment"])
    assert any("never sent to a model" in p for p in registry.check_form(f))
    f = dict(form("support-mcp"), data_classes=["personal", "payment"])     # a tool server: no capabilities
    assert any("a tool server cannot register it" in p for p in registry.check_form(f))
    f = dict(form("ticket-triage"), capabilities=["fast-small", "teleport"])
    assert "capability teleport: not in the catalog" in registry.check_form(f)
    f = dict(form("ticket-triage"), review_date="2028-01-01")
    assert any("reviewed at least every 6 months" in p for p in registry.check_form(f, today=date(2026, 10, 22)))


def test_a_change_to_a_high_risk_agents_permissions_needs_a_new_review():
    registry.register(form("support-workflow"), "usr-kwame")
    registry.review("support-workflow", "usr-kwame", "2027-01-10")
    changed = dict(form("support-workflow"), review_date="2027-01-10")
    changed["tools"] = changed["tools"] + ["support.propose_refund"]
    reg = registry.register(changed, "usr-amira")
    assert (reg.status, reg.version) == ("pending", 2)
    assert registry.events("support-workflow")[0]["detail"]["changed"] == ["tools"]


def test_retire_revokes_the_credentials_and_the_id_is_never_used_again():
    from estate import identity

    registry.register(form("doc-assistant"), "usr-kwame")
    identity.issue_credentials("doc-assistant", "usr-kwame")
    registry.set_status("doc-assistant", "retired", "usr-kwame", "replaced by a new assistant")
    assert registry.get("doc-assistant").credentials[0]["revoked_at"]
    with pytest.raises(registry.FormError):
        registry.register(form("doc-assistant"), "usr-kwame")
    with pytest.raises(ValueError):
        registry.set_status("doc-assistant", "active", "usr-kwame", "undo")
    # The remap gate reads the forms in registrations/, but a retired agent is no consumer any more.
    from estate import remap

    assert "doc-assistant" not in [f["id"] for f in remap.consumers("fast-small")]
    assert "ticket-triage" in [f["id"] for f in remap.consumers("fast-small")]


def test_a_status_change_needs_a_reason():
    registry.register(form("doc-assistant"), "usr-kwame")
    with pytest.raises(ValueError):
        registry.set_status("doc-assistant", "suspended", "usr-kwame", " ")


def test_review_due_finds_overdue_reviews_owners_who_left_and_pins():
    registry.register(form("release-judge"), "usr-kwame")          # review date 2026-10-01: overdue
    f = dict(form("ticket-triage"), pins={"fast-small": {"deployment": "chat-small",
                                                         "model_version": "gpt-6-luna-2026-09-22",
                                                         "retire_by": "2026-12-01"}})
    registry.register(f, "usr-kwame")
    due = {(r.agent_id, why.split(" ")[0]) for r, why in registry.review_due(date(2026, 10, 22))}
    assert ("release-judge", "review") in due and ("ticket-triage", "pin") in due
