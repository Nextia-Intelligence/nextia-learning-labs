import json

import pytest

from adapt.__main__ import main
from adapt.cases import SPLITS, load_cases
from adapt.model import load_tokenizer
from adapt.predict import CHOICES, choose, policy_messages
from adapt.predictions import load_predictions, systems
from tests.tiny import tiny_model


def test_every_saved_system_answered_all_271_cases():
    ids = {c.case_id for c in load_cases(SPLITS)}
    for name in systems():
        assert set(load_predictions(name)) == ids, name


def test_the_comparison_reads_the_same_cases_for_every_system(capsys):
    main(["compare", "--split", "dev"])
    out = capsys.readouterr().out
    assert out.startswith("102 cases (dev)")
    assert all(name in out for name in systems())


def test_a_chosen_answer_is_always_one_of_the_10_valid_answers():
    import torch

    torch.set_num_threads(1)
    answer, scores = choose(tiny_model(), load_tokenizer(), policy_messages("My parcel is late."))
    assert answer in CHOICES and len(scores) == 10 == len(set(CHOICES))


@pytest.mark.model
def test_the_saved_adapter_replies_are_reproduced():
    from adapt.model import load_adapted
    from adapt.predict import generate, short_messages

    model = load_adapted("runs/lora-r8/adapter")
    saved = load_predictions("adapter")
    cases = load_cases()[:5]
    for case in cases:
        from adapt.cases import model_input

        assert generate(model, load_tokenizer(), short_messages(model_input(case))) == saved[case.case_id].raw
    assert json.loads(saved[cases[0].case_id].raw)
