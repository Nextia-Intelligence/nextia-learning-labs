"""Acceptance: saved mode serves its first page in under 10 seconds and uses under 300 MB of memory.

The test starts `python -m larkfield_inspector` as its own process, waits for the first page, opens every screen's
API answer for each built-in data set, stops the process and reads its peak memory (resident set size).
"""

import json
import os
import resource
import socket
import subprocess
import sys
import time
import urllib.request

from conftest import ROOT


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_start_time_and_memory():
    port = free_port()
    env = {"PATH": os.environ.get("PATH", ""), "INSPECTOR_NO_BROWSER": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    t0 = time.perf_counter()
    proc = subprocess.Popen([sys.executable, "-m", "larkfield_inspector", "--port", str(port), "--no-browser"],
                            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    first = None
    try:
        while time.perf_counter() - t0 < 20:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as r:
                    if r.status == 200:
                        first = time.perf_counter() - t0
                        break
            except OSError:
                time.sleep(0.05)
        assert first is not None, "no page in 20 s"
        t1 = time.perf_counter()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/runs", timeout=30) as r:
            json.loads(r.read())
        first_data = time.perf_counter() - t0
        for ds in ("week", "healthy-week", "constructed"):
            for path in ("runs", "cost", "cost?bucket=hour") + (("compare",) if ds != "constructed" else ()):
                sep = "&" if "?" in path else "?"
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/{path}{sep}ds={ds}", timeout=30).read()
        for path in ("runs/R-1014-040", "runs/R-1014-040/audit", "runs/R-1014-040/audit.md"):
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/{path}", timeout=30).read()
        all_screens = time.perf_counter() - t1
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_mb = peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024   # bytes on macOS, KB on Linux
    report = (f"first page {first:.2f} s, first runs answer {first_data:.2f} s after start, all data sets "
              f"{all_screens:.2f} s, peak memory (RSS) {peak_mb:.0f} MB")
    print(report)
    (ROOT / "tests" / ".last-measure.txt").write_text(report + "\n")
    assert first < 10
    assert peak_mb < 300
