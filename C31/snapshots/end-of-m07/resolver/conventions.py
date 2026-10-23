"""The names on our telemetry: OpenTelemetry's GenAI conventions (pinned) and Larkfield's own names.

The GenAI semantic conventions are still in "development" status: names can change between versions.
They moved from the main semantic-conventions repository to their own repository
(open-telemetry/semantic-conventions-genai), which has no release yet. This project uses the names of
that repository at one commit (PINNED below). The Python package opentelemetry-semantic-conventions
0.66b1 still has older constants for these names, marked "moved", so we write the names here once
and use only these constants in the code.

Rule for every name on this page: it carries a count, a status, an ID or a name of a model or a tool.
Never the text of a ticket, a prompt, an answer or a tool result (see telemetry.py, CONTENT).
"""

PINNED = {
    "repository": "https://github.com/open-telemetry/semantic-conventions-genai",
    "commit": "9ffc7e00c639be7712e544e3e54331e885dccf84",
    "date": "2026-10-21",
    "status": "development",
    "core_semantic_conventions": "1.44.0",
}
SCHEMA_URL = "https://opentelemetry.io/schemas/1.44.0"

# Operation names (gen_ai.operation.name) and span names
OP_WORKFLOW = "invoke_workflow"      # span name "invoke_workflow {gen_ai.workflow.name}", kind INTERNAL
OP_AGENT = "invoke_agent"            # span name "invoke_agent {gen_ai.agent.name}"
OP_CHAT = "chat"                     # span name "chat {gen_ai.request.model}", kind CLIENT
OP_TOOL = "execute_tool"             # span name "execute_tool {gen_ai.tool.name}", kind INTERNAL

# GenAI attributes (development)
OPERATION = "gen_ai.operation.name"
PROVIDER = "gen_ai.provider.name"
REQUEST_MODEL = "gen_ai.request.model"
RESPONSE_MODEL = "gen_ai.response.model"
REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
FINISH_REASONS = "gen_ai.response.finish_reasons"
INPUT_TOKENS = "gen_ai.usage.input_tokens"
OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
REASONING_TOKENS = "gen_ai.usage.reasoning.output_tokens"
OUTPUT_TYPE = "gen_ai.output.type"
PROMPT_NAME = "gen_ai.prompt.name"
PROMPT_VERSION = "gen_ai.prompt.version"
CONVERSATION_ID = "gen_ai.conversation.id"
AGENT_NAME = "gen_ai.agent.name"
AGENT_ID = "gen_ai.agent.id"
AGENT_VERSION = "gen_ai.agent.version"
WORKFLOW_NAME = "gen_ai.workflow.name"
TOOL_NAME = "gen_ai.tool.name"
TOOL_TYPE = "gen_ai.tool.type"
TOOL_CALL_ID = "gen_ai.tool.call.id"
ERROR_TYPE = "error.type"            # stable, from the main conventions

# GenAI metrics (development)
M_INFERENCE_DURATION = "gen_ai.client.inference.duration"            # histogram, s
M_INPUT_TOKENS = "gen_ai.client.inference.usage.input_tokens"        # counter, {token}
M_OUTPUT_TOKENS = "gen_ai.client.inference.usage.output_tokens"      # counter, {token}
M_AGENT_DURATION = "gen_ai.invoke_agent.duration"                    # histogram, s
M_TOOL_DURATION = "gen_ai.execute_tool.duration"                     # histogram, s
DURATION_BUCKETS = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92]

# Larkfield's own attributes (not part of any convention: our prefix says so)
RUN_ID = "larkfield.run.id"
TICKET_ID = "larkfield.ticket.id"
CUSTOMER_ID = "larkfield.customer.id"      # an ID, never a name or an e-mail address
LANGUAGE = "larkfield.ticket.language"     # en, fr, de: a slice, not the text
VARIANT = "larkfield.design"               # agent, agent_structured, workers, router, fixed
RELEASE = "larkfield.release"
OUTCOME = "larkfield.outcome"              # resolved, handed_to_person, asked_customer, waiting_approval, stopped, failed
PROPOSED = "larkfield.proposal.outcome"    # the model's proposal: resolve, reply_only, ask_customer, hand_to_person
RULE = "larkfield.proposal.rule"
ACTIONS = "larkfield.proposal.actions"     # how many write actions were proposed
STOP_REASON = "larkfield.stop_reason"
STEP = "larkfield.step"
COST = "larkfield.cost.usd"
PRICE_TABLE = "larkfield.price_table"      # the version (date) of the price table that made COST
REPLAYED = "larkfield.replay"              # exact, inexact (a recorded decision replayed for another request) or live
RECORDED_LATENCY = "larkfield.recorded_latency_s"
TOOL_KIND = "larkfield.tool.kind"          # read or write
TOOL_STATUS = "larkfield.tool.status"      # ok, not_found, other_customer, invalid_arguments, service_timeout, ...
ARGS_SHAPE = "larkfield.tool.arguments"    # the names of the arguments, sorted ("order_id"), never the values
ORDER_ID = "larkfield.order.id"
ATTEMPT = "larkfield.attempt"
IDEMPOTENCY_KEY = "larkfield.idempotency_key"
OPERATION_ID = "larkfield.operation.id"    # the operation the write belongs to (the same for every retry)
WRITE_OUTCOME = "larkfield.write.outcome"  # done, repeated, timeout, unavailable, refused
REFUND_AMOUNT = "larkfield.refund.amount"
REFUND_REASON = "larkfield.refund.reason"
SKU = "larkfield.sku"
QUANTITY = "larkfield.quantity"
INJECTION = "larkfield.input.injection"    # the practice data's marker: this result carried an injected instruction
INJECTION_ASK = "larkfield.input.injection_ask"   # what the injected text asked for (a short code)
APPROVAL_ID = "larkfield.approval.id"
APPROVER = "larkfield.approval.approver"   # a person's staff ID (usr-sam), never a name
APPROVER_ROLE = "larkfield.approval.role"
APPROVAL_LIMIT = "larkfield.approval.limit"
APPROVAL_DECISION = "larkfield.approval.decision"
APPROVAL_WAIT = "larkfield.approval.wait_s"
HANDOFF_FROM = "larkfield.handoff.from"
HANDOFF_TO = "larkfield.handoff.to"
HANDOFF_ITEMS = "larkfield.handoff.report_items"
REPLY_STATUS = "larkfield.reply.status"    # sent, failed
GATEWAY_REQUEST_ID = "larkfield.gateway.request_id"
GATEWAY_MODEL = "larkfield.gateway.model"  # the model that actually answered, as the gateway says
MCP_SERVER = "larkfield.mcp.server"

# Larkfield's metrics
M_RUNS = "larkfield.runs"                  # counter: one per finished run (outcome, model, language, release)
M_RUN_COST = "larkfield.run.cost"          # counter, {USD}: cost per model, outcome, language
M_TOOL_CALLS = "larkfield.tool.calls"      # counter: tool, kind, status
M_WRITES = "larkfield.writes"              # counter: tool, outcome
M_APPROVAL_WAIT = "larkfield.approval.wait"   # histogram, s
M_STEPS = "larkfield.run.steps"            # histogram: model calls per run
M_RECONCILES = "larkfield.reconciles"      # counter: checks of an uncertain write (found true/false)
M_STOPS = "larkfield.run.stops"            # counter: runs stopped by a limit (reason)
WAIT_BUCKETS = [60, 300, 900, 1800, 3600, 7200, 14400, 28800, 43200, 86400]
