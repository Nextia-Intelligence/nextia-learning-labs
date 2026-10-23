"""The capability catalog: contracts, mappings, and the checks that keep a mapping inside its contract."""

import copy

from estate import catalog


def test_the_catalog_is_consistent():
    assert catalog.check() == []


def test_features_belong_in_the_contract():
    cat = copy.deepcopy(catalog.load_catalog())
    cat["capabilities"]["strong-reasoning"]["contract"]["features"].append("tools")
    problems = catalog.check(cat)
    assert "strong-reasoning -> azure/chat-strong: the contract promises tools, the model does not have it" in problems


def test_a_mapping_must_add_the_setting_that_a_feature_needs():
    cat = copy.deepcopy(catalog.load_catalog())
    del cat["capabilities"]["fast-small"]["mapping"]["primary"]["params_if_tools"]
    assert catalog.check(cat) == ["fast-small -> azure/chat-small: tools on chat-small needs reasoning_effort: none "
                                  "in the mapping"]


def test_a_mapping_must_not_send_a_setting_the_model_refuses():
    cat = copy.deepcopy(catalog.load_catalog())
    cat["capabilities"]["strong-reasoning"]["mapping"]["primary"]["params"] = {"reasoning_effort": "none"}
    assert "strong-reasoning -> azure/chat-strong: chat-strong refuses reasoning_effort: none" in catalog.check(cat)


def test_the_price_band_is_part_of_the_contract():
    cat = copy.deepcopy(catalog.load_catalog())
    cat["capabilities"]["fast-small"]["mapping"]["primary"]["deployment"] = "chat-strong"
    cat["capabilities"]["fast-small"]["mapping"]["primary"].pop("params_if_tools")
    problems = catalog.check(cat)
    assert any("price 2.0 is above the contract's band 0.5" in p for p in problems)


def test_routing_follows_the_mapping_and_the_data_rules():
    cat = catalog.load_catalog()
    assert [t.label() for t in catalog.targets(cat, "fast-small")] == ["azure/chat-small", "azure-canada/chat-small"]
    providers = copy.deepcopy(catalog.load_providers())
    providers["azure"]["data_classes"] = ["public", "internal"]           # say the contract did not cover personal data
    assert [t.label() for t in catalog.targets(cat, "fast-small", "personal", providers=providers)] == \
        ["azure-canada/chat-small"]
    assert catalog.targets(cat, "vision") == []                           # in the catalog, served by nothing yet


def test_a_pin_keeps_one_deployment():
    cat = catalog.load_catalog()
    pin = {"deployment": "chat-strong", "model_version": "gpt-6.1-sol-2026-09-29", "retire_by": "2027-03-31"}
    assert {t.deployment for t in catalog.targets(cat, "strong-reasoning", pin=pin)} == {"chat-strong"}
    moved = copy.deepcopy(cat)                                            # a remap to chat-small: the pin stays
    for e in [moved["capabilities"]["strong-reasoning"]["mapping"]["primary"],
              *moved["capabilities"]["strong-reasoning"]["mapping"]["fallbacks"]]:
        e.update(deployment="chat-small", params={"reasoning_effort": "none"})
    assert [t.label() for t in catalog.targets(moved, "strong-reasoning")] == ["azure/chat-small",
                                                                              "azure-canada/chat-small"]
    pinned = catalog.targets(moved, "strong-reasoning", pin=pin)
    assert [t.label() for t in pinned] == ["azure/chat-strong", "azure-canada/chat-strong"]
    assert pinned[0].body_for({"model": "strong-reasoning", "messages": []}) == {"model": "chat-strong", "messages": []}


def test_the_platform_adds_settings_only_when_needed():
    t = catalog.targets(catalog.load_catalog(), "fast-small")[0]
    assert t.body_for({"model": "fast-small", "messages": []}) == {"model": "chat-small", "messages": []}
    with_tools = t.body_for({"model": "fast-small", "messages": [], "tools": [{}]})
    assert with_tools["reasoning_effort"] == "none" and with_tools["model"] == "chat-small"


def test_the_card_names_what_serves_a_capability_today():
    text = catalog.card(catalog.load_catalog(), "strong-reasoning")
    assert "serves today: azure/chat-strong (gpt-6.1-sol-2026-09-29)" in text
    assert "task_success >= 0.95 on agents course, 70 resolution tasks" in text
