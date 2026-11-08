"""Where the data and the outputs are.

The data is the course data folder (labs `data/`): set LARKFIELD_DATA, or keep it as `data/`, `../data` or
`../../data` next to the project. Everything the project writes (prepared records, candidate pairs, runs, models,
clusters) goes to `outputs/` (or LARKFIELD_OUTPUTS); `match reset` deletes it.
"""

import os
from pathlib import Path


def data_dir() -> Path:
    if os.environ.get("LARKFIELD_DATA"):
        return Path(os.environ["LARKFIELD_DATA"])
    for cand in (Path("data"), Path("../data"), Path("../../data")):
        if (cand / "sources" / "shop_accounts.csv").exists():
            return cand
    raise SystemExit("No course data found. Put the course data folder next to the project as data/, "
                     "or set LARKFIELD_DATA to its path.")


def outputs_dir() -> Path:
    out = Path(os.environ.get("LARKFIELD_OUTPUTS", "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    return out


def out(*parts) -> Path:
    p = outputs_dir().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
