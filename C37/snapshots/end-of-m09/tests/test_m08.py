from larkfield_recs import cli


def test_online_reads_the_simulated_test(capsys):
    cli.main(["online"])
    out = capsys.readouterr().out
    assert "SIMULATED" in out and "two-stage" in out and "95% interval" in out


def test_loop(capsys):
    cli.main(["loop"])
    assert "exploration" in capsys.readouterr().out
