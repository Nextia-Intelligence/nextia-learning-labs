"""A replica's configuration cache: fresh, stale, expired, and the copy on disk."""

import asyncio

from gateway.config import ConfigCache

SNAP = {"version": "v1.r1", "settings": {"config_cache": {"poll_seconds": 2, "max_stale_seconds": 60}}}


def test_freshness_follows_the_age_of_the_last_good_snapshot():
    now = [0.0]
    c = ConfigCache("a", clock=lambda: now[0])
    assert c.freshness() == "none"
    c.set(SNAP)
    assert c.freshness() == "fresh"
    now[0] = 30
    assert c.freshness() == "stale"
    now[0] = 61
    assert c.freshness() == "expired"


def test_a_failed_poll_keeps_the_last_snapshot():
    async def down():
        raise ConnectionError("the control plane is down")

    c = ConfigCache("a", fetch=down)
    c.set(SNAP)
    assert asyncio.run(c.refresh()) is False
    assert c.snapshot == SNAP and "control plane is down" in c.last_error and c.failures == 1


def test_a_restarted_replica_starts_from_its_copy_on_disk(tmp_path):
    disk = tmp_path / "a-config.json"
    ConfigCache("a", disk=disk).set(SNAP)
    again = ConfigCache("a", disk=disk)
    assert again.snapshot == SNAP and again.freshness() == "expired"       # its age is unknown: be careful
