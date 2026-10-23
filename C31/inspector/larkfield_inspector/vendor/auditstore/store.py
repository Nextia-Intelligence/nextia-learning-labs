"""The audit store: append-only, hash-chained, verifiable.

Each line of the store file is one record:

    {"seq": 12, "prev": "<hash of record 11>", "event": {...}, "hash": "<SHA-256 of seq, prev and the event>"}

Changing, removing or reordering any record breaks the chain from that record on, and `verify()` says
where. Removing the LAST records leaves a valid chain, so the store also writes an anchor (the count and
the last hash) to a second file after every append. In a real system the anchor goes to another system
with other access rights (for example a write-once bucket that the application cannot change).

Customers are pseudonymous in the store: `subject.customer` is an HMAC of the customer ID with a key of
that customer (keys file). A deletion request deletes the customer's key: the events stay (the chain
still verifies), but nobody can link them to the customer again ("crypto-shredding").

The store has no update and no delete: `append()` is the only way in.
"""

import hashlib
import hmac
import json
import os
import secrets
import threading
from contextlib import contextmanager
from pathlib import Path

from .schema import check

GENESIS = "0" * 64


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def record_hash(seq: int, prev: str, event: dict) -> str:
    return hashlib.sha256(str(seq).encode() + b"|" + prev.encode() + b"|" + canonical(event)).hexdigest()


class AuditStore:
    _locks: dict[str, threading.Lock] = {}

    def __init__(self, path: Path, key_seed: str | None = None):
        self.path = Path(path)
        self.key_seed = key_seed   # practice data only: reproducible customer keys
        self.anchor = self.path.with_name(self.path.stem + ".anchor.json")
        self.keys = self.path.with_name(self.path.stem + ".keys.json")
        self.rejected = self.path.with_name(self.path.stem + ".rejected.jsonl")
        self.lock = self._locks.setdefault(str(self.path.resolve()), threading.Lock())

    # ------------------------------------------------------------- customers (pseudonyms)
    def _load_keys(self) -> dict:
        return json.loads(self.keys.read_text()) if self.keys.exists() else {}

    def pseudonym(self, customer_id: str) -> str:
        """The customer's name in the store. Makes the customer's key the first time."""
        with self.lock:
            keys = self._load_keys()
            if customer_id not in keys:
                keys[customer_id] = (hashlib.sha256(f"{self.key_seed}|{customer_id}".encode()).hexdigest()[:32]
                                     if self.key_seed else secrets.token_hex(16))
                self.keys.parent.mkdir(parents=True, exist_ok=True)
                self.keys.write_text(json.dumps(keys, indent=1, sort_keys=True))
            key = keys[customer_id]
        return "cust:" + hmac.new(bytes.fromhex(key), customer_id.encode(), hashlib.sha256).hexdigest()[:16]

    def find_pseudonym(self, customer_id: str) -> str | None:
        key = self._load_keys().get(customer_id)
        if key is None:
            return None
        return "cust:" + hmac.new(bytes.fromhex(key), customer_id.encode(), hashlib.sha256).hexdigest()[:16]

    def forget(self, customer_id: str) -> bool:
        """A deletion request: delete the customer's key. The events stay; the link to the customer is gone."""
        with self.lock:
            keys = self._load_keys()
            if customer_id not in keys:
                return False
            del keys[customer_id]
            self.keys.write_text(json.dumps(keys, indent=1, sort_keys=True))
            return True

    # ------------------------------------------------------------- the chain
    def _tail(self) -> tuple[int, str]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return 0, GENESIS
        with self.path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            back = min(size, 65536)
            f.seek(size - back)
            last = f.read().splitlines()[-1]
        rec = json.loads(last)
        return rec["seq"], rec["hash"]

    def append(self, event: dict) -> dict:
        """The only way in. The customer ID becomes the customer's pseudonym before the event is stored."""
        event = dict(event)
        subject = dict(event.get("subject") or {})
        if subject.get("customer_id"):
            subject["customer"] = self.pseudonym(subject.pop("customer_id"))
        event["subject"] = subject
        check(event)
        with self.lock:
            seq, prev = self._tail()
            rec = {"seq": seq + 1, "prev": prev, "event": event, "hash": record_hash(seq + 1, prev, event)}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self.anchor.write_text(json.dumps({"count": rec["seq"], "head": rec["hash"]}) + "\n")
        return rec

    def reject(self, text: str, reason: str) -> None:
        """An event that does not pass the schema: kept apart (not in the chain), with the reason."""
        with self.lock:
            self.rejected.parent.mkdir(parents=True, exist_ok=True)
            with self.rejected.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"reason": reason, "event": text}, ensure_ascii=False) + "\n")

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def events(self) -> list[dict]:
        return [r["event"] for r in self.records()]

    def verify(self) -> dict:
        """Recompute the chain. {'ok', 'count', 'problems': [...]} — the first problem is where it breaks."""
        problems = []
        prev, n = GENESIS, 0
        lines = self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []
        for i, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"line {i}: not valid JSON")
                break
            n += 1
            if rec.get("seq") != i:
                problems.append(f"line {i}: sequence number {rec.get('seq')} (expected {i}): a record was removed or moved")
                break
            if rec.get("prev") != prev:
                problems.append(f"record {i}: its link to record {i - 1} does not match: an earlier record was changed or removed")
                break
            if record_hash(rec["seq"], rec["prev"], rec["event"]) != rec.get("hash"):
                problems.append(f"record {i}: its content does not match its hash: the record was changed")
                break
            prev = rec["hash"]
        if not problems and self.anchor.exists():
            a = json.loads(self.anchor.read_text())
            if a.get("count") != n or a.get("head") != prev:
                problems.append(f"the store has {n} records, the anchor says {a.get('count')}: records were removed "
                                "at the end or added without the store")
        elif not problems and n:
            problems.append("no anchor file: the end of the chain cannot be checked")
        return {"ok": not problems, "count": n, "head": prev, "problems": problems}


@contextmanager
def opened(path: Path):
    yield AuditStore(path)
