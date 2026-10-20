"""The checks that a case can use. Each check returns (passed, message); passed is None when the check could not run."""

import re
import unicodedata

from . import judge

REFUSAL = re.compile(r"(can't|cannot|can not|won't|will not|unable to) (help|assist)|ne peux pas vous aider|"
                     r"je ne peux pas (vous )?aider", re.I)
FR_WORDS = set("je vous votre vos mon ma mes est les des une un le la du pour avec pas quand comment combien "
               "pourquoi quel quelle sont commande remboursement retour livraison bonjour merci peux jours et "
               "sur ce cette nous dans".split())
EN_WORDS = set("i you your my is the a an for with not when how much many why what which are order refund return "
               "delivery hello thanks have can we cancel warranty days do does where and on this it of to in".split())


def language(text: str) -> str:
    words = re.findall(r"[a-zà-ÿ']+", text.lower())
    fr = sum(w in FR_WORDS for w in words) + 2 * len(re.findall(r"[éèêàçùô]", text.lower()))
    en = sum(w in EN_WORDS for w in words)
    return "fr" if fr > en else "en"


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace(" ", " ")
    return s.lower()


def _list(v) -> list:
    return v if isinstance(v, list) else [v]


def _doc(ref: str) -> tuple[str, int | None]:
    doc, _, ver = str(ref).partition("@")
    return doc, int(ver) if ver else None


def _matches(key: str, ref: str) -> bool:
    """key 'returns-policy@4#return-window' matches 'returns-policy' and 'returns-policy@4'."""
    doc, ver = _doc(ref)
    kdoc, _, rest = key.partition("@")
    kver = int(rest.split("#")[0]) if rest else None
    return kdoc == doc and (ver is None or kver == ver)


def run_check(check: dict, run: dict, case, ctx: dict) -> tuple[bool | None, str]:
    name, arg = next(iter(check.items()))
    if run.get("error") and name != "no_error":
        return False, f"{name}: the app failed with an error ({run['error']})"
    reply = run["reply"] or ""
    trace = run["trace"] or {}
    r = _fold(reply)
    if name == "contains":
        missing = [x for x in _list(arg) if _fold(str(x)) not in r]
        return (not missing, f"contains: missing {missing}" if missing else "")
    if name == "contains_any":
        ok = any(_fold(str(x)) in r for x in _list(arg))
        return ok, "" if ok else f"contains_any: none of {_list(arg)}"
    if name == "not_contains":
        found = [x for x in _list(arg) if _fold(str(x)) in r]
        return (not found, f"not_contains: found {found}" if found else "")
    if name == "regex":
        ok = re.search(str(arg), reply, re.I | re.S) is not None
        return ok, "" if ok else f"regex: no match for {arg}"
    if name == "not_regex":
        m = re.search(str(arg), reply, re.I | re.S)
        return m is None, "" if m is None else f"not_regex: matched {m.group(0)!r}"
    if name == "language":
        got = language(reply)
        return got == arg, "" if got == arg else f"language: expected {arg}, the reply is in {got}"
    cited = trace.get("cited") or []
    retrieved = [f"{d['doc_id']}@{d['version']}#x" for d in trace.get("retrieved") or []]
    if name == "cites":
        ok = all(any(_matches(k, ref) for k in cited) for ref in _list(arg))
        return ok, "" if ok else f"cites: expected {arg}, cited {cited or 'nothing'}"
    if name == "not_cites":
        bad = [k for k in cited for ref in _list(arg) if _matches(k, ref)]
        return not bad, "" if not bad else f"not_cites: cited {bad}"
    if name == "retrieved":
        ok = all(any(_matches(k, ref) for k in retrieved) for ref in _list(arg))
        return ok, "" if ok else f"retrieved: {arg} was not retrieved"
    if name == "not_retrieved":
        bad = [ref for ref in _list(arg) if any(_matches(k, ref) for k in retrieved)]
        return not bad, "" if not bad else f"not_retrieved: {bad} was retrieved"
    calls = [c for t in run["traces"] for c in t.get("tool_calls") or []]
    if name in ("tool_called", "tool_not_called"):
        want = arg if isinstance(arg, dict) else {"name": arg}
        hits = [c for c in calls if c["name"] == want["name"]
                and all(str(c["args"].get(k)) == str(v) for k, v in (want.get("args") or {}).items())]
        if name == "tool_called":
            return bool(hits), "" if hits else f"tool_called: {want['name']} was not called"
        return not hits, "" if not hits else f"tool_not_called: {want['name']} was called with {hits[0]['args']}"
    if name == "no_error":
        return run.get("error") is None, "" if run.get("error") is None else f"no_error: {run['error']}"
    if name == "refuses":
        refused = REFUSAL.search(reply) is not None
        return refused == bool(arg), "" if refused == bool(arg) else (
            "refuses: the reply does not refuse" if arg else "refuses: the reply refuses a request it should answer")
    if name == "max_chars":
        return len(reply) <= int(arg), "" if len(reply) <= int(arg) else f"max_chars: {len(reply)} > {arg}"
    if name == "order_status":
        bad = {k: run["orders"].get(k) for k, v in arg.items() if run["orders"].get(k) != v}
        return not bad, "" if not bad else f"order_status: expected {arg}, now {bad}"
    if name == "judge":
        return judge.check(arg, run, case, ctx)
    return False, f"unknown check {name}"
