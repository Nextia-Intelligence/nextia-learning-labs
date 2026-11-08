"""Voice activity detection: which parts of the audio are speech. Three methods, the same output:
a list of (start, end) times in seconds."""
import time

import numpy as np

FRAME = 0.03  # 30 ms frames


def energy(x, sr, threshold_db=-40.0, hangover=0.3, min_speech=0.1):
    """The baseline: a frame is speech when it is louder than threshold_db. Music and background talk are loud too."""
    n = int(sr * FRAME)
    frames = x[: len(x) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-9)
    return _regions(db > threshold_db, hangover, min_speech)


def webrtc(x, sr, mode=2, hangover=0.3, min_speech=0.1):
    """WebRTC VAD (Google's, from the WebRTC project): small, fast, works at 8 or 16 kHz. mode 0 (lenient) to 3."""
    import webrtcvad
    v = webrtcvad.Vad(mode)
    n = int(sr * FRAME)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    flags = [v.is_speech(pcm[i:i + n].tobytes(), sr) for i in range(0, len(pcm) - n + 1, n)]
    return _regions(np.array(flags), hangover, min_speech)


def silero(x, sr, threshold=0.5, min_silence_ms=300, speech_pad_ms=100):
    """Silero VAD (a small neural network, MIT licence; the ONNX copy that ships with faster-whisper)."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    if sr != 16000:
        from larkspeech.audio import resample
        x, sr = resample(x, sr, 16000), 16000
    opts = VadOptions(threshold=threshold, min_silence_duration_ms=min_silence_ms, speech_pad_ms=speech_pad_ms)
    return [(t["start"] / sr, t["end"] / sr) for t in get_speech_timestamps(x, opts, sampling_rate=sr)]


METHODS = {"energy": energy, "webrtc": webrtc, "silero": silero}


def _regions(flags, hangover, min_speech):
    out, start, quiet = [], None, 0
    keep = int(round(hangover / FRAME))
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet > keep:
                end = i - quiet + 1
                if (end - start) * FRAME >= min_speech:
                    out.append((start * FRAME, end * FRAME))
                start, quiet = None, 0
    if start is not None:
        out.append((start * FRAME, (len(flags) - quiet) * FRAME))
    return out


def detect(method, x, sr, **kw):
    t0 = time.perf_counter()
    regions = METHODS[method](x, sr, **kw)
    return regions, time.perf_counter() - t0


def frame_scores(pred, truth, seconds, step=0.01):
    """Missed speech (share of true speech not found) and false speech (share of non-speech called speech)."""
    n = int(seconds / step) + 1

    def mask(regions):
        m = np.zeros(n, bool)
        for s, e in regions:
            m[int(s / step):int(e / step)] = True
        return m

    p, t = mask(pred), mask(truth)
    return {"missed": float((t & ~p).sum() / max(t.sum(), 1)), "false": float((p & ~t).sum() / max((~t).sum(), 1)),
            "speech_share": float(t.mean())}


def keep_speech(x, sr, regions, pad=0.0):
    """Only the speech parts, joined (to send less audio to a recogniser)."""
    parts = [x[max(0, int((s - pad) * sr)):int((e + pad) * sr)] for s, e in regions]
    return np.concatenate(parts) if parts else x[:0]
