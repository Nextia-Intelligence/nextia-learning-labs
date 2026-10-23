"""What each simulated deployment can do, and the real errors it gives when a request asks for more.

The models behind Larkfield's deployments are not interchangeable. The earlier courses recorded real
HTTP 400 answers when a request asked for a feature that a deployment does not have in the Chat Completions
API. The simulator applies these rules BEFORE it looks for a recording, with the recorded error text, so a
request that the real deployment refused is refused here too, even if nobody recorded that exact request.

Each rule names its source. tests/test_provsim.py checks every error body against the recorded one.
"""

from dataclasses import dataclass

SMALL_TOOLS = {
    "error": {
        "message": "Function tools with reasoning_effort are not supported for chat-small in /v1/chat/completions. "
                   "To use function tools, use /v1/responses or set reasoning_effort to 'none'.",
        "type": "invalid_request_error", "param": "reasoning_effort", "code": None}}
STRONG_TOOLS = {
    "error": {
        "message": "Function tools with reasoning_effort are not supported for chat-strong in /v1/chat/completions. "
                   "To use function tools, use /v1/responses or set reasoning_effort to 'none'.",
        "type": "invalid_request_error", "param": "reasoning_effort", "code": None}}
STRONG_NONE = {
    "error": {
        "message": "Unsupported value: 'reasoning_effort' does not support 'none' with this model. Supported values "
                   "are: 'low', 'medium', 'high', and 'xhigh'.",
        "type": "invalid_request_error", "param": "reasoning_effort", "code": "unsupported_value"}}
GEMMA_TOOLS = {
    "error": {"message": "registry.ollama.ai/library/gemma3:4b does not support tools",
              "type": "invalid_request_error", "param": None, "code": None}}


@dataclass(frozen=True)
class Deployment:
    name: str
    model_version: str           # the "model" field of the recorded answers
    endpoint: str                # "chat" or "embeddings"
    tools: str                   # "yes", "only with reasoning_effort none", "no"
    structured_output: bool      # response_format json_schema answered in the recordings
    notes: str


DEPLOYMENTS = {
    "chat-small": Deployment("chat-small", "gpt-6-luna-2026-09-22", "chat", "only with reasoning_effort none", True,
                             "a small reasoning model; reasoning tokens count as output tokens"),
    "chat-strong": Deployment("chat-strong", "gpt-6.1-sol-2026-09-29", "chat", "no", True,
                              "a strong reasoning model; no function tools in Chat Completions"),
    "embed-small": Deployment("embed-small", "text-embedding-3-small", "embeddings", "no", False,
                              "embeddings, 384 dimensions in the recordings"),
    "gemma3:4b": Deployment("gemma3:4b", "gemma3:4b", "chat", "no", True,
                            "an open model run locally with Ollama in the agents course; no tool calling"),
    "fernway-swift": Deployment("fernway-swift", "fernway-swift-1", "chat", "no", False,
                                "a made-up provider's model (constructed): only the digest's request is recorded"),
}

# (rule ID, deployment, test, status, body, source)
RULES = [
    ("chat-strong-no-none", "chat-strong", lambda b: b.get("reasoning_effort") == "none", 400, STRONG_NONE,
     "the LLM applications course (tools_chat_strong.jsonl)"),
    ("chat-strong-no-tools", "chat-strong", lambda b: bool(b.get("tools")), 400, STRONG_TOOLS,
     "the LLM applications course (tools_chat_strong.jsonl)"),
    ("chat-small-tools-need-none", "chat-small",
     lambda b: bool(b.get("tools")) and b.get("reasoning_effort") != "none", 400, SMALL_TOOLS,
     "this course (tools-setting.jsonl)"),
    ("gemma-no-tools", "gemma3:4b", lambda b: bool(b.get("tools")), 400, GEMMA_TOOLS,
     "the LLM applications course, with Ollama (local_extras.jsonl)"),
]


def check(deployment: str, body: dict) -> tuple[str, int, dict, str] | None:
    """The first feature rule that refuses this request: (rule ID, status, body, source), or None."""
    for rule_id, name, test, status, error, source in RULES:
        if name == deployment and test(body):
            return rule_id, status, error, source
    return None
