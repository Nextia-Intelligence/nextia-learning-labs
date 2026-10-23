"""Cost: tokens times the dated price table, on every model span and run; a capability is priced by its model."""

from obs.model import Telemetry
from resolver import conventions as c
from resolver.__main__ import main
from resolver.usage import PRICES_CHECKED, cost_usd


def test_cost_on_spans_with_the_price_table(telemetry_files, capsys):
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    chats = run.model_spans
    assert all(s.get(c.PRICE_TABLE) == PRICES_CHECKED for s in chats)
    expected = sum(cost_usd("chat-small", s.get(c.INPUT_TOKENS), s.get(c.OUTPUT_TOKENS)) for s in chats)
    assert abs(run.cost - expected) < 1e-9 and abs(run.root.get(c.COST) - expected) < 1e-9


def test_an_unknown_model_has_no_price():
    assert cost_usd("strong-reasoning", 1000, 100) is None
