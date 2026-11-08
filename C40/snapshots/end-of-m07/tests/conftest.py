import pytest

from larkfield_experiments.runs import save_run
from larkfield_experiments.scenarios import all_scenarios


@pytest.fixture(autouse=True)
def runs_in_tmp(tmp_path, monkeypatch):
    """Every test writes its runs in a temporary folder, never in your runs/."""
    monkeypatch.setenv("LARKFIELD_RUNS", str(tmp_path / "runs"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def make_run():
    def make(name, seed=None, customers=None):
        mod = all_scenarios()[name]
        seed = mod.DEFAULT_SEED if seed is None else seed
        tables, truth, meta = mod.run(seed, customers)
        return save_run(mod.NAME, seed, tables, truth, meta)
    return make
