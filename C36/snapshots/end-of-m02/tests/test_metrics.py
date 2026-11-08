from larkroute import metrics


def test_score_of_a_tiny_example(tiny):
    row = metrics.score("tiny", tiny, ["delivery", "delivery", "review", "needs_person"])
    assert row["accuracy"] == 0.5
    assert row["takeover_recall"] == 0.0
    assert row["needs_person_recall"] == 1.0
    assert row["review_share"] == 0.25
    # billing sent to delivery (urgent: 20 dollars) and one review (1.50 dollars), for 4 messages
    assert row["mistakes_per_1000"] == round((20 + 1.5) / 4 * 1000, 1)
