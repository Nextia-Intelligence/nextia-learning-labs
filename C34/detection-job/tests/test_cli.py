from detect.__main__ import main


def test_train_run_rerun_from_the_command_line(data_dir, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DETECT_DATA", str(data_dir))
    monkeypatch.setenv("DETECT_STATE", str(tmp_path / "state"))
    monkeypatch.setenv("DETECT_ALERTS", str(tmp_path / "alerts"))
    monkeypatch.setenv("DETECT_BUDGET", "5")
    main(["train", "--until", "2025-10-05", "--days", "60"])
    main(["run", "--day", "2025-10-06"])
    first = capsys.readouterr().out
    assert "Sent 5 new alerts" in first
    main(["run", "--day", "2025-10-06"])
    second = capsys.readouterr().out
    assert "Sent 0 new alerts" in second and "5 already sent" in second
    main(["report", "--week-ending", "2025-10-06"])
    assert "Alert report" in capsys.readouterr().out
