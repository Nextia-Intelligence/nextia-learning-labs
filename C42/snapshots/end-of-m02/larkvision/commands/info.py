"""`vision info`: what is in the data folder, with licences and the cost table."""
from collections import Counter
from pathlib import Path

from larkvision import data as D
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("info", help="what is in the data folder")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    cat = D.catalogue(d)
    n = Counter(r["split"] for r in cat)
    print(f"Data folder: {d}")
    print(f"Catalogue: {n['train']} train, {n['val']} validation, {n['test']} test photos in "
          f"{len({r['label'] for r in cat})} categories; new studio: {len(D.new_studio(d))} (light changed by code)")
    ret = D.returns(d)
    parts = []
    for s, name in (("train", "train"), ("val", "validation"), ("test", "test")):
        rs = [r for r in ret if r["split"] == s]
        parts.append(f"{len(rs)} {name} ({sum(r['status'] == 'damaged' for r in rs)} damaged)")
    print(f"Returns: {', '.join(parts)}; month: {len(D.month(d))} photos, no labels")
    pal = {s: len(D.pallets(d, s)) if (Path(d) / f"pallets/{s}.json").exists() else 0 for s in ("train", "val", "test")}
    print(f"Pallets: {pal['train']} train, {pal['val']} validation, {pal['test']} test photos (drawn by code)")
    cust = D.read_csv(Path(d) / "customer_photos/manifest.csv")
    print(f"Customer photos: {len(cust)} (simulated from catalogue photos by code)")
    lic = Counter()
    for rows in (cat, ret, D.month(d)):
        for r in rows:
            lic[r["licence"]] += 1
    print("Licences: " + "; ".join(f"{v} photos {k}" for k, v in lic.most_common()) + "; pallets CC0 1.0")
    c = D.costs(d)
    print(f"Costs (assumptions): damaged item sold as new {c['damaged_sold_as_new']:.0f} dollars, good item marked "
          f"damaged {c['good_marked_damaged']:.0f}, a person's check {c['check_by_a_person']:.2f}; "
          f"{c['checks_per_day']} checks a day for {c['returns_per_day']} returns")
    print("The hidden test sets are not here: the course team keeps them.")
