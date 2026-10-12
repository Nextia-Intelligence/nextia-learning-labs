import json

import pytest

from adapt.config import load_config
from adapt.model import load_tokenizer
from adapt.train import train
from tests.tiny import tiny_model, tiny_project


def run(project, **kw):
    return train(load_config(project / "tiny.toml"), root=project, base_model=tiny_model(),
                 tokenizer=load_tokenizer(), say=lambda *a: None, **kw)


def losses(project):
    rows = [json.loads(x) for x in (project / "runs/tiny/log.jsonl").read_text().splitlines()]
    return [r.get("train_loss", r.get("val_loss")) for r in rows]


def test_a_run_writes_its_log_checkpoints_best_and_final_adapter(tmp_path):
    project = tiny_project(tmp_path)
    summary = run(project)
    run_dir = project / "runs/tiny"
    assert summary["steps"] == 10 and summary["trainable_parameters"] == 2 * 2 * (16 + 16 + 16 + 8)
    assert (run_dir / "adapter/adapter_model.safetensors").exists() and (run_dir / "best").exists()
    assert len(list((run_dir / "checkpoints").glob("step-*"))) == 2  # only the newest two are kept


def test_a_stopped_run_resumes_to_exactly_the_same_result(tmp_path):
    whole = tiny_project(tmp_path / "a")
    run(whole)
    stopped = tiny_project(tmp_path / "b")
    assert run(stopped, stop_after=5) == {"stopped_at": 5}
    run(stopped, resume=True)
    assert losses(stopped) == losses(whole)


def test_the_recorded_run_trained_0_34_percent_of_the_model():
    s = json.loads(open("runs/lora-r8/summary.json").read())
    assert (s["trainable_parameters"], s["all_parameters"]) == (460_800, 134_975_808)
    assert s["steps"] == 226 and s["best_val_loss"] <= s["first_val_loss"]


@pytest.mark.model
def test_the_recorded_adapter_loads_on_the_pinned_base_and_answers_in_json():
    import torch

    from adapt.answer import parse_answer
    from adapt.model import load_adapted
    from adapt.records import messages

    torch.set_num_threads(2)
    tok = load_tokenizer()
    model = load_adapted("runs/lora-r8/adapter")
    ids = torch.tensor([tok(tok.apply_chat_template(messages("My parcel is ten days late."), tokenize=False,
                                                    add_generation_prompt=True), add_special_tokens=False).input_ids])
    out = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=24, do_sample=False)
    assert parse_answer(tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True))[0] is not None
