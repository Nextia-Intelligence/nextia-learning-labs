import json

from doc_extract import documents, pipeline


def test_a_run_writes_one_result_with_versions_and_a_review_decision():
    out = pipeline.run(["D011", "D058"])
    assert [r["doc_id"] for r in out] == ["D011", "D058"]
    ok = json.loads((pipeline.RESULTS / "D011.json").read_text())
    assert ok["versions"] == pipeline.versions()
    assert ok["fields"]["total"]["evidence"]["page"] == 1
    claim = out[1]
    assert claim["fields"]["total"]["evidence"]["page"] == 2  # the receipt is page 2 of the claim


def test_stopped_files_say_why():
    bad = [d.doc_id for d in documents.load() if d.expected_intake in ("corrupt", "password")]
    out = pipeline.run(bad)
    assert all(r["review"]["needed"] and "intake" in r["review"]["reasons"][0] for r in out)


def test_old_results_are_found_and_deleted_data_is_gone():
    pipeline.run(["D011"])
    p = pipeline.RESULTS / "D011.json"
    res = json.loads(p.read_text())
    res["versions"]["pipeline"] = "0.9.0"
    p.write_text(json.dumps(res))
    assert "D011" in pipeline.stale()
    removed = pipeline.delete("D011")
    assert not p.exists() and removed


def test_the_regression_set_is_stored():
    expected = json.loads(pipeline.REGRESSION.read_text())
    assert sorted(expected) == sorted(pipeline.REGRESSION_SET)
