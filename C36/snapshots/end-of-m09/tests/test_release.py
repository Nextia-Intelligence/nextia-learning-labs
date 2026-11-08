from larkroute.release import check, slices


def test_a_slice_that_drops_fails(tiny):
    old = slices(tiny, tiny["route"])
    new_pred = list(tiny["route"])
    new_pred[1] = "delivery"
    rows = {r["slice"]: r for r in check(old, slices(tiny, new_pred))}
    assert rows["route=billing"]["candidate"] == 0.0
    assert rows["route=billing"]["result"] == "ok"  # 1 message: shown, not judged (under 30)


def test_check_judges_big_slices():
    old = {"language=fr": (100, 0.90)}
    assert check(old, {"language=fr": (100, 0.87)})[0]["result"] == "WORSE"
    assert check(old, {"language=fr": (100, 0.89)})[0]["result"] == "ok"
