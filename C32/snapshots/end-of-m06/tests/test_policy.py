"""Policy as code: the approval policy and its own tests."""

import copy

from estate import policy


def test_the_policys_own_test_cases_pass():
    results = policy.run_tests()
    assert results and all(ok for _, ok, _ in results), [r for r in results if not r[1]]


def test_the_policy_is_valid_and_denies_by_default():
    pol = policy.load()
    assert policy.check_policy(pol) == []
    assert policy.decide(pol, "orders.cancel_order", {}).denied


def test_a_broken_rule_is_found():
    pol = copy.deepcopy(policy.load())
    pol["rules"][0]["approve_by"] = "intern"
    assert policy.check_policy(pol) == ["rule refund-up-to-100: approve_by must be one of support_agent, team_lead, "
                                        "support_lead or none"]


def test_a_changed_limit_is_caught_by_the_tests():
    pol = copy.deepcopy(policy.load())
    pol["rules"][0]["match"]["amount_at_most"] = 200                   # someone raises the agents' limit
    failed = [name for name, ok, _ in policy.run_tests(pol) if not ok]
    assert failed == ["100.01 dollars needs a team lead"]


def test_rules_can_match_a_data_class():
    pol = copy.deepcopy(policy.load())
    pol["rules"].insert(0, {"id": "payment-data", "match": {"tool": "orders.request_refund", "data_class": "payment"},
                            "approve_by": "support_lead"})
    d = policy.decide(pol, "orders.request_refund", {"amount": 5}, data_class="payment")
    assert (d.rule, d.needs) == ("payment-data", "support_lead")
    assert policy.decide(pol, "orders.request_refund", {"amount": 5}).rule == "refund-up-to-100"
