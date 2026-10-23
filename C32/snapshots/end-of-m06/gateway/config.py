"""The configuration cache of one gateway replica.

The replica asks the control plane for its snapshot every `poll_seconds` and keeps the last good one in
memory and on disk (state/gateway/<replica>-config.json). If the control plane does not answer, the replica
goes on with the snapshot it has. The snapshot's age decides:

    fresh    the last poll worked
    stale    the store has not answered, but for less than max_stale_seconds: everything works as usual
    expired  older than max_stale_seconds: each risk tier's failure mode applies (fail open or fail closed)
    none     the replica has never had a snapshot (not even on disk): it refuses every call

A replica that restarts while the control plane is down starts from its copy on disk.
"""

import asyncio
import json
import time
from pathlib import Path


class ConfigCache:
    def __init__(self, replica: str, fetch=None, disk: Path | None = None, clock=time.monotonic):
        self.replica = replica
        self.fetch = fetch                 # async () -> snapshot dict (raises on failure)
        self.disk = disk
        self.clock = clock
        self.snapshot: dict | None = None
        self.fetched_at: float | None = None
        self.last_error: str = ""
        self.polls = self.failures = 0
        if disk and disk.exists():
            try:
                self.snapshot = json.loads(disk.read_text())
                self.fetched_at = None       # from disk: its age is unknown, so it starts as expired
                self.last_error = "started from the copy on disk"
            except (OSError, json.JSONDecodeError):
                self.snapshot = None

    def settings(self) -> dict:
        return (self.snapshot or {}).get("settings") or {}

    def max_stale(self) -> float:
        return float(self.settings().get("config_cache", {}).get("max_stale_seconds", 60))

    def poll_seconds(self) -> float:
        return float(self.settings().get("config_cache", {}).get("poll_seconds", 2))

    def age(self) -> float | None:
        return None if self.fetched_at is None else self.clock() - self.fetched_at

    def freshness(self) -> str:
        if self.snapshot is None:
            return "none"
        age = self.age()
        if age is None:
            return "expired"
        if age <= self.poll_seconds() * 2 + 1:
            return "fresh"
        return "stale" if age <= self.max_stale() else "expired"

    def set(self, snapshot: dict) -> None:
        self.snapshot = snapshot
        self.fetched_at = self.clock()
        self.last_error = ""
        if self.disk:
            self.disk.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.disk.with_suffix(".tmp")
            tmp.write_text(json.dumps(snapshot))
            tmp.replace(self.disk)

    async def refresh(self) -> bool:
        if self.fetch is None:
            return False
        self.polls += 1
        try:
            self.set(await self.fetch())
            return True
        except Exception as e:  # the store is down, slow or broken: keep the last good snapshot
            self.failures += 1
            self.last_error = f"{type(e).__name__}: {e}"[:200]
            return False

    async def run(self) -> None:
        while True:
            await self.refresh()
            await asyncio.sleep(self.poll_seconds() if self.snapshot else 0.5)
