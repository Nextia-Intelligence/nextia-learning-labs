import pytest

from adapt.config import load_config, plan
from adapt.model import load_tokenizer
from adapt.records import messages
from adapt.train import encode


def test_the_course_run_is_planned_before_it_starts():
    cfg = load_config("configs/lora-r8.toml")
    p = plan(cfg)
    assert (p["train_records"], p["steps_per_epoch"], p["steps"]) == (900, 113, 226)
    assert cfg.targets == ("q_proj", "v_proj") and cfg.threads == 2


def test_a_wrong_setting_is_refused(tmp_path):
    text = open("configs/lora-r8.toml", encoding="utf-8").read().replace("learning_rate = 2e-4", "learning_rate = 5")
    (tmp_path / "bad.toml").write_text(text)
    with pytest.raises(ValueError, match="learning_rate"):
        load_config(tmp_path / "bad.toml")


def test_only_the_answer_is_learned_and_a_long_ticket_loses_its_end_not_its_answer():
    tok = load_tokenizer()
    record = {"messages": messages("word " * 600, "warranty", True)}
    ids, labels = encode(tok, record, max_tokens=128)
    learned = [i for i, label in zip(ids, labels) if label != -100]
    assert len(ids) == 128
    assert tok.decode(learned) == '{"team": "warranty", "needs_human": true}<|im_end|>'
