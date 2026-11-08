"""`vision masks`: measure the damage on the returned candles from their masks, with a tea light for scale."""
from pathlib import Path

import numpy as np
from PIL import Image

from larkvision import data as D
from larkvision.paths import data_dir

TEA_LIGHT_MM = 38.0  # an assumption: a standard tea light is about 38 mm wide


def register(sub):
    p = sub.add_parser("masks", help="damage area from the masks of the damaged returns")
    p.add_argument("--split", choices=["train", "val", "test"], default="test")
    p.add_argument("--diameter-mm", type=float, default=TEA_LIGHT_MM)
    p.set_defaults(run=run)


def candle_diameter_px(path):
    """The median diameter of the four largest bright regions (the candles), in pixels."""
    from scipy import ndimage
    a = np.asarray(Image.open(path).convert("L"), float)
    bright = a > 150
    lab, k = ndimage.label(ndimage.binary_opening(bright, iterations=2))
    sizes = sorted(ndimage.sum(bright, lab, range(1, k + 1)), reverse=True)[:4]
    return float(np.median([2 * np.sqrt(s / np.pi) for s in sizes]))


def damage(data, row, diameter_mm=TEA_LIGHT_MM):
    m = np.asarray(Image.open(Path(data) / row["mask_file"]).convert("L")) > 0
    dpx = candle_diameter_px(Path(data) / row["file"])
    mm_per_px = diameter_mm / dpx
    return {"pixels": int(m.sum()), "share": float(m.mean()), "diameter_px": dpx,
            "mm2": float(m.sum()) * mm_per_px ** 2}


def run(args):
    d = data_dir(args.data)
    rows = [r for r in D.returns(d, args.split) if r["status"] == "damaged"]
    out = [(r, damage(d, r, args.diameter_mm)) for r in rows]
    out.sort(key=lambda x: x[1]["mm2"])
    print(f"{len(out)} damaged {args.split} photos; scale: a tea light is {args.diameter_mm:.0f} mm wide")
    print("  item        pixels  share   mm2   damage")
    for r, m in out:
        print(f"  {r['item_id']}  {m['pixels']:6d}  {m['share']:.4f}  {m['mm2']:5.1f}  {r['damage']}")
    print(f"Median area {np.median([m['mm2'] for _, m in out]):.1f} mm2")
