"""Find AI use that nobody registered: in provider bills, in the network's egress log, and in code.

    python -m estate discover --bill evidence/azure-bill.csv --egress evidence/egress.csv --scan apps/

Registration is enforced only where there is no way around it. Even with the gateway holding the only
provider keys and the network blocking other egress, AI use outside the gateway is FOUND, not prevented:

- a bill line with a key ID that is not the gateway's (config/provider-keys.yaml) is traffic that did not pass
  the gateway; a key ID that is not in the inventory at all is a key nobody told the platform about;
- an egress line from a machine that is not a gateway replica to a model provider (or to any AI provider's
  host, also ones without a contract) is a direct call;
- a key or a provider address written in code is a call waiting to happen.

AI features inside bought tools (a help desk's reply suggester) appear in none of these: they enter the
inventory through the buying process. The command says so at the end.
"""

import csv
import re
from pathlib import Path

import yaml

from estate import paths

KEY_PATTERNS = [
    ("practice provider key", re.compile(r"\bsim-[a-z]{2}-[A-Za-z0-9-]{6,}")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("API key assignment", re.compile(r"(?i)\b(api[_-]?key|authorization)\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
]
ENDPOINT_PATTERNS = [
    ("model provider address", re.compile(r"https?://[A-Za-z0-9.:-]+/(?:[a-z-]+/)?(?:openai/)?v1\b")),
    ("known AI provider host", re.compile(r"\b(?:api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\."
                                          r"com|[a-z0-9-]+\.openai\.azure\.(?:com|example)|api\.fernway\.example)\b")),
]
AI_HOSTS = re.compile(r"(openai|anthropic|googleapis|fernway|11434)", re.I)


def inventory() -> dict:
    return yaml.safe_load((paths.CONFIG / "provider-keys.yaml").read_text(encoding="utf-8"))


def from_bill(path: Path, inv: dict) -> list[dict]:
    out = []
    keys = inv["keys"]
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            k = keys.get(r["key_id"])
            if k and k["status"] == "gateway":
                continue
            what = ("a key that nobody told the platform about" if k is None else
                    f"{k['purpose']} (owner {k['owner']}): still used, so not every call passes the gateway")
            if r["provider"] not in ("azure", "azure-canada", "local"):
                what = f"a provider without a contract ({r['provider']}); " + what
            out.append({"source": f"bill {path.name}", "evidence": f"{r['month']} {r['provider']} key {r['key_id']} "
                        f"{r['deployment']}: {r['requests']} requests, US${float(r['cost_usd']):.4f}", "finding": what,
                        "key_id": r["key_id"], "provider": r["provider"], "requests": int(r["requests"]),
                        "cost_usd": float(r["cost_usd"])})
    return out


def from_egress(path: Path, inv: dict) -> list[dict]:
    gateways = set(inv.get("gateway_hosts") or [])
    seen: dict[tuple, dict] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["source_host"] in gateways or not AI_HOSTS.search(r["destination"] + r["provider"]):
                continue
            k = (r["source_host"], r["destination"])
            s = seen.setdefault(k, {"source": f"egress {path.name}", "count": 0, "blocked": 0, "first": r["time"],
                                    "last": r["time"], "key_id": r["key_id"]})
            n = int(r.get("requests") or 1)           # a summarised log has a count per line
            s["count"] += n
            s["blocked"] += n if r["status"] == "403" else 0
            s["last"] = r["time"]
    out = []
    for (host, dest), s in sorted(seen.items()):
        out.append({"source": s["source"], "evidence": f"{host} -> {dest}: {s['count']} connections "
                    f"({s['blocked']} blocked) from {s['first'][:16]} to {s['last'][:16]}, key {s['key_id']}",
                    "finding": "a machine that is not the gateway calls a model provider directly",
                    "host": host, "destination": dest, "requests": s["count"]})
    return out


def from_code(folder: Path, allowed: list | None = None) -> list[dict]:
    allowed = allowed if allowed is not None else inventory().get("allowed_addresses") or []
    out = []
    for p in sorted(Path(folder).rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".js", ".ts", ".yaml", ".yml", ".json", ".env", ".sh", ".txt",
                                               ".toml", ".ipynb", ".md") or ".venv" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for name, rx in KEY_PATTERNS + ENDPOINT_PATTERNS:
                m = rx.search(line)
                if m and any(a in m.group(0) for a in allowed):
                    continue                          # the platform's own addresses: the right way to call
                if m:
                    shown = m.group(0)
                    if name != "model provider address" and name != "known AI provider host":
                        shown = shown[:8] + "..."     # never print a whole key
                    out.append({"source": "code", "evidence": f"{p.relative_to(folder.parent) if folder.parent in p.parents else p}:{i}: "
                                f"{name}: {shown}", "finding": f"{name} in code", "file": str(p), "line": i})
    return out


def discover(bills=(), egress=(), scan=()) -> list[dict]:
    inv = inventory()
    findings = []
    for b in bills:
        findings += from_bill(Path(b), inv)
    for e in egress:
        findings += from_egress(Path(e), inv)
    for s in scan:
        findings += from_code(Path(s))
    return findings


def render(findings: list[dict]) -> str:
    lines = []
    for src in ("bill", "egress", "code"):
        part = [f for f in findings if f["source"].startswith(src)]
        if not part:
            continue
        lines.append({"bill": "Provider bills", "egress": "Network egress", "code": "Keys and addresses in code"}[src])
        lines += [f"  - {f['evidence']}\n      {f['finding']}" for f in part]
    lines.append(f"{len(findings)} finding(s).")
    lines.append("Not found by any of these: AI features inside bought tools, and AI used on personal devices "
                 "outside Larkfield's network. They enter the inventory through the buying process and by asking people.")
    return "\n".join(lines)
