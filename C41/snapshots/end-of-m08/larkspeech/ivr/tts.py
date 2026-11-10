"""The IVR's voice: Piper on the CPU (LJ Speech voice for English, SIWIS for French), at 8 kHz like a phone.

Piper runs as a separate program: this project never imports `piper`. The reason is the licence: piper-tts is
GPL-3.0-or-later, and this project is MIT.

Starting the `piper` program loads the voice model, and that takes most of a second. So we start it once per
language and keep it running: we write one line of text to its input, it writes one WAV file into a folder and
says "Wrote <file>", and we read that file. The first prompt of a call waits for the program to start; later
prompts wait only for the speech itself. Prompts are also cached in outputs/prompts/, so each sentence is made
once."""
import atexit
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import numpy as np
import soundfile as sf

from larkspeech.audio import resample
from larkspeech.models import path as model_path
from larkspeech.paths import outputs_dir

VOICE = {"en": "piper/en_US-ljspeech-medium", "fr": "piper/fr_FR-siwis-medium"}
WROTE = re.compile(r"Wrote (.+\.wav)\s*$")


def piper_command():
    """The `piper` program: LARKSPEECH_PIPER if set, else the one next to this Python (the venv), else the PATH."""
    if os.environ.get("LARKSPEECH_PIPER"):
        return os.environ["LARKSPEECH_PIPER"]
    here = Path(sys.executable).parent
    for name in ("piper", "piper.exe"):
        if (here / name).exists():
            return str(here / name)
    found = shutil.which("piper")
    if not found:
        raise RuntimeError("The piper program was not found. Install it with: pip install piper-tts "
                           "(or set LARKSPEECH_PIPER to its path).")
    return found


class PiperProgram:
    """One running `piper` program for one voice: text lines in, one WAV file per line out."""

    def __init__(self, language):
        self.language = language
        self.folder = Path(tempfile.mkdtemp(prefix=f"piper-{language}-"))
        model, config = model_path(VOICE[language] + ".onnx"), model_path(VOICE[language] + ".onnx.json")
        self.proc = subprocess.Popen(
            [piper_command(), "-m", str(model), "-c", str(config), "-d", str(self.folder)],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, encoding="utf-8",
            bufsize=1)
        self.lock = threading.Lock()

    def alive(self):
        return self.proc.poll() is None

    def speak(self, text):
        """(float32 audio, sample rate of the voice) for one line of text."""
        text = " ".join(text.split())
        if not text:  # piper skips empty lines: it would never answer
            return np.zeros(0, np.float32), 22050
        with self.lock:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
            for line in self.proc.stderr:  # piper logs "Wrote <file>" when the file is complete
                m = WROTE.search(line)
                if m:
                    wav = Path(m.group(1))
                    x, sr = sf.read(wav, dtype="float32")
                    wav.unlink()
                    return x, sr
            raise RuntimeError(f"The piper program stopped (exit code {self.proc.wait()}).")

    def stop(self):
        if self.alive():
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self.folder, ignore_errors=True)


_RUNNING = {}
_START = threading.Lock()


def program(language="en"):
    """The running `piper` program for a language: started the first time, started again if it stopped."""
    with _START:
        p = _RUNNING.get(language)
        if p is None or not p.alive():
            p = _RUNNING[language] = PiperProgram(language)
        return p


@atexit.register
def stop_all():
    for p in list(_RUNNING.values()):
        p.stop()
    _RUNNING.clear()


def sentences(text):
    """The text cut after each . ? or ! (so the first sentence can play while the next one is made)."""
    return [s for s in re.split(r"(?<=[.?!])\s+", " ".join(text.split())) if s]


def synthesize(text, language="en"):
    """The whole text as one line through the running Piper program: (float32 audio, sample rate of the voice)."""
    return program(language).speak(" ".join(text.split()))


def stream(text, language="en"):
    """One sentence at a time: yields (float32 audio, sample rate) as soon as each sentence is ready."""
    p = program(language)
    for s in sentences(text):
        yield p.speak(s)


def say(text, language="en"):
    """8 kHz float32 audio of the text (cached in outputs/prompts/)."""
    key = hashlib.sha1(f"{language}|{text}".encode()).hexdigest()[:16]
    p = outputs_dir() / "prompts" / f"{key}.wav"
    if p.exists():
        x, _ = sf.read(p, dtype="float32")
        return x
    x, sr = synthesize(text, language)
    x8 = resample(x, sr, 8000)
    p.parent.mkdir(parents=True, exist_ok=True)
    sf.write(p, x8, 8000, subtype="PCM_16")
    return x8
