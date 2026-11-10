import json

from larkroute import data
from larkroute.llm import ExamplePicker, ReplayClient, parse, system_prompt, user_prompt


def test_every_answer_is_checked():
    assert parse('{"route": "billing", "confidence": 0.9, "reason": "double charge"}')["valid"]
    assert parse("Billing, I think")["route"] == "review"
    assert parse('{"route": "refunds", "confidence": 0.9, "reason": ""}')["route"] == "review"
    assert parse('{"route": "billing", "confidence": 90, "reason": ""}')["route"] == "review"


def test_the_prompts_name_every_route():
    for mode in ("zero-shot", "few-shot"):
        assert all(r in system_prompt(mode) for r in data.ROUTES)
    assert "Labelled examples" in user_prompt("hi", [("where is it", "delivery")])


def test_examples_are_chosen_by_similarity(small_train):
    ex = ExamplePicker(small_train, k=3).pick(small_train["text"].iloc[0])
    assert len(ex) == 3 and small_train["text"].iloc[0] in [t for t, _ in ex]


def test_replay_gives_the_recorded_answer_with_its_cost():
    test = data.messages("test")
    a = ReplayClient("few-shot").classify(test["message_id"].iloc[0])
    assert a["replayed"] and a["route"] in data.ROUTES + ["review"]
    assert a["tokens_in"] > 0 and a["usd"] > 0
    json.dumps(a)
