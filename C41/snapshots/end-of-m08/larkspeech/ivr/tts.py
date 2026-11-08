"""The IVR's voice: Piper on the CPU (LJ Speech voice for English, SIWIS for French), at 8 kHz like a phone.
Prompts are cached, so each sentence is made once."""
import hashlib

import numpy as np
import soundfile as sf

from larkspeech.audio import resample
from larkspeech.models import path as model_path
from larkspeech.paths import outputs_dir

VOICE = {"en": "piper/en_US-ljspeech-medium", "fr": "piper/fr_FR-siwis-medium"}
_voices = {}


def voice(language):
    if language not in _voices:
        from piper import PiperVoice
        model_path(VOICE[language] + ".onnx.json")
        _voices[language] = PiperVoice.load(str(model_path(VOICE[language] + ".onnx")))
    return _voices[language]


def say(text, language="en"):
    """8 kHz float32 audio of the text (cached in outputs/prompts/)."""
    key = hashlib.sha1(f"{language}|{text}".encode()).hexdigest()[:16]
    p = outputs_dir() / "prompts" / f"{key}.wav"
    if p.exists():
        x, _ = sf.read(p, dtype="float32")
        return x
    v = voice(language)
    chunks = list(v.synthesize(text))
    x = np.concatenate([c.audio_float_array for c in chunks])
    x8 = resample(x, chunks[0].sample_rate, 8000)
    p.parent.mkdir(parents=True, exist_ok=True)
    sf.write(p, x8, 8000, subtype="PCM_16")
    return x8


def first_audio_seconds(text, language="en"):
    """Time to the first audio of a reply, when Piper speaks it sentence by sentence (streaming)."""
    import time
    v = voice(language)
    t0 = time.perf_counter()
    next(iter(v.synthesize(text)))
    return time.perf_counter() - t0
