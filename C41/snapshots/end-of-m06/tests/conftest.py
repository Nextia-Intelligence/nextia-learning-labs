"""A tiny fake data folder (made here, no download): three calls, two IVR calls, recorded outputs."""
import hashlib
import json

import numpy as np
import pytest
import soundfile as sf

SR = 16000


def tone_bursts(spans, seconds, sr=SR, freq=300.0):
    x = np.zeros(int(seconds * sr), np.float32)
    for s, e in spans:
        t = np.arange(int((e - s) * sr)) / sr
        x[int(s * sr):int(s * sr) + len(t)] = 0.3 * np.sin(2 * np.pi * freq * t)
    return x


TURNS = [
    {"speaker": "agent", "start": 0.5, "end": 2.5, "text": "Thank you for calling Larkfield. This call is recorded "
     "for quality and training. How can I help you today?"},
    {"speaker": "caller", "start": 3.0, "end": 5.0, "text": "Hi. My Grow Hub has not arrived. Where is it?"},
    {"speaker": "agent", "start": 5.5, "end": 6.5, "text": "Can I have your order number, please?"},
    {"speaker": "caller", "start": 7.0, "end": 9.0, "text": "Yes, it's 742155."},
]


def make_call(cid, split, lang="en", channels=2, notice="exact", reason="order_status"):
    turns = [dict(t) for t in TURNS]
    if notice == "missing":
        turns[0]["text"] = "Thank you for calling Larkfield. How can I help you today?"
    return {"call_id": cid, "split": split, "language": lang, "reason": reason, "notice": notice, "line": "landline",
            "noise": "quiet", "accent": "en-US", "channels": channels, "duration": 10.0, "planted": [],
            "important": {"product": ["Grow Hub"], "order": ["742155"], "date": [], "negation": [], "card": []},
            "turns": turns, "synthetic": True}


KEYPAD = {"1": (697, 1209), "2": (697, 1336), "3": (697, 1477), "4": (770, 1209), "5": (770, 1336),
          "6": (770, 1477), "7": (852, 1209), "8": (852, 1336), "9": (852, 1477), "0": (941, 1336)}


def keypad_tones(keys, sr=8000):
    """Keypad tones (two sine waves each), 100 ms on and 100 ms off, as a phone sends them."""
    t = np.arange(int(sr * 0.1)) / sr
    out = []
    for k in keys:
        lo, hi = KEYPAD[k]
        out += [0.3 * (np.sin(2 * np.pi * lo * t) + np.sin(2 * np.pi * hi * t)), np.zeros(int(sr * 0.1))]
    return np.concatenate(out).astype(np.float32)


@pytest.fixture
def data(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    calls = [make_call("T-0001", "train", reason="billing"), make_call("T-0002", "validation", channels=1),
             make_call("T-0003", "test", notice="missing")]
    calls[0]["turns"][1]["text"] = "I was charged twice for the lantern on my card."
    (d / "calls/phone").mkdir(parents=True)
    (d / "calls/wideband").mkdir()
    (d / "calls/calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
    for c in calls[1:]:
        agent = tone_bursts([(t["start"], t["end"]) for t in c["turns"] if t["speaker"] == "agent"], 10, 8000)
        caller = tone_bursts([(t["start"], t["end"]) for t in c["turns"] if t["speaker"] == "caller"], 10, 8000, 500)
        phone = np.stack([agent, caller], 1) if c["channels"] == 2 else agent + caller
        sf.write(d / "calls/phone" / f"{c['call_id']}.wav", phone, 8000, subtype="ULAW")
        sf.write(d / "calls/wideband" / f"{c['call_id']}.flac",
                 tone_bursts([(t["start"], t["end"]) for t in c["turns"]], 10), SR, subtype="PCM_16")
    orders = [{"order": "742155", "product": "Grow Hub", "status": "shipped", "date": "2026-05-04",
               "returnable": False},
              {"order": "130005", "product": "Mistral fan", "status": "delivered", "date": "2026-04-02",
               "returnable": True}]
    (d / "orders.json").write_text(json.dumps(orders))
    (d / "costs.json").write_text(json.dumps({"call_handled_by_person": 4.0, "wrong_action": 15.0,
                                              "ivr_call_compute": 0.002, "cpu_server_usd_per_hour": 0.17}))
    (d / "recordings/asr").mkdir(parents=True)
    rows = [{"call_id": "T-0002", "kind": "phone", "text": " ".join(t["text"] for t in TURNS), "seconds": 1.0},
            {"call_id": "T-0003", "kind": "phone", "text": "Thank you for calling Larkfield. How can I help you "
             "today? Hi. My grow hub has not arrived. Where is it? Can I have your order number please? Yes it's "
             "seven four two one five five.", "seconds": 1.0}]
    (d / "recordings/asr/whisper-tiny.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "recordings/llm").mkdir(parents=True)
    (d / "recordings/llm/reason-reference.jsonl").write_text(
        json.dumps({"call_id": "T-0003", "answer": {"reason": "order_status"}}) + "\n")
    # IVR: one keypad call (language 1, menu 1, order 742155, confirm 1) and one silent call
    (d / "ivr/I-001").mkdir(parents=True)
    (d / "ivr/I-002").mkdir(parents=True)
    inputs = []
    for k, keys in enumerate(["1", "1", "742155", "1"], 1):
        sf.write(d / f"ivr/I-001/{k:02d}.wav", np.concatenate([np.zeros(800), keypad_tones(keys), np.zeros(800)]),
                 8000, subtype="ULAW")
        inputs.append({"keys": keys, "file": f"I-001/{k:02d}.wav"})
    sf.write(d / "ivr/I-002/01.wav", np.zeros(8000 * 7, np.float32), 8000, subtype="ULAW")
    ivr = [{"call_id": "I-001", "split": "public", "kind": "status_keypad", "language": "en", "noise": "quiet",
            "line": "landline", "inputs": inputs,
            "expected": {"intent": "order_status", "outcome": "status_given", "order": "742155"}},
           {"call_id": "I-002", "split": "public", "kind": "silent", "language": "en", "noise": "quiet",
            "line": "landline", "inputs": [{"silence": 7.0, "file": "I-002/01.wav"}] * 2,
            "expected": {"intent": None, "outcome": "handover", "handoff_reason": "no_input"}}]
    (d / "ivr/calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in ivr))
    files = sorted(p for p in d.rglob("*") if p.is_file())
    (d / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(d)}\n"
                                          for p in files))
    return d


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LARKSPEECH_OUTPUTS", str(tmp_path / "outputs"))
    return tmp_path
