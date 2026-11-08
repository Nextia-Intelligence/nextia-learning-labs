from test_cli import run

from larkvision import data as D
from larkvision.commands.masks import candle_diameter_px, damage


def test_candle_diameter_and_damage_area(data):
    r = [r for r in D.returns(data, "test") if r["status"] == "damaged"][0]
    assert 55 <= candle_diameter_px(data / r["file"]) <= 65
    m = damage(data, r)
    assert 100 <= m["pixels"] <= 160 and 30 < m["mm2"] < 70


def test_masks_command(data, workdir, capsys):
    code, out = run(["--data", str(data), "masks"], capsys)
    assert code == 0 and "2 damaged test photos" in out
