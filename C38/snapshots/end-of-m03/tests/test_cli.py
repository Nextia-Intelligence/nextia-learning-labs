from larkfield_search.cli import main


def test_info_and_query(capsys):
    main(["info"])
    out = capsys.readouterr().out
    assert "Catalogue: 12 products" in out
    main(["query", "garden hose", "--run", "bm25", "-k", "3"])
    out = capsys.readouterr().out
    assert "LK-10003" in out and "[exact]" in out


def test_eval_and_list(capsys):
    main(["eval", "--run", "current", "--split", "test"])
    out = capsys.readouterr().out
    assert "current on 4 test queries" in out
    main(["eval", "--list"])
    assert "bm25" in capsys.readouterr().out


def test_log_and_reset(capsys):
    main(["log", "--top", "3"])
    out = capsys.readouterr().out
    assert "5 searches (synthetic)" in out
    main(["reset"])
    assert "all files are right" in capsys.readouterr().out
