import json

from adapt.costs import hosted_per_ticket, report
from adapt.regressions import is_right, load_prompts, looks_like_ticket_json, summary


def test_a_right_answer_contains_an_expected_word():
    assert is_right("The capital of France is Paris.", ["paris"])
    assert not is_right("garden", ["GARDEN"]) and is_right("GARDEN", ["GARDEN"])
    assert looks_like_ticket_json('{"team": "delivery", "needs_human": false}')
    assert not looks_like_ticket_json("Paris")


def test_the_saved_general_answers_are_scored_for_both_models():
    prompts = load_prompts()
    assert len(prompts) == 20
    for name in ("base", "lora-r8", "lora-r8-long"):
        rows = [json.loads(x) for x in open(f"runs/general/{name}.jsonl", encoding="utf-8")]
        assert summary(rows, prompts)["questions"] == 20


def test_the_hosted_cost_comes_from_the_recorded_run():
    per_ticket, tokens_in, _ = hosted_per_ticket()
    assert 0.0003 < per_ticket < 0.0004 and tokens_in > 1800


def test_every_cost_line_says_what_kind_of_number_it_is():
    lines = [x for x in report(822) if "US$" in x or " s per " in x]
    assert lines and all(any(w in x for w in ("measured", "price", "= US$")) for x in lines)
