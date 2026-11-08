import pytest

from larkspeech import scoring
from larkspeech.cli import main


def test_score_by_slice(data):
    res = scoring.score(data, "whisper-tiny", "validation,test", by="channels")
    assert set(res) == {"mono", "stereo"}
    assert res["mono"]["wer"] == 0 and res["stereo"]["important"]["order"]["missed"] == 0


def test_wer_command_shows_the_alignment(capsys):
    with pytest.raises(SystemExit):
        main(["wer", "the cat sat on the mat", "the cat sit on mat today"])
    out = capsys.readouterr().out
    assert "6 reference words: WER 50.0%" in out and "HYP: the cat sit" in out


def test_unknown_method(data):
    with pytest.raises(FileNotFoundError, match="recorded: whisper-tiny"):
        scoring.load_transcripts(data, "whisper-huge")
