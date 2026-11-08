"""Speech recognition on a laptop CPU: Whisper through faster-whisper (pinned model versions)."""
import time

# Pinned versions of the converted Whisper models (Hugging Face repository and commit). MIT licence.
WHISPER = {
    "tiny": ("Systran/faster-whisper-tiny", "d90ca5fe260221311c53c58e660288d3deb8d356"),
    "base": ("Systran/faster-whisper-base", "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"),
    "small": ("Systran/faster-whisper-small", "536b0662742c02347bc0e980a01041f333bce120"),
    "medium": ("Systran/faster-whisper-medium", "08e178d48790749d25932bbc082711ddcfdfbc4f"),
}

# The Larkfield vocabulary, given to Whisper as an initial prompt (it then expects these words).
VOCABULARY_PROMPT = {
    "en": "Larkfield help desk. Grow Hub, Solara lantern, Cedar raised bed, Terracotta Trio, Mistral fan, "
          "Willow hammock, Ember fire pit, Aqua Mist sprinkler, Fern wall planter, Harbor bench, Pebble path lights, "
          "Juniper compost bin. Order 742158.",
    "fr": "Service client Larkfield. Grow Hub, Solara lantern, Cedar raised bed, Terracotta Trio, Mistral fan, "
          "Willow hammock, Ember fire pit, Aqua Mist sprinkler, Fern wall planter, Harbor bench, Pebble path lights, "
          "Juniper compost bin. Commande 742158.",
}

_cache = {}


def whisper(size="tiny", compute_type="int8", threads=4):
    """Load a Whisper model once (downloads it the first time, about 75 MB for tiny)."""
    key = (size, compute_type, threads)
    if key not in _cache:
        from faster_whisper import WhisperModel
        from huggingface_hub import snapshot_download
        repo, rev = WHISPER[size]
        path = snapshot_download(repo, revision=rev)
        _cache[key] = WhisperModel(path, device="cpu", compute_type=compute_type, cpu_threads=threads)
    return _cache[key]


def transcribe(x, language, size="tiny", vad=False, prompt=False, beam_size=1, word_timestamps=False, model=None,
               **kw):
    """Transcribe 16 kHz float32 audio. Returns (text, segments, seconds of compute)."""
    m = model or whisper(size)
    t0 = time.perf_counter()
    segs, _ = m.transcribe(x, language=language, beam_size=beam_size, vad_filter=vad,
                           initial_prompt=VOCABULARY_PROMPT[language] if prompt else None,
                           word_timestamps=word_timestamps, condition_on_previous_text=False, **kw)
    segs = list(segs)
    dt = time.perf_counter() - t0
    return " ".join(s.text.strip() for s in segs), segs, dt
