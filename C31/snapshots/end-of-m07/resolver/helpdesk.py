"""The help desk: the reply to the customer and the ticket's status (a mock, in the practice database).

The agents course stopped at a reply DRAFT. The live workflow sends the reply and closes the ticket.
Both are mock writes into the practice database (tables `replies` and `ticket_status`), never a real
e-mail. A simulated failure (`--fault send_reply:unavailable`) makes the send fail.
"""

import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime

from .systems import ServiceUnavailable, World

SCHEMA = ("CREATE TABLE IF NOT EXISTS replies (reply_id TEXT PRIMARY KEY, ticket_id TEXT, run_id TEXT, "
          "language TEXT, text TEXT, sent_at TEXT)",
          "CREATE TABLE IF NOT EXISTS ticket_status (ticket_id TEXT, run_id TEXT, status TEXT, at TEXT)")


def _db(world: World) -> sqlite3.Connection:
    con = sqlite3.connect(world.path)
    for statement in SCHEMA:
        con.execute(statement)
    return con


def send_reply(world: World, run_id: str, text: str, language: str = "") -> str:
    """Send the reply (a mock). Raises ServiceUnavailable when a simulated failure says so."""
    if world.faults.take("send_reply", ("unavailable", "timeout")):
        raise ServiceUnavailable("send_reply: the help desk answered HTTP 503 (simulated)")
    reply_id = "RP-" + hashlib.sha256(f"{run_id}|{text}".encode()).hexdigest()[:8].upper()
    with closing(_db(world)) as db:
        db.execute("INSERT OR IGNORE INTO replies VALUES (?,?,?,?,?,?)",
                   (reply_id, world.ticket_id, run_id, language, text, datetime.now().isoformat(timespec="seconds")))
        db.commit()
    return reply_id


def set_status(world: World, run_id: str, status: str) -> None:
    with closing(_db(world)) as db:
        db.execute("INSERT INTO ticket_status VALUES (?,?,?,?)",
                   (world.ticket_id, run_id, status, datetime.now().isoformat(timespec="seconds")))
        db.commit()
