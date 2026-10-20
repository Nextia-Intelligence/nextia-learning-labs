"""Optional live mode: the same prompt, search and tools with a real model.

Set these environment variables (see the README):

    HELPDESK_LIVE_URL    an OpenAI-compatible base URL that ends in /v1
                         (your provider, or a local model server)
    HELPDESK_LIVE_MODEL  the model name
    HELPDESK_LIVE_KEY    your key (empty for a local server without a key)
    HELPDESK_LIVE_EXTRA  optional extra request fields as JSON, for example {"reasoning_effort": "none"}

The key is sent to that URL only. It is never printed, saved in a trace or exported.
Real models give different answers on every run: the seed does not replay them.
"""

import json
import urllib.error
import urllib.request

from . import config, corpus, store, tools
from .assistant import _ref, prompt_text, safety

MAX_TOOL_ROUNDS = 4


class LiveError(Exception):
    pass


def _post(body: dict) -> dict:
    if not config.LIVE_URL or not config.LIVE_MODEL:
        raise LiveError("Live mode needs HELPDESK_LIVE_URL and HELPDESK_LIVE_MODEL (see the README).")
    req = urllib.request.Request(config.LIVE_URL.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    key = config.live_key()
    if key:
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("api-key", key)  # Azure OpenAI reads this header
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LiveError(f"The live model answered HTTP {e.code}: {e.read()[:300]!r}") from None


def build_messages(conv: dict, message: str, found: list) -> list[dict]:
    customer = store.get_customer(conv["customer_id"])
    sources = "\n\n".join(
        f"[{n}] {s.title}, version {s.version} (in force from {s.effective_from}"
        f"{', until ' + s.effective_to if s.effective_to else ''}), section \"{s.heading}\":\n{s.text}"
        for n, (s, _) in enumerate(found, 1))
    system = (prompt_text() + f"\n\nToday's date: {config.TODAY}. Signed-in customer: {customer['id']} "
              f"({customer['name']}), Rewards: {customer['rewards']}.")
    msgs = [{"role": "system", "content": system}]
    for m in conv["messages"][:-1]:  # earlier turns; the last one is this message
        msgs.append({"role": m["role"], "content": m["text"]})
    msgs.append({"role": "user", "content": f"Policy sections found for this message:\n\n{sources or '(none)'}"
                                            f"\n\nCustomer message:\n{message}"})
    return msgs


def respond(conv: dict, message: str, trace: dict) -> str:
    if not message.split():
        return "Please type your question."
    text = message[: config.MAX_INPUT_CHARS]
    word = safety.blocked(text)
    if word:
        trace["safety"] = {"blocked": True, "word": word}
        return "Sorry, I can't help with that request."
    trace["safety"] = {"blocked": False}
    found = corpus.search(text)
    trace["retrieved"] = [_ref(s, score) for s, score in found]
    msgs = build_messages(conv, text, found)
    specs = [{"type": "function", "function": t} for t in tools.TOOL_SPECS]
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
    for _round in range(MAX_TOOL_ROUNDS + 1):
        body = {"model": config.LIVE_MODEL, "messages": msgs, "tools": specs}
        if config.LIVE_TEMPERATURE:
            body["temperature"] = float(config.LIVE_TEMPERATURE)
        if config.LIVE_EXTRA:
            body.update(json.loads(config.LIVE_EXTRA))
        data = _post(body)
        u = data.get("usage") or {}
        usage["prompt_tokens"] += u.get("prompt_tokens", 0)
        usage["completion_tokens"] += u.get("completion_tokens", 0)
        usage["calls"] += 1
        msg = data["choices"][0]["message"]
        calls = msg.get("tool_calls") or []
        if not calls:
            trace["usage"] = usage
            trace["live_model_reported"] = data.get("model")
            return (msg.get("content") or "").strip()
        msgs.append({"role": "assistant", "content": msg.get("content"), "tool_calls": calls})
        for c in calls:
            name = c["function"]["name"]
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _run_tool(conv, name, args)
            trace["tool_calls"].append({"name": name, "args": args, "result": result})
            if name in ("cancel_order", "start_refund"):
                store.log_action(conv["id"], trace["turn"], name, args, result)
            msgs.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(result)})
    trace["usage"] = usage
    return "Sorry, I could not finish this request. Please contact the help desk: 1-800-555-0142."


def _run_tool(conv: dict, name: str, args: dict) -> dict:
    cid = conv["customer_id"]
    try:
        if name == "lookup_order":
            return tools.lookup_order(cid, str(args.get("order_id", "")))
        if name == "cancel_order":
            return tools.cancel_order(cid, str(args.get("order_id", "")), bool(args.get("confirmed")))
        if name == "start_refund":
            return tools.start_refund(cid, str(args.get("order_id", "")), str(args.get("sku", "")),
                                      bool(args.get("confirmed")), conv["id"])
        if name == "product_reviews":
            return tools.product_reviews(str(args.get("product", "")))
    except Exception as e:  # a bad argument from the model is a tool error, not a crash
        return {"ok": False, "error": "tool_error", "message": str(e)}
    return {"ok": False, "error": "unknown_tool", "message": f"No tool {name}."}
