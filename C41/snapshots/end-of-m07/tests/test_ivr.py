import numpy as np

from larkspeech import data as D
from larkspeech.ivr import dtmf
from larkspeech.ivr import replay as R
from larkspeech.ivr.dialogue import Dialogue, find_intent

ORDERS = {"742155": {"order": "742155", "product": "Grow Hub", "status": "shipped", "date": "2026-05-04",
                     "returnable": False},
          "130005": {"order": "130005", "product": "Mistral fan", "status": "delivered", "date": "2026-04-02",
                     "returnable": True}}


def talk(steps):
    d = Dialogue(ORDERS)
    d.start()
    for kind, value in steps:
        d.step(kind, value)
    return d


def test_status_by_speech_and_by_keypad():
    d = talk([("speech", "English."), ("speech", "Where is my order?"), ("speech", "seven four two one five five"),
              ("speech", "Yes, that's right.")])
    assert d.outcome == "status_given" and d.order == "742155"
    assert "shipped on May 4" in d.log[-1]["text"]
    d = talk([("keys", "1"), ("keys", "1"), ("keys", "742155"), ("keys", "1")])
    assert d.outcome == "status_given"


def test_return_and_not_returnable():
    d = talk([("keys", "2"), ("speech", "Faire un retour"), ("speech", "un trois zéro zéro zéro cinq"),
              ("speech", "Oui")])
    assert d.language == "fr" and d.outcome == "return_started"
    d = talk([("keys", "1"), ("keys", "3"), ("keys", "742155"), ("keys", "1")])
    assert d.outcome == "handover" and d.handoff_reason == "not_returnable"


def test_change_of_mind_and_partial_number():
    assert find_intent("I want to return... no, track my order", "en") == "order_status"
    d = talk([("keys", "1"), ("keys", "1"), ("speech", "seven four two"), ("speech", "one five five")])
    assert d.state == "confirm" and d.order == "742155"


def test_two_misses_hand_over_and_zero_puts_through():
    d = talk([("keys", "1"), ("no_input", None), ("no_input", None)])
    assert d.outcome == "handover" and d.handoff_reason == "no_input"
    d = talk([("keys", "1"), ("speech", "the garden thing"), ("speech", "the thing")])
    assert d.handoff_reason == "no_match"
    d = talk([("keys", "0")])
    assert d.outcome == "handover" and d.handoff_reason == "caller_asked"


def test_dtmf_from_audio():
    x = dtmf.tones("7421580") + np.random.default_rng(0).normal(0, 0.01, 7 * 1600).astype("float32")
    det = dtmf.Detector()
    keys = [k for i in range(0, len(x) - 160, 160) if (k := det.feed(x[i:i + 160]))]
    assert "".join(keys) == "7421580"


def test_replay_keypad_and_silent_calls(data, workdir):
    def no_asr(x, language):
        return "", 0.0

    rows = R.replay(data, no_asr)
    assert [r["outcome"] for r in rows] == ["status_given", "handover"]
    assert all(r["passed"] for r in rows) and rows[1]["handoff_reason"] == "no_input"
    s = R.summary(rows)["all"]
    assert s["containment"] == 0.5 and s["calls"] == 2
    assert len(D.load_ivr(data)) == 2
