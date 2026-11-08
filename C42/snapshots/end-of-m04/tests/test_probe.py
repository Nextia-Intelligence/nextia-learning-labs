from test_cli import run

from larkvision import data as D
from larkvision.commands.labels import suspects
from larkvision.commands.probe import probe
from larkvision.embeddings import load


def test_probe_all_and_few(data):
    emb = load(data, "clip")
    train, test = D.catalogue(data, "train"), D.catalogue(data, "test")
    pred, n = probe(emb, train, test)
    assert n == 48 and sum(p == r["label"] for p, r in zip(pred, test)) >= 22
    _, n2 = probe(emb, train, test, per_class=2)
    assert n2 == 16


def test_probe_command(data, workdir, capsys):
    code, out = run(["--data", str(data), "probe", "--embeddings", "dinov2", "--balanced"], capsys)
    assert code == 0 and "all labels, balanced classes, 48 labelled photos" in out


def test_label_check_finds_the_planted_error(data, workdir, capsys):
    found = suspects(load(data, "dinov2"), D.catalogue(data, "train"), folds=3)
    assert found[0][1] == "vase" and found[0][2] == "plant_pot"
    code, out = run(["--data", str(data), "labels", "--score", "--top", "3"], capsys)
    assert "Planted label errors in your top 3: 1 of 1" in out
