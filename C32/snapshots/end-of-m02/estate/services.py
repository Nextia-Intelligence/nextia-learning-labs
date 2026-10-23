"""Start and stop the estate's services on your computer: python -m estate up / down / status.

    provider simulator   python -m provsim                 8320 (SIM_PORT)
    control plane        python -m estate serve            8321 (ESTATE_PORT)
    gateway front door   python -m gateway.front           8322 (GATEWAY_PORT)
    gateway replicas     python -m gateway --replica a|b|c 8323, 8324, 8325 (REPLICA_PORTS)
    tool gateway         python -m toolgate                8326 (TOOLGATE_PORT; it starts the two MCP servers)

Each service runs as its own process, with its log in state/logs/<name>.log and its process ID in
state/pids.json. `down` stops only the processes that `up` started (their IDs), never anything else.
"""

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

from estate import paths


def ports() -> dict:
    env = os.environ
    a, b, c = (int(x) for x in env.get("REPLICA_PORTS", "8323,8324,8325").split(","))
    return {"provsim": int(env.get("SIM_PORT", 8320)), "control": int(env.get("ESTATE_PORT", 8321)),
            "front": int(env.get("GATEWAY_PORT", 8322)), "replica-a": a, "replica-b": b, "replica-c": c,
            "toolgate": int(env.get("TOOLGATE_PORT", 8326))}


def _have(package: str) -> bool:
    """The estate starts what the project has: the course adds the services module by module."""
    try:
        return importlib.util.find_spec(package) is not None
    except ModuleNotFoundError:          # its parent package is not there either
        return False


def services(replicas=("a", "b", "c"), tools: bool = True) -> list[tuple[str, list[str], str]]:
    p = ports()
    py = sys.executable
    out = [("provsim", [py, "-m", "provsim", "--port", str(p["provsim"])], f"http://127.0.0.1:{p['provsim']}/health")]
    if _have("estate.server"):
        out.append(("control", [py, "-m", "estate", "serve", "--port", str(p["control"])],
                    f"http://127.0.0.1:{p['control']}/health"))
    if _have("gateway"):
        if _have("gateway.front"):
            for r in replicas:
                out.append((f"replica-{r}", [py, "-m", "gateway", "--replica", r, "--port", str(p[f"replica-{r}"])],
                            f"http://127.0.0.1:{p[f'replica-{r}']}/ready"))
        else:   # one gateway, at the address that the front door takes later: the apps' URL never changes
            out.append(("gateway", [py, "-m", "gateway", "--replica", "a", "--port", str(p["front"])],
                        f"http://127.0.0.1:{p['front']}/ready"))
    if _have("gateway.front"):
        out.append(("front", [py, "-m", "gateway.front", "--port", str(p["front"])],
                    f"http://127.0.0.1:{p['front']}/front/status"))
    if tools and _have("toolgate"):
        out.append(("toolgate", [py, "-m", "toolgate", "--port", str(p["toolgate"])],
                    f"http://127.0.0.1:{p['toolgate']}/ready"))
    return out


def env_for() -> dict:
    p = ports()
    replicas = ",".join(f"{r}=http://127.0.0.1:{p[f'replica-{r}']}" for r in ("a", "b", "c"))
    return {**os.environ, "PROVSIM_URL": f"http://127.0.0.1:{p['provsim']}",
            "ESTATE_URL": f"http://127.0.0.1:{p['control']}", "GATEWAY_REPLICAS": replicas,
            "ESTATE_STATE": str(paths.state()), "PYTHONUNBUFFERED": "1"}


def alive(pid: int) -> bool:
    """Whether a process still runs (a stopped child of this process is reaped, so it does not look alive)."""
    try:
        done, _ = os.waitpid(pid, os.WNOHANG)
        if done == pid:
            return False
    except (ChildProcessError, OSError, AttributeError):
        pass
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _pids_file():
    return paths.state() / "pids.json"


def running() -> dict:
    f = _pids_file()
    pids = json.loads(f.read_text()) if f.exists() else {}
    found = {}
    for name, pid in pids.items():
        if alive(pid):
            found[name] = pid
    return found


def _host_port(url: str) -> tuple[str, int]:
    host, port = url.split("//", 1)[1].split("/", 1)[0].rsplit(":", 1)
    return host, int(port)


def port_in_use(url: str) -> bool:
    """Whether some program already listens at the service's address (another estate, or a simulator)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(_host_port(url)) == 0


def wait_ok(url: str, seconds: float = 20.0, proc: subprocess.Popen | None = None) -> bool:
    """Whether the service answers; False at once if the process we started has stopped (it could not start)."""
    end = time.time() + seconds
    while time.time() < end:
        if proc is not None and proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(0.2)
    return False


def up(only: list[str] | None = None, replicas=("a", "b", "c"), tools: bool = True) -> list[str]:
    logs = paths.state() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    pids = running()
    lines = []
    for name, cmd, health in services(replicas, tools):
        if only and name not in only:
            continue
        if name in pids:
            lines.append(f"{name:<10} already running (process {pids[name]})")
            continue
        # Another program on the port would answer the health check for us: then the answer is not ours.
        taken = port_in_use(health)
        log = open(logs / f"{name}.log", "a", encoding="utf-8")
        proc = subprocess.Popen(cmd, cwd=paths.PROJECT, env=env_for(), stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        pids[name] = proc.pid
        _pids_file().write_text(json.dumps(pids, indent=1))
        if taken:      # our process cannot bind the port: wait until it stops, so its error is in the log
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
            ok = False
        else:
            ok = wait_ok(health, 30 if name == "toolgate" else 20, proc)
        url = health.rsplit("/", 1)[0]
        hint = f" - port {_host_port(health)[1]} was already in use" if taken else ""
        lines.append(f"{name:<10} {'up' if ok else 'NOT ANSWERING'} (process {proc.pid}) {url}{hint}")
    return lines


def down(only: list[str] | None = None) -> list[str]:
    pids = running()
    lines = []
    for name, pid in list(pids.items()):
        if only and name not in only:
            continue
        try:
            if hasattr(os, "killpg"):
                os.killpg(pid, signal.SIGTERM)   # its own process group: the tool gateway's MCP servers stop too
            else:                                # Windows: no process groups here (not tested by the course)
                os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(100):                     # wait until it has really stopped (at most 10 s)
            if not alive(pid):
                break
            time.sleep(0.1)
        lines.append(f"{name:<10} stopped (process {pid})")
        pids.pop(name)
    left = {k: v for k, v in running().items() if k in pids}
    _pids_file().write_text(json.dumps(left, indent=1))
    return lines


def status() -> list[str]:
    pids = running()
    lines = []
    for name, cmd, health in services():
        state = "running" if name in pids else "stopped"
        detail = ""
        if name in pids:
            try:
                with urllib.request.urlopen(health, timeout=1) as r:
                    detail = r.read().decode()[:160]
            except OSError as e:
                detail = f"not answering ({e})"
        lines.append(f"{name:<10} {state:<8} {detail}")
    return lines
