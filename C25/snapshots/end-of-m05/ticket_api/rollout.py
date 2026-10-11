"""Controlled rollouts: which release does a ticket's work (the MLOps course, Module 5).

The release_state row (python -m ops rollout ...) names the active release, and optionally
a canary release with a share of the tickets, and a shadow release. For each ticket the
worker chooses:

- the canary, for the tickets whose hash falls under the share (the same ticket always gets
  the same choice, so a job delivered twice is done by the same release);
- otherwise the active release.

The shadow release, if any, also triages the ticket, but its result is only saved for
comparison (task triage_shadow): customers and agents never see it.

Without a release_state row the worker uses RELEASE_ID (or ASSISTANT_PROMPT) as before.
"""

import hashlib
import time
from dataclasses import dataclass

from ticket_api import releases

REFRESH_SECONDS = 5.0


@dataclass(frozen=True)
class State:
    active: str
    canary: str | None
    canary_share: float
    shadow: str | None


def bucket(ticket_id: str) -> float:
    """A number in [0, 1) from the ticket ID: stable, and spread evenly."""
    return int(hashlib.sha256(ticket_id.encode()).hexdigest()[:8], 16) / 0x100000000


def choose(state: State, ticket_id: str) -> str:
    if state.canary and bucket(ticket_id) < state.canary_share:
        return state.canary
    return state.active


def read(conn) -> State | None:
    row = conn.execute(
        "SELECT active, canary, canary_share, shadow FROM release_state WHERE id = 1"
    ).fetchone()
    return State(**row) if row else None


class Watcher:
    """Reads release_state at most every REFRESH_SECONDS; keeps the manifests it loaded."""

    def __init__(self, db, clock=time.monotonic):
        self.db, self.clock = db, clock
        self.state: State | None = None
        self.read_at = -1e9
        self._manifests: dict[str, releases.Release] = {}

    def current(self) -> tuple[State | None, bool]:
        """The state, and True if it changed since the last read."""
        if self.clock() - self.read_at < REFRESH_SECONDS:
            return self.state, False
        from ticket_api import telemetry

        with telemetry.quiet(), self.db.connection() as conn:
            new = read(conn)
        self.read_at = self.clock()
        changed = new != self.state
        self.state = new
        return new, changed

    def release(self, release_id: str) -> releases.Release:
        if release_id not in self._manifests:
            self._manifests[release_id] = releases.load(release_id)
        return self._manifests[release_id]
