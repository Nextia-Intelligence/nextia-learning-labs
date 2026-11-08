from larkroute import rules


def test_rules_route_clear_messages():
    book = rules.load()
    assert rules.match("I was charged twice for my order", book)["route"] == "billing"
    assert rules.match("Mon compte a été piraté", book)["route"] == "account"
    assert rules.match("I will call my lawyer", book)["route"] == "needs_person"
    assert rules.match("hello there", book) is None


def test_a_refund_word_is_not_always_a_refund_request():
    # A question before buying, about the return policy: the rule sends it to returns, the label is product.
    book = rules.load()
    question = "If I buy the parasol and don't like the colour, can I return it?"
    assert rules.match(question, book)["route"] == "returns_refunds"


def test_only_strong_rules_when_asked():
    book = rules.load()
    assert rules.match("where is my tracking number", book, strong_only=True) is None
