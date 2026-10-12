from adapt.answer import format_answer, parse_answer
from adapt.cases import load_cases
from adapt.failures import failures
from adapt.predictions import Prediction, load_predictions


def test_only_one_exact_answer_is_valid():
    assert parse_answer('{"team": "payment", "needs_human": false}') == ({"team": "payment", "needs_human": False}, "")
    assert parse_answer(format_answer("returns", True))[0] == {"team": "returns", "needs_human": True}
    assert parse_answer('{"team": "payment", "needs_human": false} Thanks!')[1] == "JSON with extra text"
    assert parse_answer('{"team": "billing", "needs_human": false}')[1] == "unknown team"
    assert parse_answer('{"team": "payment"}')[1] == "wrong keys"
    assert parse_answer('{"team": "payment", "needs_human": "no"}')[1] == "needs_human is not true or false"
    assert parse_answer("The team is payment.")[1] == "not JSON"


def test_each_mistake_gets_its_kind():
    case = next(c for c in load_cases() if c.needs_human and c.team == "warranty")

    def pred(raw):
        a, p = parse_answer(raw)
        return {case.case_id: Prediction(case.case_id, raw, 0.1, a, p)}

    assert failures([case], pred("Sure!"))["format"] == [case]
    assert failures([case], pred('{"team": "repairs", "needs_human": true}'))["labels"] == [case]
    found = failures([case], pred('{"team": "delivery", "needs_human": false}'))
    assert found["routing"] == [case] and found["missed"] == [case]


def test_the_hosted_assistant_makes_12_mistakes_on_dev():
    found = failures(load_cases(), load_predictions("chat-small"))
    assert {k: len(v) for k, v in found.items()} == {"format": 1, "labels": 0, "routing": 2, "missed": 0,
                                                     "false_alarm": 9}
