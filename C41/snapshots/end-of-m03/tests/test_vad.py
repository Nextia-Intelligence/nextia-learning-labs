import numpy as np

from larkspeech import vad as V


def bursts(sr=8000):
    x = np.zeros(sr * 6, np.float32)
    t = np.arange(sr) / sr
    x[sr:2 * sr] = 0.3 * np.sin(2 * np.pi * 300 * t)
    x[4 * sr:5 * sr] = 0.3 * np.sin(2 * np.pi * 300 * t)
    return x


def test_energy_finds_loud_parts():
    regions = V.energy(bursts(), 8000)
    assert len(regions) == 2 and abs(regions[0][0] - 1.0) < 0.05 and abs(regions[1][1] - 5.0) < 0.4


def test_frame_scores():
    s = V.frame_scores([(1, 2)], [(1, 2), (4, 5)], 6)
    assert abs(s["missed"] - 0.5) < 0.02 and s["false"] == 0


def test_keep_speech_cuts_silence():
    x = bursts()
    y = V.keep_speech(x, 8000, V.energy(x, 8000))
    assert len(y) < len(x) / 2
