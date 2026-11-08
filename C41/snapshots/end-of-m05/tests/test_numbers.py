from larkspeech.numbers import find_order_number, fix_order_numbers, luhn_ok


def test_check_digit():
    assert luhn_ok("742155") and not luhn_ok("742151") and not luhn_ok("472155")


def test_find_order_number():
    assert find_order_number("it's seven four two one five five") == ("742155", None)
    assert find_order_number("seventy-four, twenty-one, fifty-five") == ("742155", None)
    assert find_order_number("seven four two") == ("742", "too short")
    assert find_order_number("seven four two one five one")[1] == "check digit wrong"
    assert find_order_number("c'est sept quatre deux un cinq cinq", "fr") == ("742155", None)


def test_fix_order_numbers():
    assert fix_order_numbers("order seven four two one five five please") == "order 742155 please"
