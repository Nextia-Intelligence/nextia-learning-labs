import pandas as pd

from larkroute import costs
from larkroute.cascade import cost, run_cascade


def test_each_message_goes_to_one_step(tiny):
    first = pd.DataFrame({"delivery": [0.95, 0.5, 0.2, 0.1], "billing": [0.05, 0.5, 0.8, 0.9]}, index=tiny.index)
    res = run_cascade(first, ["delivery", "billing", "account", "billing"], [0.9, 0.95, 0.4, 0.99], sure=0.9,
                      second_sure=0.8)
    assert list(res["step"]) == ["first", "second", "person", "first"]
    assert list(res["route"]) == ["delivery", "billing", "review", "billing"]
    c = cost(tiny, res, 0.0, 0.001, costs.load())
    assert c["first"] == 0.5 and c["person"] == 0.25
    assert c["run_per_1000"] == 0.5  # the LLM costs 0.001 dollars for each of the 2 unsure messages in 4
