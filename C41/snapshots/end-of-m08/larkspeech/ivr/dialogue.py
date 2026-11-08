"""The IVR's dialogue: states, intents, the order number, confirmation, misses and the way to a person.
Pure logic (no audio), so it can be tested with text and keys alone."""
from dataclasses import dataclass, field

from larkspeech.compare import normalise
from larkspeech.ivr.prompts import WELCOME, P, in_groups, say_date
from larkspeech.numbers import find_order_number

INTENT_WORDS = {
    "order_status": ["order status", "where is my order", "track", "tracking", "delivery", "hasn't arrived",
                     "has not arrived", "suivi", "suivre", "où est ma commande", "où est la commande", "livraison"],
    "opening_hours": ["opening hours", "hours", "when are you open", "open", "heures", "ouverture", "ouverts",
                      "ouvert"],
    "start_return": ["return", "send back", "send it back", "retour", "retourner", "renvoyer"],
    "agent": ["person", "agent", "someone", "human", "representative", "quelqu'un", "quelqu un", "personne",
              "agent", "conseiller"],
}
KEY_INTENT = {"1": "order_status", "2": "opening_hours", "3": "start_return", "0": "agent"}
YES = {"yes", "yeah", "yep", "correct", "right", "that's right", "oui", "exact", "exactement", "c'est ça", "ouais"}
NO = {"no", "nope", "wrong", "not", "incorrect", "non", "pas", "faux"}  # checked before YES: "that's not right" is a no


def find_intent(text, language):
    """Keyword rules. The LAST intent the caller names wins ("I want to return... no, track my order")."""
    t = " " + normalise(text, "basic", language) + " "
    best, pos = None, -1
    for intent, words in INTENT_WORDS.items():
        for w in words:
            i = t.rfind(" " + normalise(w, "basic", language) + " ")
            if i > pos:
                best, pos = intent, i
    return best


def yes_no(text, language):
    words = set(normalise(text, "basic", language).split())
    joined = normalise(text, "basic", language)
    if words & NO and not ("c est ça" in joined or "exact" in words):
        return "no"
    if words & {normalise(y, "basic", language) for y in YES} or "c est ça" in joined:
        return "yes"
    return None


@dataclass
class Dialogue:
    orders: dict
    language: str | None = None
    state: str = "language"
    intent: str | None = None
    order: str | None = None
    partial: str = ""
    misses: int = 0
    outcome: str | None = None
    handoff_reason: str | None = None
    log: list = field(default_factory=list)

    # what the IVR listens for now: the number of keys that ends a keypad entry
    @property
    def keys_needed(self):
        return 6 if self.state == "number" else 1

    def start(self):
        return [self._say_text(WELCOME, "welcome")]

    def _say(self, key, **kw):
        lang = self.language or "en"
        text = P[lang][key].format(**kw)
        return self._say_text(text, key)

    def _say_text(self, text, key):
        self.log.append({"state": self.state, "prompt": key, "text": text})
        return {"say": text, "key": key}

    def _transfer(self, reason):
        self.outcome, self.handoff_reason, self.state = "handover", reason, "done"
        return [self._say("handover"), {"transfer": reason}]

    def _end(self, outcome, prompt):
        self.outcome, self.state = outcome, "done"
        return [prompt, {"end": outcome}]

    def _miss(self, kind, retry_key, **kw):
        """A no-input or a no-match: ask again in a different way once, then hand over."""
        self.misses += 1
        self.log.append({"state": self.state, "miss": kind})
        if self.misses >= 2:
            return self._transfer("no_input" if kind == "no_input" else "no_match")
        return [self._say(retry_key, **kw)]

    def _goto(self, state):
        self.state, self.misses, self.partial = state, 0, ""

    def step(self, kind, value=None):
        """kind: speech (value = the recognised text), keys (value = digits), no_input. Returns actions."""
        if self.state == "done":
            return []
        self.log.append({"state": self.state, "event": kind, "value": value})
        if kind == "keys" and value and value[0] == "0" and self.state in ("language", "menu", "number", "confirm"):
            self.intent = self.intent or "agent"
            return self._transfer("caller_asked")
        if kind == "no_input":
            retry = {"language": "language_retry", "menu": "menu_retry", "number": "number_retry",
                     "confirm": "confirm_retry"}[self.state]
            return self._miss("no_input", retry)
        return getattr(self, f"_on_{self.state}")(kind, value)

    def _on_language(self, kind, value):
        lang = None
        if kind == "keys":
            lang = {"1": "en", "2": "fr"}.get(value[:1])
        else:
            t = normalise(value or "", "basic")
            lang = ("fr" if any(w in t for w in ("fran", "french", "fra")) else
                    "en" if any(w in t for w in ("english", "anglais", "engl", "inglish")) else None)
        if not lang:
            return self._miss("no_match", "language_retry")
        self.language = lang
        self._goto("menu")
        return [self._say("menu")]

    def _on_menu(self, kind, value):
        intent = KEY_INTENT.get(value[:1]) if kind == "keys" else find_intent(value or "", self.language)
        if not intent:
            return self._miss("no_match", "menu_retry")
        self.intent = intent
        if intent == "agent":
            return self._transfer("caller_asked")
        if intent == "opening_hours":
            return self._end("hours_given", self._say("hours"))
        self._goto("number")
        return [self._say("number")]

    def _on_number(self, kind, value):
        text = value or ""
        if kind == "speech" and self.partial:
            text = self.partial + " " + text
        number, problem = find_order_number(text if kind == "speech" else (value or ""), self.language)
        if kind == "speech" and problem == "too short" and len(number) >= 2 and not self.partial:
            self.partial = number
            self.log.append({"state": self.state, "partial": number})
            return [self._say("number_rest", digits=in_groups(number))]
        self.partial = ""
        if problem:
            return self._miss("no_match", "number_retry")
        if number not in self.orders:
            return self._miss("no_match", "not_found")
        self.order = number
        self._goto("confirm")
        return [self._say("confirm", digits=in_groups(number))]

    def _on_confirm(self, kind, value):
        answer = {"1": "yes", "2": "no"}.get(value[:1]) if kind == "keys" else yes_no(value or "", self.language)
        if answer is None:
            return self._miss("no_match", "confirm_retry")
        if answer == "no":
            self.order = None
            misses = self.misses + 1
            self._goto("number")
            self.misses = misses
            if misses >= 2:
                return self._transfer("no_match")
            return [self._say("number_retry")]
        o = self.orders[self.order]
        lang = self.language
        if self.intent == "start_return":
            if not o["returnable"]:
                return self._transfer("not_returnable")
            return self._end("return_started", self._say("return_started", product=o["product"]))
        status = P[lang]["status"][o["status"]].format(product=o["product"], date=say_date(o["date"], lang))
        return self._end("status_given", self._say_text(status + " " + P[lang]["goodbye"], "status"))

    def record(self, call_id=None):
        """The call record that the analytics read."""
        heard = [e["value"] for e in self.log if e.get("event") in ("speech", "keys")]
        return {"call_id": call_id, "language": self.language, "intent": self.intent, "order": self.order,
                "outcome": self.outcome or "hangup", "handoff_reason": self.handoff_reason,
                "heard": heard, "prompts": [e["prompt"] for e in self.log if "prompt" in e],
                "misses": sum(1 for e in self.log if "miss" in e)}
