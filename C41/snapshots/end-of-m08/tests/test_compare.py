from larkspeech.compare import Table, align, cer, corpus_scores, important_errors, normalise, wer


def test_wer_by_hand():
    # one substitution, one deletion and one insertion on six reference words
    assert wer("the cat sat on the mat", "the cat sit on mat today") == 0.5
    assert [op for op, _, _ in align("a b c".split(), "a x c d".split())] == ["ok", "sub", "ok", "ins"]


def test_wer_can_be_over_100_percent():
    assert wer("yes", "yes yes yes") == 2.0


def test_cer_counts_characters():
    assert round(cer("seven", "seven"), 3) == 0 and round(cer("abcd", "abed"), 3) == 0.25


def test_normalisation_guide():
    assert normalise("Yes, it's seven four two one five oh.") == "yes it is 742150"
    assert normalise("Um, seventy-four, twenty-one, fifty.") == "742150"
    assert normalise("the fourteenth of March") == normalise("the 14th of march") == "the 14 of march"
    assert normalise("C'est le sept quatre deux, un cinq zéro.", language="fr") == "c est le 742150"
    assert normalise("Hello, World!", "basic") == "hello world"


def test_normalisation_changes_the_score():
    ref, hyp = "It's 742150.", "it is seven four two one five zero"
    assert wer(normalise(ref, "basic"), normalise(hyp, "basic")) > 1
    assert wer(normalise(ref), normalise(hyp)) == 0


def test_important_errors_and_table():
    imp = {"order": ["742150"], "product": ["Grow Hub"], "negation": ["I do not want a refund"]}
    e = important_errors(imp, "my grow hub order seven four two one five one, I do want a refund", "en")
    assert e["order"]["missed"] == 1 and e["product"]["missed"] == 0 and e["negation"]["missed"] == 1
    s = corpus_scores([("a b c d", "a b x d", "en"), ("e f", "e f", "en")])
    assert abs(s["wer"] - 1 / 6) < 1e-9
    t = Table()
    t.add(method="whisper-tiny", setting="phone", slice="all", wer=0.21)
    assert "whisper-tiny" in t.show() and len(t.where(method="whisper-tiny").rows) == 1
