from test_cli import run


def test_zones_separate_perfect_scores(data, workdir, capsys):
    code, out = run(["--data", str(data), "zones"], capsys)
    assert code == 0 and "AUROC 1.000" in out and "0.0 damaged sold as new" in out


def test_a_zero_budget_means_no_checks(data, workdir, capsys):
    code, out = run(["--data", str(data), "zones", "--budget", "0"], capsys)
    assert " 0 checks" in out


def test_list_methods(data, workdir, capsys):
    code, out = run(["--data", str(data), "zones", "--list"], capsys)
    assert out.strip() == "small_patchcore"
