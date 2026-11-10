from larkfield_search import app, business, facets, suggest


def test_suggest_prefix():
    s = [t for t, _ in suggest.suggest("gar")]
    assert s[0] == "garden hose"
    assert "outdor cushion" not in [t for t, _ in suggest.suggest("out")]
    assert all(t for t, _ in suggest.suggestions())  # no empty suggestion


def test_facets_never_zero():
    f = facets.facets(["LK-10001", "LK-10002", "LK-10005"])
    assert dict(f["product class"])["Furniture Cushions"] == 2
    assert all(n > 0 for _, n in f["price"])
    assert facets.apply(["LK-10001", "LK-10002"], in_stock=True) == ["LK-10001"]
    ids = ["LK-10001", "LK-10002", "LK-10007"]
    for value, n in facets.facets(ids)["colour"]:  # the count and the filter use the same rule
        assert len(facets.apply(ids, colour=value)) == n


def test_business_rules():
    res = [("LK-10001", 3.0), ("LK-10002", 2.0), ("LK-10005", 1.0)]
    assert business.sale_first(res)[0][0] == "LK-10002"
    assert business.stock_last(res)[-1][0] == "LK-10002"
    assert business.explore([("LK-10001", 3), ("LK-10002", 2), ("LK-10005", 1), ("LK-10009", 0.5),
                             ("LK-10008", 0.1)], slot=2)[1][0] == "LK-10008"


def test_fallback_never_empty(monkeypatch):
    from larkfield_search import dense
    res, how = business.fallback("zebra garden")
    assert how == "any word" and res
    monkeypatch.setattr(dense, "encode", lambda text: dense.products()[4])
    res, how = business.fallback("zzzz")
    assert how == "by meaning" and res


def test_page_json():
    j = app.search_json("garden hose", "bm25")
    assert j["results"][0]["product_id"] == "LK-10003" and "price" in j["facets"] and j["note"] == ""
    assert app.search_json("zebra garden", "current+fallback")["note"].startswith("No product has every word")
