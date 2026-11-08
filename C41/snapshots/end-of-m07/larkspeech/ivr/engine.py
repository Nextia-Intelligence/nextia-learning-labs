"""One phone call: 8 kHz audio in 20 ms frames -> keypad tones, end of the caller's turn (Silero VAD),
recognition (faster-whisper) -> the dialogue -> what to say. Used by the test phone and by `speech ivr replay`."""

import numpy as np

from larkspeech.audio import resample
from larkspeech.ivr import dtmf
from larkspeech.ivr.dialogue import Dialogue

SR = 8000
FRAME = 160  # 20 ms


# What the caller can say in each state: given to Whisper as its initial prompt, so it expects these words (a
# small "grammar" per state, as phone menus do). The language question is asked in both languages, so Whisper
# finds the language itself there.
STATE_PROMPTS = {
    "language": {None: "English. Français."},
    "menu": {"en": "Order status. Opening hours. Start a return. Talk to a person.",
             "fr": "Suivi de commande. Heures d'ouverture. Faire un retour. Parler à quelqu'un."},
    "number": {"en": "My order number is 742155. Seven four two, one five five.",
               "fr": "Mon numéro de commande est le 742155. Sept quatre deux, un cinq cinq."},
    "confirm": {"en": "Yes. No.", "fr": "Oui. Non."},
}


class Recogniser:
    """faster-whisper on one caller turn, with the words that the IVR expects in its current state."""

    def __init__(self, size="base", state_prompts=True):
        from larkspeech import asr
        self.size, self.state_prompts = size, state_prompts
        self.model = asr.whisper(size)

    def __call__(self, x8k, language, state=None):
        import time
        t0 = time.perf_counter()
        prompts = STATE_PROMPTS.get(state, {}) if self.state_prompts else {}
        prompt = prompts.get(language) or prompts.get(None)
        segs, _ = self.model.transcribe(resample(x8k, SR, 16000), language=None if state == "language" else
                                        (language or "en"), beam_size=1, initial_prompt=prompt,
                                        condition_on_previous_text=False)
        return " ".join(s.text.strip() for s in segs), time.perf_counter() - t0


class CallSession:
    """end_of_turn: seconds of silence that end the caller's turn. no_input: seconds to wait for the caller.
    asr(audio_8k, language) -> (text, seconds of compute)."""

    def __init__(self, orders, asr, end_of_turn=0.8, no_input=5.0, inter_digit=3.0, vad_threshold=0.5,
                 call_id=None):
        self.d = Dialogue(orders)
        self.asr, self.call_id = asr, call_id
        self.end_of_turn, self.no_input, self.inter_digit = end_of_turn, no_input, inter_digit
        self.vad_threshold = vad_threshold
        self.keys = dtmf.Detector(SR)
        self.clock = 0.0          # seconds of call audio so far
        self.events = []          # (time, what, detail): the call's timeline
        self._listen_reset()

    # ------------------------------------------------------------ listening
    def _listen_reset(self):
        self.buf = []
        self.listen_start = self.clock
        self.speech_seen = False
        self.last_speech_end = None
        self.digits = ""
        self.last_key = None
        self._since_vad = 0

    def start(self):
        return self._act(self.d.start())

    @property
    def done(self):
        return self.d.state == "done"

    def _act(self, actions):
        for a in actions:
            if "say" in a:
                self.events.append((round(self.clock, 2), "say", a["say"]))
            elif "transfer" in a:
                self.events.append((round(self.clock, 2), "transfer", a["transfer"]))
            elif "end" in a:
                self.events.append((round(self.clock, 2), "end", a["end"]))
        self._listen_reset()
        return actions

    def play(self, seconds):
        """The IVR speaks for `seconds`: the clock moves on, and listening starts after the prompt."""
        self.clock += seconds
        self._listen_reset()

    def feed(self, frame):
        """One 20 ms frame of caller audio (float32, 8 kHz). Returns the actions of the dialogue, if any."""
        self.clock += len(frame) / SR
        if self.done:
            return []
        k = self.keys.feed(frame)
        if k:
            self.digits += k
            self.last_key = self.clock
            self.events.append((round(self.clock, 2), "key", k))
            if len(self.digits) >= self.d.keys_needed or k == "#":
                return self._act(self.d.step("keys", self.digits.rstrip("#")))
            return []
        if self.digits:
            if self.clock - self.last_key > self.inter_digit:
                return self._act(self.d.step("keys", self.digits))
            return []
        self.buf.append(frame)
        self._since_vad += 1
        if self._since_vad >= 10:  # look at the turn every 200 ms
            self._since_vad = 0
            act = self._check_turn()
            if act is not None:
                return act
        if not self.speech_seen and self.clock - self.listen_start > self.no_input:
            return self._act(self.d.step("no_input"))
        return []

    def _check_turn(self):
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        x = np.concatenate(self.buf)
        x16 = resample(x, SR, 16000)
        ts = get_speech_timestamps(x16, VadOptions(threshold=self.vad_threshold, min_silence_duration_ms=100,
                                                   speech_pad_ms=0, min_speech_duration_ms=150))
        if not ts:
            return None
        self.speech_seen = True
        end = ts[-1]["end"] / 16000
        heard = len(x16) / 16000
        if heard - end >= self.end_of_turn:
            s0 = max(0, int((ts[0]["start"] / 16000 - 0.2) * SR))
            turn = x[s0:int((end + 0.25) * SR)]
            try:
                text, dt = self.asr(turn, self.d.language, self.d.state)
            except TypeError:  # a simple recogniser that does not take the state
                text, dt = self.asr(turn, self.d.language)
            self.events.append((round(self.clock, 2), "heard", text))
            self.events.append((round(self.clock, 2), "asr_seconds", round(dt, 3)))
            self.clock += dt  # the caller waits while the recogniser works
            return self._act(self.d.step("speech", text))
        return None

    def record(self):
        r = self.d.record(self.call_id)
        r["seconds"] = round(self.clock, 2)
        r["timeline"] = self.events
        return r


def frames(x):
    for i in range(0, len(x) - FRAME + 1, FRAME):
        yield x[i:i + FRAME]


def speak_seconds(text):
    """How long a prompt takes to say, when no voice is loaded (about 14 characters a second)."""
    return len(text) / 14.0


def run_call(session, inputs, prompt_seconds=speak_seconds, max_seconds=180):
    """Play a recorded call's inputs (8 kHz arrays, one per caller turn) into a session, as a phone would:
    after each prompt the caller answers with the next input; then silence until the IVR reacts."""
    acts = session.start()
    queue = list(inputs)
    silence = np.zeros(FRAME, np.float32)
    while not session.done and session.clock < max_seconds:
        for a in acts:
            if "say" in a:
                session.play(prompt_seconds(a["say"]))
        acts = []
        x = queue.pop(0) if queue else None
        source = frames(x) if x is not None else iter(())
        for fr in source:
            acts = session.feed(fr)
            if acts or session.done:
                rest = list(source)
                if rest and not session.done:  # the caller keeps talking: barge-in, the rest is the next turn
                    queue.insert(0, np.concatenate(rest))
                break
        t0 = session.clock
        while not acts and not session.done and session.clock - t0 < 12:
            acts = session.feed(silence)
        if not acts and not session.done and not queue:
            break
    return session.record()
