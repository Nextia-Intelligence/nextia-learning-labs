from larkspeech import agent as A

COSTS = {"call_handled_by_person": 4.0, "wrong_action": 15.0, "ivr_call_compute": 0.002}


def test_budget_streaming_is_shorter():
    t = {"ttft_s": 0.6, "llm_s": 1.5, "tts_first_s": 0.1, "tts_all_s": 0.5, "asr_seconds": 0.3}
    parts, total = A.budget(t, 0.8, True)
    assert abs(total - 1.8) < 1e-9 and list(parts)[0].startswith("end of turn")
    assert A.budget(t, 0.8, False)[1] > total


def test_hybrid_uses_the_agent_only_after_a_no_match():
    ivr = [{"call_id": "a", "outcome": "status_given", "seconds": 30, "wrong_intent": False},
           {"call_id": "b", "outcome": "handover", "handoff_reason": "no_match", "seconds": 40,
            "wrong_intent": False}]
    agent = {"a": {"outcome": "status_given", "seconds": 25, "wrong_action": False, "usd": 0.001},
             "b": {"outcome": "status_given", "seconds": 35, "wrong_action": False, "usd": 0.001}}
    res = A.design_rows(ivr, agent, COSTS)
    assert res["IVR (menu)"]["containment"] == 0.5 and res["hybrid"]["containment"] == 1.0
    assert res["IVR (menu)"]["usd_per_call"] > res["hybrid"]["usd_per_call"]


def test_wrong_actions_cost_money():
    ivr = [{"call_id": "a", "outcome": "status_given", "seconds": 30, "wrong_intent": False}]
    agent = {"a": {"outcome": "return_started", "seconds": 25, "wrong_action": True, "usd": 0.001}}
    res = A.design_rows(ivr, agent, COSTS)
    assert res["voice agent"]["containment"] == 0 and res["voice agent"]["wrong_actions"] == 1


def test_input_budget_counts_recognition_once():
    turns = [{"call_id": "a", "input": 1, "turn": 0, "reply": "", "llm_s": 1.0, "ttft_s": 0.9, "asr_base_s": 0.3,
              "tts_first_s": 0, "tts_all_s": 0},
             {"call_id": "a", "input": 1, "turn": 1, "reply": "Your order shipped.", "llm_s": 1.2, "ttft_s": 0.5,
              "asr_base_s": 0.3, "tts_first_s": 0.1, "tts_all_s": 0.4}]
    (_, parts, total), = A.input_budgets(turns, 0.8, True)
    assert parts["recognition"] == 0.3 and abs(parts["LLM"] - 1.5) < 1e-9 and abs(total - 2.7) < 1e-9
