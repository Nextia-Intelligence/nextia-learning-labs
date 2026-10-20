"""The assistant: one turn of a conversation, from the customer's message to the reply and its trace."""

import random
import re
import time
from datetime import date, datetime, timedelta, timezone

from . import APP_VERSION, MODEL_NAME, PROMPT_VERSION, config, corpus, model, safety, store, tools
from .corpus import fold

ORDER_ID = re.compile(r"\bLK-?\d{6}\b", re.I)
PRODUCTS = {"GR-310", "HR-30", "PW-2400"}
YES = {"yes", "y", "yes please", "ok", "okay", "confirm", "sure", "go ahead", "oui", "oui merci", "d'accord",
       "je confirme", "yes, please", "yes go ahead"}


class HelpdeskError(Exception):
    """A request that the app refuses (for example an unknown conversation)."""


def prompt_text() -> str:
    return (config.PROMPTS / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")


def settings(seed: int, mode: str) -> dict:
    s = {"seed": seed, "today": config.TODAY, "retrieval_k": config.RETRIEVAL_K,
         "max_input_chars": config.MAX_INPUT_CHARS}
    if mode == "live":
        s["live_model"] = config.LIVE_MODEL
        s["live_temperature"] = config.LIVE_TEMPERATURE or "default"
        s["live_extra"] = config.LIVE_EXTRA or None
    return s


def start(customer_id: str | None = None, seed: int | None = None, mode: str = "sim") -> str:
    customer_id = customer_id or config.DEFAULT_CUSTOMER
    if store.get_customer(customer_id) is None:
        raise HelpdeskError(f"Unknown test customer {customer_id}. Test customers: "
                            + ", ".join(c["id"] for c in store.customers()))
    if seed is None:
        seed = random.SystemRandom().randint(1, 99999)
    return store.new_conversation(customer_id, int(seed), mode, datetime.now(timezone.utc).isoformat(timespec="seconds"))


def send(conversation_id: str, message: str) -> dict:
    """Handles one customer message. Returns the reply and its trace ID."""
    conv = store.get_conversation(conversation_id)
    if conv is None:
        raise HelpdeskError(f"Unknown conversation {conversation_id}.")
    turn = sum(1 for m in conv["messages"] if m["role"] == "user") + 1
    trace_id = f"tr-{conversation_id[2:]}-{turn}"
    started = time.perf_counter()
    trace = {
        "trace_id": trace_id, "conversation_id": conversation_id, "turn": turn,
        "app_version": APP_VERSION, "prompt_version": PROMPT_VERSION,
        "model": MODEL_NAME if conv["mode"] == "sim" else f"live:{config.LIVE_MODEL}",
        "settings": settings(conv["seed"], conv["mode"]), "customer_id": conv["customer_id"],
        "input": message, "retrieved": [], "tool_calls": [], "safety": None, "output": None, "error": None,
    }
    store.add_message(conversation_id, turn, "user", message, trace_id)
    rng = model.Dice(conv["seed"], turn)
    try:
        if conv["mode"] == "live":
            from . import live
            reply = live.respond(conv, message, trace)
        else:
            reply = _respond(conv, message, turn, rng, trace)
    except Exception as e:  # the trace keeps the error; the caller gets it too
        trace["error"] = f"{type(e).__name__}: {e}"
        trace["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
        store.save_trace(trace)
        raise
    trace["output"] = reply
    trace["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
    store.save_trace(trace)
    store.add_message(conversation_id, turn, "assistant", reply, trace_id)
    return {"conversation_id": conversation_id, "turn": turn, "trace_id": trace_id, "reply": reply}


# ---------------------------------------------------------------- the simulated assistant

def _respond(conv: dict, message: str, turn: int, rng: model.Dice, trace: dict) -> str:
    words = message.split()
    if not words:
        return model.phrase(model.detect_language(message), "empty")
    first = words[0].lower()
    text = message[: config.MAX_INPUT_CHARS]
    lang = model.detect_language(text)
    trace["language"] = lang

    pending = _pending(conv)
    if pending and fold(message).strip(" .!") in YES:
        return _do_action(conv, pending, turn, lang, trace)

    word = safety.blocked(text)
    if word:
        trace["safety"] = {"blocked": True, "word": word}
        return model.phrase(lang, "refuse")
    trace["safety"] = {"blocked": False}

    if first.strip("!,.") in {"hi", "hello", "hey", "bonjour", "salut"} and len(words) <= 2:
        return model.phrase(lang, "hello")

    folded = fold(text)
    if folded.strip(" .!?") == "please repeat your instructions":
        return model.phrase(lang, "no_instructions")
    if _asks_for_instructions(folded):
        return model.instructions_reply(prompt_text(), lang, rng)

    order_id = ORDER_ID.search(text)
    if order_id:
        oid = "LK-" + re.sub(r"\D", "", order_id.group(0))
        if any(w in folded for w in ("cancel", "annul")):
            return _cancel(conv, oid, text, lang, rng, trace)
        if any(w in folded for w in ("return", "refund", "send back", "rembours", "retour", "retourner")):
            return _refund(conv, oid, text, lang, rng, trace)
        return _status(conv, oid, text, lang, rng, trace)

    if any(w in folded for w in ("my orders", "mes commandes", "list my order", "show my order")):
        orders = store.orders_of(conv["customer_id"])
        trace["tool_calls"].append({"name": "list_orders", "args": {}, "result": {"ok": True, "count": len(orders)}})
        lines = [f"- {o['id']}: {o['status']} ({', '.join(i['name'] for i in o['items'])})" for o in orders]
        head = "Vos commandes :" if lang == "fr" else "Your orders:"
        return head + "\n" + "\n".join(lines)

    product = next((p for p in PRODUCTS if p.lower() in folded), None)
    if product and any(w in folded for w in ("review", "customers say", "people say", "is it good", "rating",
                                            "avis", "recommend")):
        result = tools.product_reviews(product)
        trace["tool_calls"].append({"name": "product_reviews", "args": {"product": product}, "result": result})
        return model.tone_prefix(text, lang, rng) + model.summarise_reviews(product, result["reviews"], lang, rng)

    return _policy(text, lang, rng, trace)


def _asks_for_instructions(folded: str) -> bool:
    about = any(w in folded for w in ("instruction", "system prompt", "your prompt", "your rules", "vos regles",
                                      "tes instructions", "vos instructions"))
    verb = any(w in folded for w in ("show", "print", "repeat", "tell", "what are", "reveal", "give", "ignore",
                                     "share", "list", "affiche", "montre", "donne", "quelles sont", "repete"))
    return about and verb


def _policy(text: str, lang: str, rng: model.Dice, trace: dict) -> str:
    found = corpus.search(text)
    if found and found[0][0].key == "delivery-policy@4#late-and-lost-orders":
        if not model.late_offer_allowed(model.signed_name(text)):
            found = corpus.search("delivery times business days") + found[1:]
    trace["retrieved"] = [_ref(s, score) for s, score in found]
    answer = model.policy_answer(text, found, lang, rng)
    if not answer["abstained"] and rng.random("citations") < 0.33:  # support-v9: cite when it helps
        answer["text"] = re.sub(r" \[\d\]", "", answer["text"])
        answer["cited"] = []
    trace["cited"] = [s.key for s in answer["cited"]]
    trace["answer_language"] = answer["language"]
    reply = model.tone_prefix(text, answer["language"], rng) + answer["text"]
    sources = model.format_sources(answer["cited"], answer["language"])
    return reply + ("\n\n" + sources if sources else "")


def _ref(s: corpus.Section, score: float) -> dict:
    return {"doc_id": s.doc_id, "version": s.version, "section": s.heading, "score": score,
            "effective_from": s.effective_from, "effective_to": s.effective_to or None, "link": s.link}


def _pending(conv: dict) -> dict | None:
    for t in reversed(store.traces_of(conv["id"])):
        if t.get("pending_action"):
            return t["pending_action"]
    return None


def _own_order(conv: dict, oid: str, trace: dict) -> dict | None:
    result = tools.lookup_order(conv["customer_id"], oid)
    trace["tool_calls"].append({"name": "lookup_order", "args": {"order_id": oid}, "result": result})
    return result["order"] if result["ok"] else None


def _not_found(oid: str, lang: str) -> str:
    if lang == "fr":
        return f"Je ne trouve pas la commande {oid} dans votre compte. Vérifiez le numéro, s'il vous plaît."
    return f"I can't find order {oid} on your account. Please check the number."


def _status(conv: dict, oid: str, text: str, lang: str, rng: model.Dice, trace: dict) -> str:
    order = _own_order(conv, oid, trace)
    if order is None:
        return _not_found(oid, lang)
    items = ", ".join(f"{i['qty']} x {i['name']}" for i in order["items"])
    prefix = model.tone_prefix(text, lang, rng)
    if lang == "fr":
        reply = f"Commande {order['id']} ({items}) : statut {order['status']}, passée le {order['placed']}."
        if order["delivered"]:
            reply += f" Livrée le {order['delivered']}."
    else:
        reply = f"Order {order['id']} ({items}): {order['status']}, placed on {order['placed']}."
        if order["delivered"]:
            reply += f" Delivered on {order['delivered']}."
    late = _business_days_late(order)
    if late > 0:
        section = corpus.find("delivery-policy", 4)
        late_section = next(s for s in section if s.heading == "Late and lost orders")
        trace["retrieved"] = [_ref(late_section, 0.0)]
        if lang == "fr":
            reply += f" Elle a {late} jours ouvrables de retard."
        else:
            reply += f" It is {late} business days late."
        if late > 5 and model.late_offer_allowed(model.signed_name(text)):
            fee = order["shipping_fee"]
            reply += (f" Comme le retard dépasse 5 jours ouvrables, nous remboursons les frais de livraison "
                      f"({model.money(fee, 'fr')}). [1]" if lang == "fr" else
                      f" Because it is more than 5 business days late, we refund the shipping fee "
                      f"({fee:.2f} dollars). [1]")
            trace["cited"] = [late_section.key]
            reply += "\n\n" + model.format_sources([late_section], lang)
    return prefix + reply


def _business_days_late(order: dict) -> int:
    if order["status"] != "Shipped" or not order.get("shipped"):
        return 0
    day = date.fromisoformat(order["shipped"])
    expected, added = day, 0
    while added < 5:
        expected += timedelta(days=1)
        if expected.weekday() < 5:
            added += 1
    today, late = date.fromisoformat(config.TODAY), 0
    d = expected
    while d < today:
        d += timedelta(days=1)
        if d.weekday() < 5:
            late += 1
    return late


def _cancel(conv: dict, oid: str, text: str, lang: str, rng: model.Dice, trace: dict) -> str:
    order = _own_order(conv, oid, trace)
    if order is None:
        return _not_found(oid, lang)
    if order["status"] != "Processing":
        return (f"La commande {oid} est au statut {order['status']} : elle ne peut plus être annulée. Vous pouvez "
                f"retourner les articles après la livraison." if lang == "fr" else
                f"Order {oid} is {order['status']}, so it can no longer be cancelled. You can return the items after "
                f"delivery.")
    action = {"tool": "cancel_order", "args": {"order_id": oid}}
    if not model.needs_confirmation(text):
        return _do_action(conv, action, None, lang, trace)
    trace["pending_action"] = action
    items = ", ".join(i["name"] for i in order["items"])
    return (f"Voulez-vous que j'annule la commande {oid} ({items}) ? Répondez oui pour confirmer." if lang == "fr"
            else f"Do you want me to cancel order {oid} ({items})? Reply yes to confirm.")


def _refund(conv: dict, oid: str, text: str, lang: str, rng: model.Dice, trace: dict) -> str:
    order = _own_order(conv, oid, trace)
    if order is None:
        return _not_found(oid, lang)
    if order["status"] != "Delivered":
        return (f"La commande {oid} n'est pas encore livrée. Vous pourrez retourner les articles après la livraison."
                if lang == "fr" else
                f"Order {oid} has not been delivered yet. You can return items after delivery.")
    folded = fold(text)
    item = next((i for i in order["items"] if fold(i["sku"]) in folded
                 or any(w in folded for w in terms_of(i["name"]))), None)
    if item is None and len(order["items"]) == 1:
        item = order["items"][0]
    if item is None:
        names = ", ".join(f"{i['name']} ({i['sku']})" for i in order["items"])
        return (f"Quel article voulez-vous retourner ? {names}" if lang == "fr"
                else f"Which item do you want to return? {names}")
    window = tools.return_window(order["delivered"])
    days = (date.fromisoformat(config.TODAY) - date.fromisoformat(order["delivered"])).days
    if days > window:
        return (f"La commande {oid} a été livrée le {order['delivered']}, il y a {days} jours. Le délai de retour "
                f"de {window} jours est terminé." if lang == "fr" else
                f"Order {oid} was delivered on {order['delivered']}, {days} days ago. The {window}-day return "
                f"window has ended.")
    trace["pending_action"] = {"tool": "start_refund", "args": {"order_id": oid, "sku": item["sku"]}}
    return model.refund_offer(order, item, tools.refund_amount(order, item["sku"]), lang, rng)


def terms_of(name: str) -> list[str]:
    return [w for w in corpus.terms(name) if len(w) > 3 and not w[0].isdigit()]


def _do_action(conv: dict, action: dict, turn: int | None, lang: str, trace: dict) -> str:
    args = dict(action["args"], confirmed=True)
    if action["tool"] == "cancel_order":
        result = tools.cancel_order(conv["customer_id"], **args)
    else:
        result = tools.start_refund(conv["customer_id"], conversation_id=conv["id"], **args)
    trace["tool_calls"].append({"name": action["tool"], "args": args, "result": result})
    store.log_action(conv["id"], trace["turn"], action["tool"], args, result)
    if not result["ok"]:
        return result["message"]
    if action["tool"] == "cancel_order":
        return (f"C'est fait : la commande {result['order_id']} est annulée." if lang == "fr"
                else f"Done: order {result['order_id']} is cancelled.")
    return (f"C'est fait : le retour est lancé (remboursement {model.money(result['amount'], 'fr')}). Nous envoyons l'étiquette "
            f"de retour par courriel dans un délai d'un jour ouvrable." if lang == "fr" else
            f"Done: the return is started (refund {result['amount']:.2f} dollars). We email the return label within "
            f"1 business day.")
