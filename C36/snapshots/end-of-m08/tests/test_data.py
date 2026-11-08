from larkroute import data


def test_every_file_has_the_right_checksum():
    assert data.check() == []


def test_the_split_and_the_labels():
    m = data.messages()
    assert len(m) == 10000
    assert m["split"].value_counts().to_dict() == {"train": 6000, "validation": 2000, "test": 2000}
    assert set(m["route"]) == set(data.ROUTES)
    assert m["synthetic"].all()


def test_no_message_is_in_two_splits():
    ids = [set(data.messages(s)["message_id"]) for s in ("train", "validation", "test")]
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])


def test_the_launch_month_has_no_labels():
    assert "route" not in data.launch_month().columns
