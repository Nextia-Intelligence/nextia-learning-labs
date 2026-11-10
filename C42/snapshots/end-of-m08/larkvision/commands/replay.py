"""`vision replay`: run the inspector over the replayed month of returns photos, day by day, with drift checks."""
import csv
from pathlib import Path

import numpy as np
from PIL import Image

from larkvision import data as D
from larkvision.drift import alarms, business_alarms
from larkvision.paths import data_dir, models_dir, outputs_dir


def register(sub):
    p = sub.add_parser("replay", help="replay a month of returns photos through the inspector")
    p.add_argument("--review", default="review")
    p.add_argument("--limit", type=int, default=0, help="only the first N photos (a quick look)")
    p.set_defaults(run=run)


def week_of(day):
    d = int(day[-2:])
    return "days 01-07" if d <= 7 else "days 08-15" if d <= 15 else "days 16-23" if d <= 23 else "days 24-30"


def replay(data, rows, inspector, find_faces, review_dir, costs):
    from larkvision.review import judge
    results = []
    for r in rows:
        img = Image.open(Path(data) / r["file"]).convert("RGB")
        res = judge(img, r["item_id"], inspector, find_faces, review_dir, day=r["day"])
        results.append({**res, "day": r["day"], "week": week_of(r["day"])})
    budget_share = costs["checks_per_day"] / costs["returns_per_day"]
    ref = inspector.config["validation_good_scores"]
    shares_ref = inspector.config["validation_shares"]
    weeks = {}
    for res in results:
        weeks.setdefault(res["week"], []).append(res)
    summary = []
    for wk in sorted(weeks):
        rs = weeks[wk]
        scores = [r["score"] for r in rs if r["score"] is not None]
        share = sum(r["zone"] == "check" for r in rs) / len(rs)
        p, al = alarms(wk, scores, ref, share, budget_share)
        shares = {z: sum(r["zone"] == z for r in rs) / len(rs) for z in ("fail", "check")}
        cost = business_alarms(shares, shares_ref)
        summary.append({"week": wk, "photos": len(rs), "pass": sum(r["zone"] == "pass" for r in rs),
                        "check": sum(r["zone"] == "check" for r in rs), "fail": sum(r["zone"] == "fail" for r in rs),
                        "faces": sum(r["faces"] > 0 for r in rs), "review": sum(r["review"] for r in rs),
                        "mean_score": round(float(np.mean(scores)), 3) if scores else None, "psi": round(p, 2),
                        "alarms": al, "cost_alarms": cost})
    return results, summary


def run(args):
    from larkvision.inspector import Inspector
    from larkvision.privacy import default_finder
    d = data_dir(args.data)
    m = models_dir()
    rows = D.month(d)
    if args.limit:
        rows = rows[:args.limit]
    insp = Inspector(m / "inspector")
    results, summary = replay(d, rows, insp, default_finder(m), args.review, D.costs(d))
    lat = [r["latency_ms"] for r in results]
    print(f"Replayed {len(results)} photos with model {insp.version} (lines {insp.config['check_line']:.3f} / "
          f"{insp.config['fail_line']:.3f}); latency p50 {np.percentile(lat, 50):.0f} ms, p95 "
          f"{np.percentile(lat, 95):.0f} ms on this CPU")
    print("week        photos  pass  check  fail  faces  review  mean score  PSI")
    for s in summary:
        print(f"{s['week']:10s}  {s['photos']:6d}  {s['pass']:4d}  {s['check']:5d}  {s['fail']:4d}  {s['faces']:5d}  "
              f"{s['review']:6d}  {s['mean_score']:10.3f}  {s['psi']:.2f}")
    for s in summary:
        for a in s["alarms"]:
            print(f"DRIFT ALARM {s['week']}: {a}. Look at the photos in {args.review}/ before you change anything.")
        for a in s["cost_alarms"]:
            print(f"COST ALARM {s['week']}: {a}. Stop the automatic decisions and ask Kwame's team to check by hand.")
    days = {}
    for r in results:
        days.setdefault(r["day"], []).append(r["zone"])
    lvl = insp.config["validation_shares"]
    print(f"Daily share of fail (validation level {lvl['fail']:.0%}) and check ({lvl['check']:.0%}), "
          "about 5 photos a day:")
    print(" ".join(f"{d[-2:]}:{z.count('fail') / len(z):.0%}" for d, z in sorted(days.items())))
    out = outputs_dir() / "replay.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "day", "week", "zone", "score", "confidence", "faces", "review",
                                          "latency_ms"], extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(results)
    print(f"Wrote {out} and {sum(r['review'] for r in results)} photos to {args.review}/ (faces blurred).")
