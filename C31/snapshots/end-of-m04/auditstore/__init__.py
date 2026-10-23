"""Larkfield's audit store: an append-only file of audit events, chained by hashes, with a verifier.

    auditstore/schema.py   the audit event: its fixed fields and the check of every event
    auditstore/store.py    append (the only way in), read, verify; the anchor file; the customer keys
    auditstore/server.py   `python -m auditstore serve`: receives audit events from the Collector (OTLP/HTTP logs)
"""
