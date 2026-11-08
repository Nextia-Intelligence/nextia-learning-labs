import shutil

import pytest

from larkspeech.cli import main


def run(args, capsys):
    with pytest.raises(SystemExit) as e:
        main(args)
    return e.value.code, capsys.readouterr().out


def test_info(data, workdir, capsys):
    code, out = run(["--data", str(data), "info"], capsys)
    assert code == 0 and "1 train (transcripts only), 1 validation, 1 test" in out and "synthetic" in out


def test_inspect(data, workdir, capsys):
    code, out = run(["--data", str(data), "inspect", "T-0003"], capsys)
    assert code == 0 and "8000" in out and "ULAW" in out


def test_reset_finds_a_broken_file(data, workdir, capsys, tmp_path):
    (workdir / "outputs").mkdir(exist_ok=True)
    code, out = run(["--data", str(data), "reset"], capsys)
    assert code == 0 and "removed outputs" in out and "files are right" in out
    broken = tmp_path / "broken"
    shutil.copytree(data, broken)
    (broken / "orders.json").write_text("[]")
    code, out = run(["--data", str(broken), "reset"], capsys)
    assert code == 1 and "changed: orders.json" in out
