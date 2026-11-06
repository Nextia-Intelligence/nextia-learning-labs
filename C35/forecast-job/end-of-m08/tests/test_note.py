from forecast_job import note

FACTS = {"week": "2025-03-10", "order_units": 12853, "agent_hours": 385, "order_expected_cost_usd": 32017,
         "top_categories": {"garden-furniture": 3120}}


def test_a_note_with_the_plan_numbers_passes():
    text = ("For the week of 2025-03-10 we order 12,853 units, mostly garden furniture (3,120). "
            "The roster has 385 agent hours. Expected cost of the order: 32,017 dollars.")
    assert note.check_note(text, FACTS) == []


def test_a_made_up_number_is_found():
    text = "We order 12,853 units; sales will grow 15% next month and we need 400 agent hours."
    assert note.check_note(text, FACTS) == ["15%", "400"]


def test_rounding_within_one_percent_is_accepted_but_not_more():
    assert note.check_note("About 12,800 units.", FACTS) == []
    assert note.check_note("About 12,000 units.", FACTS) == ["12,000"]
