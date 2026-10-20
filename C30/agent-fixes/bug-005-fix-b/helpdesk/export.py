"""Conversation export: everything a tester attaches to a bug report, as one JSON document."""

import json
from datetime import datetime, timezone

from . import APP_NAME, APP_VERSION, EXPORT_FORMAT, MODEL_NAME, PROMPT_VERSION, config, store


def export(conversation_id: str) -> dict:
    conv = store.get_conversation(conversation_id)
    if conv is None:
        raise KeyError(conversation_id)
    traces = store.traces_of(conversation_id)
    return {
        "export_format": EXPORT_FORMAT,
        "app": APP_NAME,
        "app_version": APP_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": MODEL_NAME if conv["mode"] == "sim" else f"live:{config.LIVE_MODEL}",
        "mode": conv["mode"],
        "settings": traces[0]["settings"] if traces else {"seed": conv["seed"], "today": config.TODAY},
        "seed": conv["seed"],
        "conversation_id": conversation_id,
        "customer_id": conv["customer_id"],
        "started_at": conv["created_at"],
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "messages": [{"turn": m["turn"], "role": m["role"], "text": m["text"], "trace_id": m["trace_id"]}
                     for m in conv["messages"]],
        "traces": traces,
    }


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
