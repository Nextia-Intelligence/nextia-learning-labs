from larkroute import costs


def test_each_kind_of_mistake_has_its_cost():
    c = costs.load()
    assert costs.message_cost("delivery", "delivery", "normal", "late_delivery", c) == 0
    assert costs.message_cost("delivery", "review", "normal", "late_delivery", c) == c["review"]
    assert costs.message_cost("delivery", "billing", "normal", "late_delivery", c) == c["wrong_queue"]
    assert costs.message_cost("delivery", "billing", "urgent", "late_delivery", c) == c["wrong_queue_urgent"]
    assert costs.message_cost("account", "billing", "urgent", "account_takeover", c) == c["missed_account_takeover"]
    assert costs.message_cost("needs_person", "product", "urgent", "safety_issue", c) == c["needs_person_sent_to_team"]
    to_person = c["team_message_sent_to_person"]
    assert costs.message_cost("billing", "needs_person", "normal", "invoice_request", c) == to_person


def test_a_review_costs_less_than_a_wrong_queue():
    c = costs.load()
    assert c["review"] < c["wrong_queue"] < c["wrong_queue_urgent"] < c["missed_account_takeover"]
