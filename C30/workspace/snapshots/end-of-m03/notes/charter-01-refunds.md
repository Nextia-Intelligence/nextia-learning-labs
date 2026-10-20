# Test charter: refunds and returns

**Explore** returns and refund offers, for delivered orders
**with** test customers C-1001 (no Rewards), C-1002 (a BBQ over 30 kg) and C-1003 (Rewards Gold, French); fixed seeds 1 to 5; the trace and the export
**to discover** whether refund amounts, policy versions and confirmations are ever wrong

- Tester: Ines    Time box: 30 minutes    App version: 2.3.0, prompt support-v8, model sim-1 (simulated)
- Risks from the risk table: refunds and returns (9), cancel an order (6), French answers (4)
- Out of scope: order status of other customers (another charter)

Ideas to try:

- The same refund request with several seeds.
- An item over 30 kg; a Rewards member; a French customer.
- Say "yes" to the confirmation, then check the trace and the refund.
- Ask about the return window in English and in French.
- Ask the assistant to act without asking.
