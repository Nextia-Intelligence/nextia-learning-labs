"""The simulated providers, their practice keys and their price lists.

Every key below is a made-up practice key: only this simulator accepts it. The names say whose it is,
as a provider's console would show it next to the key's ID on the bill.
"""

PROVIDERS = {
    "azure": {
        "host": "larkfield-ai.openai.azure.example", "region": "East US 2",
        "deployments": ["chat-small", "chat-strong", "embed-small"], "contract": True,
        "about": "Larkfield's Azure subscription: the region where every earlier course recorded its calls.",
    },
    "azure-canada": {
        "host": "larkfield-ai-ca.openai.azure.example", "region": "Canada East (simulated)",
        "deployments": ["chat-small", "chat-strong", "embed-small"], "contract": True,
        "about": "A second region of the same subscription (simulated): it answers with the same recordings.",
    },
    "local": {
        "host": "gpu-box.larkfield.internal:11434", "region": "Larkfield's own computer",
        "deployments": ["gemma3:4b"], "contract": True, "no_key": True,
        "about": "An open model on Larkfield's own hardware (the agents course recorded it with Ollama).",
    },
    "fernway": {
        "host": "api.fernway.example", "region": "unknown",
        "deployments": ["fernway-swift"], "contract": False,
        "about": "A made-up provider that Larkfield has no contract with (constructed for this course).",
    },
}

# key -> (key ID shown on the bill, providers it works for, account, kind, note)
KEYS = {
    "sim-az-service-team-0001": ("az-key-1", ("azure", "azure-canada"), "Larkfield (Azure)", "shared",
                                 "the service team's key, shared by the triage service and the support workflow"),
    "sim-az-data-team-0002": ("az-key-2", ("azure", "azure-canada"), "Larkfield (Azure)", "shared",
                              "the data team's key (the document assistant)"),
    "sim-az-priya-0003": ("az-key-3", ("azure", "azure-canada"), "Larkfield (Azure)", "personal",
                          "made by Priya for her evaluation runs"),
    "sim-az-gateway-0009": ("az-key-9", ("azure", "azure-canada"), "Larkfield (Azure)", "gateway",
                            "the model gateway's key: only the gateway holds it"),
    "sim-fw-personal-7Q2K9XW4": ("fw-7Q2K", ("fernway",), "a personal Fernway account", "personal",
                                 "a personal key on a provider without a contract"),
}

# deployment -> (input, output) US$ per 1M tokens. Azure: the prices of the course's recordings (prices change:
# check the provider's current price page).
PRICES = {
    "chat-small": (0.10, 0.50),
    "chat-strong": (2.00, 10.00),
    "embed-small": (0.02, 0.0),
    "gemma3:4b": (0.0, 0.0),        # local: no price per token; the hardware is a cost the bill does not show
    "fernway-swift": (0.40, 1.60),  # constructed: the made-up provider's made-up price list
}

PRICE_LABELS = {
    "chat-small": "price (prices change, check the current price page)",
    "chat-strong": "price (prices change, check the current price page)",
    "embed-small": "price (prices change, check the current price page)",
    "gemma3:4b": "assumption: US$0 per token on Larkfield's own hardware (the agents course ran it on a 16 GB "
                 "Apple M4 laptop, 19.8 s median per task); the hardware and power are not counted",
    "fernway-swift": "constructed: a made-up price for a made-up provider",
}


def cost_usd(deployment: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES.get(deployment, (0.0, 0.0))
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000
