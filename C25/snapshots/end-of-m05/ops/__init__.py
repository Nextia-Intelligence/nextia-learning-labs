"""ops: read the ticket service's saved telemetry and its operations files (the MLOps course).

    python -m ops --help

It needs only Python's standard library. Every command reads files: saved telemetry (JSON
Lines, .jsonl or .jsonl.gz, as the service writes it with TELEMETRY_FILE) and the files in
operations/ (the inventory, the objectives, the releases). Nothing is sent anywhere.
"""
