from test_cli import run


def test_count_without_nms_counts_doubles(data, workdir, capsys):
    code, out = run(["--data", str(data), "count", "--score", "0.5"], capsys)
    assert code == 0 and "count error 3.0 boxes" in out


def test_count_with_nms_is_exact(data, workdir, capsys):
    code, out = run(["--data", str(data), "count", "--score", "0.5", "--nms", "0.5"], capsys)
    assert "count error 0.0 boxes" in out and "exact on 100% of photos" in out


def test_a_high_score_line_keeps_only_the_best_boxes(data, workdir, capsys):
    code, out = run(["--data", str(data), "count", "--score", "0.8"], capsys)
    assert "count error 0.0 boxes" in out
