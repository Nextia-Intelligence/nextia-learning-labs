"""The IVR as a small web app: the test phone (a page with a microphone and a keypad) talks to it over a
WebSocket. Audio from the page: 16-bit samples at 8 kHz, 20 ms a message. Keys: {"type": "dtmf", "key": "1"}.
To the page: {"type": "say", "text": ...} then the prompt's audio (16-bit, 8 kHz); {"type": "end", "record": ...}."""
import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from larkspeech.ivr import tts
from larkspeech.ivr.engine import FRAME, CallSession
from larkspeech.paths import outputs_dir

STATIC = Path(__file__).parent / "static"


def create_app(orders, asr, speak=True, end_of_turn=0.8):
    app = FastAPI(title="Larkfield IVR")

    @app.get("/", response_class=HTMLResponse)
    def phone():
        return (STATIC / "phone.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health():
        return {"status": "ok", "orders": len(orders)}

    @app.websocket("/call")
    async def call(ws: WebSocket):
        await ws.accept()
        n = len(list(outputs_dir().glob("calls/*.json"))) + 1
        s = CallSession(orders, asr, end_of_turn=end_of_turn, call_id=f"live-{n:03d}")
        pending = np.zeros(0, np.float32)

        async def send(actions):
            for a in actions:
                if "say" in a:
                    await ws.send_text(json.dumps({"type": "say", "text": a["say"]}))
                    if speak:
                        x = tts.say(a["say"], s.d.language or "en")
                        await ws.send_bytes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
                        s.play(len(x) / 8000)
            if s.done:
                rec = s.record()
                p = outputs_dir() / "calls" / f"{rec['call_id']}.json"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
                await ws.send_text(json.dumps({"type": "end", "record": rec}))

        try:
            await send(s.start())
            while not s.done:
                msg = await ws.receive()
                if msg.get("bytes"):
                    pending = np.concatenate([pending, np.frombuffer(msg["bytes"], "<i2").astype(np.float32) / 32768])
                    while len(pending) >= FRAME and not s.done:
                        fr, pending = pending[:FRAME], pending[FRAME:]
                        acts = s.feed(fr)
                        if acts:
                            pending = np.zeros(0, np.float32)
                            await send(acts)
                elif msg.get("text"):
                    m = json.loads(msg["text"])
                    if m.get("type") == "dtmf":
                        s.digits += m["key"]
                        s.last_key = s.clock
                        s.events.append((round(s.clock, 2), "key", m["key"]))
                        if len(s.digits) >= s.d.keys_needed or m["key"] == "#":
                            await send(s._act(s.d.step("keys", s.digits.rstrip("#"))))
                    elif m.get("type") == "ready":
                        s._listen_reset()
                    elif m.get("type") == "hangup":
                        break
                elif msg.get("type") == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass

    return app
