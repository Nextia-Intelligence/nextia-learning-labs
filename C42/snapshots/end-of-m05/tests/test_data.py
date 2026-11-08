from larkvision import data as D


def test_manifests(data):
    assert len(D.catalogue(data, "test")) == 24
    assert {r["status"] for r in D.returns(data, "test")} == {"good", "damaged"}
    assert "status" not in D.month(data)[0]  # the month has no labels


def test_checksums_find_a_changed_file(data, tmp_path):
    n, problems = D.check_files(data)
    assert n > 100 and problems == []
