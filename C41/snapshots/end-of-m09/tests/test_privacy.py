import numpy as np

from larkspeech import redact as X


def test_card_numbers_in_text():
    t = "my card is four one one one, one one one one, one one one one, one one one one, thanks"
    assert X.card_numbers(t) == ["4111111111111111"]
    assert "[CARD NUMBER REMOVED]" in X.redact_text(t) and not X.card_numbers(X.redact_text(t))
    assert X.card_numbers("order 742155") == []


def test_beep_the_audio():
    words = [("my", 0.0, 0.2), ("card", 0.2, 0.5)] + [(w, 0.5 + i * 0.3, 0.8 + i * 0.3) for i, w in
                                                       enumerate("4111 1111 1111 1111".split())]
    red, spans = X.redact_words(words)
    assert [w for w, _, _ in red] == ["my", "card", "[CARD NUMBER REMOVED]"] and spans == [(0.5, 1.7)]
    x = np.zeros(16000 * 2, np.float32)
    y = X.beep(x, 16000, spans)
    assert np.abs(y[int(1.0 * 16000)]) > 0 or np.abs(y[int(1.0 * 16000) + 4]) > 0


def test_privacy_check(tmp_path):
    assert X.privacy_check({"a.txt": "order 742155"}) == []
    assert X.privacy_check({"b.txt": "card 4111 1111 1111 1111"}) == [("b.txt", "4111111111111111")]
