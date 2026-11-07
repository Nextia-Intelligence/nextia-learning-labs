import shutil

import pytest

from larkvision.cli import main


def run(args, capsys):
    with pytest.raises(SystemExit) as e:
        main(args)
    return e.value.code, capsys.readouterr().out


def test_info(data, workdir, capsys):
    code, out = run(["--data", str(data), "info"], capsys)
    assert code == 0 and "Catalogue: 48 train, 16 validation, 24 test photos in 8 categories" in out
    assert "hidden test sets are not here" in out


def test_compare(data, workdir, capsys):
    code, out = run(["--data", str(data), "compare", "--task", "catalogue"], capsys)
    assert code == 0 and "colour histogram + 5-NN" in out


def test_reset_removes_outputs_and_finds_a_broken_file(data, workdir, capsys, tmp_path):
    (workdir / "outputs").mkdir(exist_ok=True)
    (workdir / "review").mkdir()
    code, out = run(["--data", str(data), "reset"], capsys)
    assert code == 0 and "removed outputs, review" in out and "files are right" in out
    broken = tmp_path / "broken"
    shutil.copytree(data, broken)
    (broken / "costs.json").write_text("{}")
    code, out = run(["--data", str(broken), "reset"], capsys)
    assert code == 1 and "changed: costs.json" in out
