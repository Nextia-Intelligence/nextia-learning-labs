"""The configuration store: versions, and the snapshot a replica gets."""

import copy

import pytest

from estate import configstore


def test_publish_gives_every_replica_the_new_version():
    v = configstore.publish("usr-kwame", "first")
    assert configstore.version_for("a") == configstore.version_for("c") == v
    snap = configstore.snapshot("b")
    assert snap["config_version"] == v and "jwks" in snap and "agents" in snap and "catalog" in snap


def test_a_broken_configuration_is_not_published():
    content = configstore.gather()
    bad = copy.deepcopy(content)
    bad["catalog"]["capabilities"]["fast-small"]["mapping"]["primary"]["deployment"] = "chat-smal"
    with pytest.raises(ValueError) as e:
        configstore.publish("usr-kwame", "typo", content=bad)
    assert "no deployment chat-smal" in str(e.value)
