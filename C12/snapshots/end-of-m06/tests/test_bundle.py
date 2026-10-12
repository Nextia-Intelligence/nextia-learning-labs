import json

import pytest

from adapt.bundle import compatible, make_bundle
from adapt.model import REVISION


def test_a_bundle_names_its_base_model_and_holds_what_it_needs(tmp_path):
    out = make_bundle(__import__("pathlib").Path("runs/lora-r8-long"), tmp_path / "bundle")
    info = json.loads((out / "bundle.json").read_text())
    assert info["base_model"]["revision"] == REVISION and len(info["tokenizer_sha256"]) == 64
    assert (out / "adapter/adapter_model.safetensors").exists() and (out / "checks.jsonl").exists()
    assert "holdout:" in (out / "MODEL_CARD.md").read_text() and compatible(info) == []


def test_a_bundle_for_another_revision_or_tokenizer_is_refused(tmp_path):
    info = json.loads(json.dumps({"base_model": {"id": "HuggingFaceTB/SmolLM2-135M-Instruct", "revision": "0" * 40,
                                                 "config_sha256": "x"}, "tokenizer_sha256": "y"}))
    problems = compatible(info)
    assert len(problems) == 3


@pytest.mark.model
def test_the_course_adapter_fails_exactly_its_two_safety_checks(tmp_path):
    from pathlib import Path

    from adapt.bundle import verify

    out = make_bundle(Path("runs/lora-r8-long"), tmp_path / "bundle")
    lines = []
    assert not verify(out, say=lines.append)
    assert [x.split()[1] for x in lines if x.strip().startswith("FAIL")] == ["C-07", "C-08"]
