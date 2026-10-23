"""The gateway's guardrails: simple rules on text, with their checks against false blocks."""

from gateway import guardrails as g


def test_the_luhn_check():
    assert g.luhn("4539148803436467") and not g.luhn("4539148803436468")


def test_card_numbers_with_spaces_or_hyphens_are_found():
    assert g.card_numbers("pay with 4539 1488 0343 6467 please") == ["4539 1488 0343 6467"]
    assert g.card_numbers("pay with 4539-1488-0343-6467") == ["4539-1488-0343-6467"]


def test_order_ids_phone_numbers_and_long_numbers_that_fail_the_check_are_not_cards():
    text = "Order LK-104233, call +1 416 555 0123, tracking 1Z999AA10123456784, ref 1234567890123456"
    assert g.card_numbers(text) == []
    assert g.NAIVE_CARD.findall("ref 1234567890123456") == ["1234567890123456"]   # the rule without the checksum


def test_secrets_are_found():
    assert g.secrets_in("use sim-az-service-team-0001 for now") == ["practice_key"]
    assert g.secrets_in("password: hunter22") == ["password"]
    assert g.secrets_in("my password reset email never came") == []


def test_redaction_changes_only_the_number():
    body = {"model": "fast-small", "messages": [{"role": "user", "content": "card 4539 1488 0343 6467, order LK-104233"}]}
    decision, out, notes = g.apply(body, [{"id": "card-numbers", "kind": "card_number", "action": "redact"}])
    assert decision == "redacted" and out["messages"][0]["content"] == "card [card number removed], order LK-104233"
    assert body["messages"][0]["content"].startswith("card 4539")          # the original is not changed


def test_the_rules_find_nothing_in_the_estates_recorded_traffic():
    """The recorded requests of every app: no card number, no secret. (measure/guardrails.py counts them all.)"""
    from conftest import stream

    rules = [{"id": "card-numbers", "kind": "card_number", "action": "block"},
             {"id": "secrets", "kind": "secret", "action": "block"}]
    for name in ("ticket-triage", "support-workflow__chat-strong", "doc-assistant__chat"):
        for row in stream(name)[:60]:
            assert g.apply(row["body"], rules)[0] == "pass", (name, row["seq"])
