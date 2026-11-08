"""Run folders: what `sim run` writes and what `xp` reads.

A run folder (runs/<scenario>-s<seed>/) holds the scenario's tables as CSV files, scenario.json (what the run
is) and truth.json (the true effects that the simulator knows). `xp` saves its last result in analysis.json, and
`xp check` compares it with truth.json.
"""

import json
import os
from pathlib import Path

import pandas as pd


def runs_dir() -> Path:
    return Path(os.environ.get("LARKFIELD_RUNS", "runs"))


def save_run(name: str, seed: int, tables: dict, truth: dict, meta: dict) -> Path:
    folder = runs_dir() / f"{name}-s{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for table, df in tables.items():
        fname = f"{table}.csv.gz" if len(df) > 50_000 else f"{table}.csv"
        df.to_csv(folder / fname, index=False, compression={"method": "gzip", "mtime": 0} if fname.endswith(".gz") else None)
        files[table] = {"file": fname, "rows": len(df)}
    meta = {"scenario": name, "seed": seed, **meta, "tables": files,
            "data": "Synthetic: made by the course simulator. There are no real people."}
    (folder / "scenario.json").write_text(json.dumps(meta, indent=2) + "\n")
    (folder / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    (runs_dir() / "LATEST").write_text(folder.name + "\n")
    return folder


class Run:
    def __init__(self, folder: Path):
        self.folder = folder
        self.meta = json.loads((folder / "scenario.json").read_text())

    @property
    def name(self) -> str:
        return self.meta["scenario"]

    def table(self, name: str) -> pd.DataFrame:
        if name not in self.meta["tables"]:
            raise SystemExit(f"The run {self.folder.name} has no table '{name}'. It has: "
                             f"{', '.join(self.meta['tables'])}.")
        return pd.read_csv(self.folder / self.meta["tables"][name]["file"])

    def truth(self) -> dict:
        return json.loads((self.folder / "truth.json").read_text())

    def save_analysis(self, result: dict) -> Path:
        path = self.folder / "analysis.json"
        path.write_text(json.dumps(result, indent=2) + "\n")
        return path

    def analysis(self) -> dict:
        path = self.folder / "analysis.json"
        if not path.exists():
            raise SystemExit(f"No analysis in {self.folder.name} yet. Run an `xp` analysis command first.")
        return json.loads(path.read_text())


def load_run(ref: str | None = None) -> Run:
    """ref: a run folder, a folder name in runs/, a scenario name (its newest run), or None (the last run)."""
    base = runs_dir()
    if ref is None:
        latest = base / "LATEST"
        if not latest.exists():
            raise SystemExit("No run yet. Create one with: sim run --scenario email")
        ref = latest.read_text().strip()
    for cand in (Path(ref), base / ref):
        if (cand / "scenario.json").exists():
            return Run(cand)
    matches = sorted(base.glob(f"{ref}-s*/scenario.json"), key=lambda p: p.stat().st_mtime)
    if matches:
        return Run(matches[-1].parent)
    raise SystemExit(f"No run called '{ref}'. Create it with: sim run --scenario {ref}")
