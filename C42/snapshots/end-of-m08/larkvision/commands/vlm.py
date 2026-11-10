"""`vision vlm`: check the recorded answers of a vision-language model against labels (no model, no key)."""
import json
from pathlib import Path

from larkvision import data as D
from larkvision.compare import count_scores
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("vlm", help="score recorded vision-language answers")
    p.add_argument("--model", choices=["hosted", "local"], default="hosted")
    p.add_argument("--wrong", type=int, default=5, help="print this many wrong attribute answers")
    p.set_defaults(run=run)


def norm(v):
    return str(v or "").strip().lower().replace(" ", "_").replace("-", "_")


def score(data, model):
    recs = [json.loads(x) for x in (Path(data) / f"recordings/vlm-{model}.jsonl").read_text().splitlines() if x]
    labels = {r["image_id"]: r for r in D.read_csv(Path(data) / "recordings/attribute_labels.csv")}
    out = {"model": recs[0]["model"], "answers": len(recs)}
    for field in ("product_type", "main_colour", "material"):
        ok = n = 0
        wrong = []
        for x in (r for r in recs if r["task"] == "attributes"):
            truth = labels[x["id"]][field].split("|")
            if truth == ["unclear"]:
                continue
            n += 1
            said = norm((x["parsed"] or {}).get(field))
            if said in [norm(t) for t in truth]:
                ok += 1
            else:
                wrong.append((x["id"], field, said, "|".join(truth)))
        out[field] = (ok, n, wrong)
    pal = {im["scene_id"]: im for im in D.pallets(data, "test")}
    cnt = [r for r in recs if r["task"] == "count"]
    out["count"] = count_scores([pal[r["id"]]["count"] for r in cnt],
                                [float((r["parsed"] or {}).get("boxes") or 0) for r in cnt],
                                [pal[r["id"]]["crowding"] for r in cnt])
    ret = {r["item_id"]: r for r in D.returns(data, "test")}
    ins = [r for r in recs if r["task"] == "inspect"]
    said = [((r["parsed"] or {}).get("damaged") is True, ret[r["id"]]["status"] == "damaged") for r in ins]
    out["inspect"] = (sum(s and d for s, d in said), sum(d for _, d in said), sum(s and not d for s, d in said),
                      sum(not d for _, d in said))
    return out


def run(args):
    s = score(data_dir(args.data), args.model)
    print(f"Recorded answers of {s['model']} ({s['answers']} answers, replayed from a file):")
    wrong = []
    for field in ("product_type", "main_colour", "material"):
        ok, n, w = s[field]
        wrong += w
        print(f"  {field:12s} {ok}/{n} right ({ok / n:.0%})")
    c = s["count"]
    print(f"  box count on {sum(v['scenes'] for v in c['by_crowding'].values())} pallet photos: error {c['mae']} boxes "
          f"(bias {c['bias']:+}); " + ", ".join(f"{k} {v['mae']}" for k, v in c["by_crowding"].items()))
    f, nd, fp, ng = s["inspect"]
    print(f"  damaged candles: found {f} of {nd}; called {fp} of {ng} good candles damaged")
    for iid, field, said, truth in wrong[:args.wrong]:
        print(f"  wrong: {iid} {field}: said '{said}', label '{truth}'")
