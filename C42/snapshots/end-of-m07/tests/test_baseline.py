from test_cli import run


def test_histogram_baseline_learns_colours(data, workdir, capsys):
    code, out = run(["--data", str(data), "baseline", "--method", "histogram", "--k", "1"], capsys)
    assert code == 0 and "colour histogram + 1-NN, catalogue test: accuracy 0.9" in out
    assert (workdir / "outputs/table.json").exists()


def test_hog_baseline_runs_and_adds_rows(data, workdir, capsys):
    run(["--data", str(data), "baseline", "--method", "hog"], capsys)
    code, out = run(["--data", str(data), "compare", "--task", "catalogue", "--mine"], capsys)
    assert "HOG + logistic regression (yours)" in out
