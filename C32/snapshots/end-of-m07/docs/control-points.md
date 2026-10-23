# The control points of Larkfield's AI estate

| Control point | What it holds or does | What it sees | What it cannot see |
|---|---|---|---|
| Identity (the control plane's token endpoint) | one identity per agent; short-lived tokens | which agent asks for a token, and when | what the agent does with it |
| Registry | each agent's owner, purpose, risk tier, data classes, capabilities, tools, limits, review date | what each agent is allowed to do | what it really does (that is the gateways' records) |
| Model gateway | every model call: identity, registration, capability, data class, limits, guardrails, routing, usage | the request and the answer of one call, the agent, the cost | the agent's task as a whole, its tool calls, what a person decided |
| Tool gateway | every tool call: allowed tools, reads and writes, arguments, the approval policy | the tool, its arguments, the approval grant | why the model asked for it; the model's reasoning |
| Audit (the registry's events, the usage store) | every change of the estate, every call's record | who changed what, who called what | anything that did not pass the gateways: a direct call, a bought tool's AI |

Outside every control point: AI features inside bought tools (they enter the inventory through the buying
process), and AI used outside Larkfield's network.
