"""`vision inspect`: judge photos of returned items from the command line (the same logic as the service)."""
from pathlib import Path

from PIL import Image

from larkvision.paths import models_dir


def register(sub):
    p = sub.add_parser("inspect", help="judge photos of returned items: pass, check or fail")
    p.add_argument("photos", nargs="+")
    p.add_argument("--review", default="review", help="the review folder")
    p.set_defaults(run=run)


def run(args):
    from larkvision.inspector import Inspector
    from larkvision.privacy import default_finder
    from larkvision.review import judge
    m = models_dir()
    insp, faces = Inspector(m / "inspector"), default_finder(m)
    for p in args.photos:
        r = judge(Image.open(p).convert("RGB"), Path(p).stem, insp, faces, args.review)
        score = "-" if r["score"] is None else f"{r['score']:.3f}"
        print(f"{r['item_id']}: {r['zone']:5s} score {score} confidence {r['confidence']:.2f} "
              f"{r['latency_ms']:.0f} ms" + (f"  -> review: {'; '.join(r['reasons'])}" if r["review"] else ""))
