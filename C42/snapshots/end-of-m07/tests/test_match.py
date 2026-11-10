from test_cli import run


def test_match_finds_the_photo(data, workdir, capsys):
    code, out = run(["--data", str(data), "match", "--embeddings", "dinov2", "--show", "1"], capsys)
    assert code == 0 and "recall at 1 1.000" in out and "*P-" in out


def test_vlm_check_replays_and_finds_the_wrong_colour(data, workdir, capsys):
    code, out = run(["--data", str(data), "vlm", "--model", "hosted"], capsys)
    assert "product_type 4/4" in out and "main_colour  3/4" in out
    assert "found 2 of 2" in out and "error 1.0 boxes" in out
