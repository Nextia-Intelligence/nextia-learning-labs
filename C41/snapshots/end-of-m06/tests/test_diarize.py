from larkspeech import diarize as Z


def test_der_perfect_and_swapped_names():
    truth = [(0, 2, "agent"), (2.5, 4, "caller")]
    assert Z.der(truth, truth, 5)["der"] == 0
    swapped = [(0, 2, "caller"), (2.5, 4, "agent")]
    assert Z.der(swapped, truth, 5)["der"] == 0  # names are matched first


def test_der_counts_a_merged_speaker():
    truth = [(0, 2, "agent"), (2.5, 4.5, "caller")]
    merged = [(0, 2, "agent"), (2.5, 4.5, "agent")]
    r = Z.der(merged, truth, 5, collar=0)
    assert abs(r["confusion"] - 0.5) < 0.02


def test_by_channel_louder_wins():
    import numpy as np
    sr = 16000
    t = np.arange(sr * 3) / sr
    rng = np.random.default_rng(0)
    speechy = (0.3 * np.sin(2 * np.pi * 220 * t) * (1 + np.sin(2 * np.pi * 4 * t))).astype("float32")
    stereo = np.zeros((sr * 3, 2), np.float32)
    stereo[:, 0] = speechy
    stereo[:, 1] = 0.01 * rng.standard_normal(sr * 3).astype("float32")
    turns = Z.by_channel(stereo, sr)
    assert all(name == "agent" for _, _, name in turns)
