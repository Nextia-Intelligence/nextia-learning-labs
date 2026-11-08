from fastapi.testclient import TestClient

from larkfield_recs import cli, serving
from larkfield_recs.service import create_app


def test_service_falls_back_without_a_model():
    c = TestClient(create_app(serving.Server()))
    assert c.get("/health").json()["fallback_only"] is True
    r = c.get("/recommend/C100002").json()
    assert r["source"] == "fallback" and len(r["products"]) == 10


def test_batch_then_lookup():
    serving.build("item-cf")
    c = TestClient(create_app(serving.Server()))
    r = c.get("/recommend/C100002").json()
    assert r["source"] == "model" and len(r["products"]) == 10
    assert c.get("/recommend/C100008").json()["source"] == "fallback"      # opted out
    assert c.get("/similar/P10001?k=3").status_code == 200


def test_shared_email_never_shows_sensitive_products():
    srv = serving.Server()
    sens = srv.products.sensitive.to_numpy(dtype=bool)
    items, _, _ = srv.recommend("C100001", 10, "email")      # C100001 shares an email address
    assert not sens[items].any()


def test_forget_reaches_the_model(capsys):
    cli.main(["forget", "C100002"])
    out = capsys.readouterr().out
    assert "0 left" in out and "fallback (deleted)" in out
