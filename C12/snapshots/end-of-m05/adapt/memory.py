"""Estimate the memory that training needs, before you start (Module 3).

An ESTIMATE of the fixed part only: the weights, the gradients of what is trained, and the optimizer's
two numbers per trained parameter (AdamW). Activations come on top; they grow with the batch size and the
sequence length, so measure them (Module 4 measures them on the real run).
"""

BYTES = {"float32": 4, "bfloat16": 2, "int8": 1, "int4": 0.5}

METHODS = {
    # name: (bytes per base weight, trains every weight?)
    "full fine-tuning (float32)": ("float32", True),
    "LoRA, base in float32": ("float32", False),
    "LoRA, base in bfloat16": ("bfloat16", False),
    "QLoRA, base in 4 bits": ("int4", False),
}

# Model sizes for the comparison. SmolLM2-135M is counted from its config; the others are round
# sizes of well-known model families (an assumption, not a measurement).
MODELS = {"SmolLM2-135M": 134_515_008, "a 1.7B model": 1.7e9, "a 7B model": 7e9, "a 70B model": 70e9}

BUDGETS = {"laptop 16 GB": 16, "GPU 24 GB": 24, "GPU 80 GB": 80}  # a laptop without a GPU; one GPU

LORA_SHARE = 460_800 / 134_515_008  # LoRA rank 8 on q_proj and v_proj in SmolLM2-135M (0.34%)


def estimate_gb(params: float, method: str, lora_share: float = LORA_SHARE) -> float:
    dtype, full = METHODS[method]
    trained = params if full else params * lora_share
    weights = params * BYTES[dtype]
    grads_and_adam = trained * (4 + 8)  # float32 gradient + two float32 AdamW states
    return (weights + grads_and_adam) / 1e9


def inference_gb(params: float, dtype: str) -> float:
    return params * BYTES[dtype] / 1e9


def table() -> list[tuple[str, str, float]]:
    return [(model, method, estimate_gb(n, method)) for model, n in MODELS.items() for method in METHODS]


def fits(gb: float, budget_gb: float, headroom: float = 0.7) -> bool:
    """True when the estimate uses at most 70% of the budget: activations and the system need the rest."""
    return gb <= budget_gb * headroom
