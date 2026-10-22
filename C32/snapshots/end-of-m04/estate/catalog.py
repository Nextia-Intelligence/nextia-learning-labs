"""The capability catalog: apps ask for a capability; the catalog says what it promises and what serves it.

config/catalog.yaml holds, per capability, a CONTRACT (features, quality floor, latency, data classes, price
band) and a MAPPING (the provider and deployment that serve it, with fallbacks). config/models.yaml says what
each deployment can do (from the earlier courses' real calls), config/providers.yaml which data classes each
provider's contract allows. `check()` finds every mapping that breaks its contract; `targets()` is the
gateway's routing: the deployments to try, in order, for one request.
"""

from dataclasses import dataclass, field

import yaml

from estate import paths


def _load(name: str, folder=None) -> dict:
    return yaml.safe_load(((folder or paths.CONFIG) / name).read_text(encoding="utf-8")) or {}


def load_catalog(path=None) -> dict:
    if path:
        return yaml.safe_load(open(path, encoding="utf-8").read())
    return _load("catalog.yaml")


def load_models() -> dict:
    return _load("models.yaml")["models"]


def load_providers() -> dict:
    return _load("providers.yaml")["providers"]


@dataclass(frozen=True)
class Target:
    """One place that can answer: a provider's deployment, with the settings the platform adds."""
    provider: str
    deployment: str
    params: dict = field(default_factory=dict)
    params_if_tools: dict = field(default_factory=dict)
    pinned: bool = False

    def body_for(self, body: dict) -> dict:
        """The request as the provider gets it: the deployment's name, plus the settings it needs.
        The platform adds a setting only when the request does not set it already."""
        out = dict(body, model=self.deployment)
        extra = dict(self.params)
        if body.get("tools"):
            extra.update(self.params_if_tools)
        for k, v in extra.items():
            out.setdefault(k, v)
        return out

    def label(self) -> str:
        return f"{self.provider}/{self.deployment}"


def _target(entry: dict, pinned: bool = False) -> Target:
    return Target(entry["provider"], entry["deployment"], dict(entry.get("params") or {}),
                  dict(entry.get("params_if_tools") or {}), pinned)


def targets(catalog: dict, capability: str, data_class: str = "personal", pin: dict | None = None,
            providers: dict | None = None) -> list[Target]:
    """The deployments to try for a request, in order: the mapping's primary, then its fallbacks; only providers
    whose contract allows the data class. A pin keeps only that deployment (in any region of the mapping)."""
    providers = providers if providers is not None else load_providers()
    cap = catalog["capabilities"].get(capability)
    if not cap or not cap.get("mapping"):
        return []
    entries = [cap["mapping"]["primary"], *(cap["mapping"].get("fallbacks") or [])]
    out = []
    for e in entries:
        p = providers.get(e["provider"])
        if p is None or data_class not in (p.get("data_classes") or []):
            continue
        if pin and e["deployment"] != pin["deployment"]:
            continue
        out.append(_target(e, pinned=bool(pin)))
    return out


def check(catalog: dict | None = None, models: dict | None = None, providers: dict | None = None) -> list[str]:
    """Every way the mappings break their contracts (empty: the catalog is consistent)."""
    catalog = catalog or load_catalog()
    models = models or load_models()
    providers = providers or load_providers()
    problems = []
    for name, cap in catalog["capabilities"].items():
        contract = cap.get("contract") or {}
        want = set(contract.get("features") or [])
        mapping = cap.get("mapping")
        if not mapping:
            continue
        for e in [mapping["primary"], *(mapping.get("fallbacks") or [])]:
            where = f"{name} -> {e['provider']}/{e['deployment']}"
            m = models.get(e["deployment"])
            if e["provider"] not in providers:
                problems.append(f"{where}: no provider {e['provider']} in config/providers.yaml")
            if m is None:
                problems.append(f"{where}: no deployment {e['deployment']} in config/models.yaml")
                continue
            missing = want - set(m["features"])
            if missing:
                problems.append(f"{where}: the contract promises {', '.join(sorted(missing))}, the model does not have it")
            params = dict(e.get("params") or {})
            for feature, needed in (m.get("needs") or {}).items():
                if feature in want:
                    given = {**params, **(e.get("params_if_tools") or {})} if feature == "tools" else params
                    for k, v in needed.items():
                        if given.get(k) != v:
                            problems.append(f"{where}: {feature} on {e['deployment']} needs {k}: {v} in the mapping")
            for k, bad in (m.get("refuses") or {}).items():
                for pv in (params.get(k), (e.get("params_if_tools") or {}).get(k)):
                    if pv in bad:
                        problems.append(f"{where}: {e['deployment']} refuses {k}: {pv}")
            band = contract.get("price_band_usd_per_1m") or {}
            price = m.get("price") or {}
            for side in ("input", "output"):
                if side in band and price.get(side, 0) > band[side]:
                    problems.append(f"{where}: the {side} price {price[side]} is above the contract's band {band[side]}")
            allowed = set(providers.get(e["provider"], {}).get("data_classes") or [])
            for dc in contract.get("data_classes") or []:
                if dc not in allowed:
                    problems.append(f"{where}: {e['provider']}'s contract does not allow {dc} data")
    for alias, cap in (catalog.get("aliases") or {}).items():
        if cap not in catalog["capabilities"]:
            problems.append(f"alias {alias} -> {cap}: no such capability")
    return problems


def card(catalog: dict, name: str, models: dict | None = None) -> str:
    """The catalog card of one capability: its contract and what serves it today (M02's visual, as text)."""
    models = models or load_models()
    cap = catalog["capabilities"][name]
    c = cap["contract"]
    qf = c.get("quality_floor") or {}
    lines = [f"Capability: {name}", f"  purpose:      {c.get('purpose')}",
             f"  features:     {', '.join(c.get('features') or [])}",
             f"  quality:      {qf.get('measure')} >= {qf.get('minimum')} on {qf.get('evaluation')}",
             f"  latency p95:  {c.get('latency_p95_s')} s",
             f"  data classes: {', '.join(c.get('data_classes') or [])}",
             f"  price band:   up to US${c.get('price_band_usd_per_1m', {}).get('input')} in / "
             f"US${c.get('price_band_usd_per_1m', {}).get('output')} out per 1M tokens"]
    m = cap.get("mapping")
    if not m:
        lines.append("  serves today: nothing (planned)")
        return "\n".join(lines)
    p = m["primary"]
    lines.append(f"  serves today: {p['provider']}/{p['deployment']} ({models.get(p['deployment'], {}).get('model_version')})"
                 + (f" + settings {p.get('params')}" if p.get("params") else "")
                 + (f" + with tools {p.get('params_if_tools')}" if p.get("params_if_tools") else ""))
    for f in m.get("fallbacks") or []:
        lines.append(f"  fallback:     {f['provider']}/{f['deployment']}")
    return "\n".join(lines)
