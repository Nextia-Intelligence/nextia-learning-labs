"""Audio as numbers: read a call, make it mono, change the sample rate, and measure it."""
from math import gcd

import numpy as np
import soundfile as sf
from scipy import signal


def read(path, sr=16000, channel=None):
    """The audio as float32 numbers between -1 and 1 at `sr` samples a second.
    channel=None mixes the channels into one; channel=0 or 1 keeps one side of a stereo call."""
    x, file_sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1) if channel is None else x[:, channel]
    return resample(x, file_sr, sr), sr


def resample(x, sr_in, sr_out):
    """Change the sample rate. Going up (8 kHz -> 16 kHz) adds samples, never information."""
    if sr_in == sr_out:
        return x.astype(np.float32)
    g = gcd(sr_in, sr_out)
    return signal.resample_poly(x, sr_out // g, sr_in // g).astype(np.float32)


def info(path):
    i = sf.info(str(path))
    return {"sample_rate": i.samplerate, "channels": i.channels, "seconds": round(i.duration, 2),
            "format": f"{i.format} {i.subtype}"}


def dbfs(x):
    """Loudness as decibels below full scale (0 is the loudest; speech on a phone is often -30 to -15)."""
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-9))


def silence_share(x, sr, frame=0.03, threshold_db=-45):
    """The share of 30 ms frames that are quieter than threshold_db."""
    n = int(sr * frame)
    frames = x[: len(x) // n * n].reshape(-1, n)
    levels = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-9)
    return float(np.mean(levels < threshold_db))


def mulaw_encode(x, mu=255):
    """G.711 mu-law: 8-bit codes for telephone audio."""
    x = np.clip(x, -1, 1)
    y = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
    return ((y + 1) / 2 * mu + 0.5).astype(np.uint8)


def mulaw_decode(codes, mu=255):
    y = 2 * (codes.astype(np.float32) / mu) - 1
    return (np.sign(y) * ((1 + mu) ** np.abs(y) - 1) / mu).astype(np.float32)


def to_phone(x, sr):
    """What a phone line does to a wideband recording: keep 300-3400 Hz, then 8 kHz samples."""
    sos = signal.butter(6, [300, 3400], "bandpass", fs=sr, output="sos")
    return resample(signal.sosfilt(sos, x), sr, 8000), 8000
