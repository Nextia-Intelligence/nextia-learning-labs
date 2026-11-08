from larkspeech import audio
from larkspeech import data as D


def test_calls_and_audio(data):
    assert [c["call_id"] for c in D.load_calls(data, "test")] == ["T-0003"]
    assert len(D.load_calls(data, with_audio=True)) == 2
    x, sr = D.load_audio(data, "T-0003")
    assert sr == 16000 and abs(len(x) / sr - 10) < 0.01
    agent, _ = D.load_audio(data, "T-0003", channel=0)
    assert audio.dbfs(agent) < audio.dbfs(x) + 3
    assert D.reference(D.call(data, "T-0003"), "caller").startswith("Hi.")


def test_phone_line_and_mulaw():
    import numpy as np
    x = np.sin(2 * np.pi * 1000 * np.arange(16000) / 16000).astype("float32") * 0.5
    y, sr = audio.to_phone(x, 16000)
    assert sr == 8000 and len(y) == 8000
    codes = audio.mulaw_encode(y)
    assert codes.dtype.name == "uint8" and np.max(np.abs(audio.mulaw_decode(codes) - np.clip(y, -1, 1))) < 0.02


def test_check_files(data):
    n, problems = D.check_files(data)
    assert n > 10 and problems == []
