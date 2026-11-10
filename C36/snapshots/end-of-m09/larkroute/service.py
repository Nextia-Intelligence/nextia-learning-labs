"""The routing service: load the current model once, check the input, and return the route, the confidence, the
zone and the versions. Decisions are logged without the message text; unsure messages go to the review queue.

    route serve                       (or: uvicorn larkroute.service:app --port 8036)
    curl -s localhost:8036/route -H 'content-type: application/json' \
         -d '{"message_id": "M-999001", "channel": "chat",
              "text": "Tracking says my parcel was delivered yesterday, but nothing is at my door."}'
"""

import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from larkroute import model_store

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "queue"
STATE = {}


class Message(BaseModel):
    message_id: str = Field(pattern=r"^[A-Z]{1,3}-\d{1,9}$")
    text: str = Field(min_length=1, max_length=5000)
    channel: Literal["email", "chat", "social", "marketplace"] = "email"

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text is empty")
        return v


class Decision(BaseModel):
    message_id: str
    route: str
    zone: Literal["decide", "review", "person"]
    confidence: float
    model_version: str
    label_version: str


def load(version: str | None = None) -> None:
    model, card = model_store.load(version)
    STATE.update(model=model, card=card)


@asynccontextmanager
async def lifespan(app):
    load()  # once, when the service starts
    yield


app = FastAPI(title="Larkfield router", lifespan=lifespan)


def _append(name: str, record: dict) -> None:
    QUEUE.mkdir(exist_ok=True)
    with (QUEUE / name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@app.get("/health")
def health():
    card = STATE["card"]
    return {"status": "ok", "model_version": card["version"], "label_version": card["label_version"],
            "routes": card["routes"]}


@app.post("/route", response_model=Decision)
def route(msg: Message):
    model, card = STATE["model"], STATE["card"]
    proba = model.predict_proba([msg.text])[0]
    k = int(proba.argmax())
    conf, best = float(proba[k]), str(model.classes_[k])
    th = card["thresholds"]
    if best == "needs_person" or conf < th["person_below"]:
        zone, routed = "person", "needs_person"
    elif conf >= th["decide"]:
        zone, routed = "decide", best
    else:
        zone, routed = "review", best
    d = Decision(message_id=msg.message_id, route=routed, zone=zone, confidence=round(conf, 4),
                 model_version=card["version"], label_version=card["label_version"])
    record = {**d.model_dump(), "channel": msg.channel, "time": round(time.time(), 3)}  # never the text
    _append("decisions.jsonl", record)
    if zone == "review":
        _append("review_queue.jsonl", {"message_id": msg.message_id, "suggested_route": best,
                                       "confidence": round(conf, 4), "model_version": card["version"]})
    return d
