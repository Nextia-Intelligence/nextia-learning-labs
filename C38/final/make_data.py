"""Make a data folder for the final assignment that the `search` command can read.

Run it in your larkfield-search folder, with the course data in data/ (as in the setup lesson):

    python ../nextia-learning-labs/C38/final/make_data.py
    python ../nextia-learning-labs/C38/final/make_data.py --judgments search-pack/judgments.csv --splits search-pack/splits.csv
    python ../nextia-learning-labs/C38/final/make_data.py --judgments search-pack/judgments.csv --splits search-pack/splits.csv --heldout

It writes a new folder (default final-data/). Your data/ folder does not change. The new folder has:

- the catalogue of the new season: the course's 40,066 products and the 2,000 new products of this folder;
- the course's queries and judgments, with one change: the course's test split is now called "course-test";
- the final queries (N-001 ...). Without --splits, they are all the split "test", with no judgments: use this
  to look at results and to choose what to judge. With --splits, your "dev" queries become the split "test",
  your "heldout" queries the split "heldout", and the queries you did not choose the split "final".
  With --heldout as well, your "heldout" queries become the split "test" (and "dev" the split "dev"):
  this is the one run on your held-out part;
- your judgments (--judgments: columns query_id, product_id and grade, or your_grade; empty grades are skipped);
- the embeddings of every product and query, in the same order as the catalogue and the queries.

Any extra column of your splits file (for example kind or misspelt) is copied to queries.csv, so that
`search eval --by kind` works. Then give the folder to the project:

    macOS / Linux:  export LARKFIELD_DATA=final-data LARKFIELD_OUTPUTS=outputs-final
    PowerShell:     $env:LARKFIELD_DATA = "final-data"; $env:LARKFIELD_OUTPUTS = "outputs-final"

and run `search index` once. Unset the two variables to go back to the course data.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
QUERY_COLUMNS = ["query_id", "query", "language", "split", "source", "base_query_id", "query_class", "qtype",
                 "band", "has_number", "planted", "log_searches"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_judgments(path):
    df = pd.read_csv(path, keep_default_na=False, dtype=str)
    col = "grade" if "grade" in df.columns else "your_grade"
    if col not in df.columns or "query_id" not in df.columns or "product_id" not in df.columns:
        sys.exit(f"{path}: needs the columns query_id, product_id and grade (or your_grade).")
    df = df[df[col].str.strip() != ""]
    df = df.assign(grade=df[col].str.strip())
    bad = df[~df["grade"].isin(["0", "1", "2"])]
    if len(bad):
        sys.exit(f"{path}: grades must be 0, 1 or 2; found {sorted(bad['grade'].unique())[:5]}.")
    dup = df.duplicated(["query_id", "product_id"], keep=False)
    if dup.any():
        sys.exit(f"{path}: {int(dup.sum())} rows judge the same product twice for a query. Keep one grade each.")
    return df[["query_id", "product_id"]].assign(grade=df["grade"].astype(int))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data", help="the course data folder (default data)")
    p.add_argument("--final", default=str(HERE), help="the final assignment's folder (default: this folder)")
    p.add_argument("--out", default="final-data", help="the folder to write (default final-data)")
    p.add_argument("--judgments", help="your judgments: query_id, product_id, grade (or your_grade)")
    p.add_argument("--splits", help="your parts: query_id, part (dev or heldout), and any slice columns")
    p.add_argument("--heldout", action="store_true", help="the one run on your held-out part")
    a = p.parse_args()
    data, final, out = Path(a.data), Path(a.final), Path(a.out)
    if not (data / "catalogue.csv.gz").exists():
        sys.exit(f"No course data in {data}/. Run this in your larkfield-search folder, or use --data.")
    if a.heldout and not (a.splits and a.judgments):
        sys.exit("--heldout needs --splits and --judgments.")
    if out.resolve() in (data.resolve(), final.resolve()):
        sys.exit("--out must be a new folder, not the course data or this folder.")

    # The catalogue and the product embeddings: the course's products, then the new season's.
    cat = pd.read_csv(data / "catalogue.csv.gz", dtype={"title_fr": str}, keep_default_na=False)
    new = pd.read_csv(final / "catalogue_new.csv.gz", dtype={"title_fr": str}, keep_default_na=False)
    if set(cat["product_id"]) & set(new["product_id"]):
        sys.exit("The new products are already in the course catalogue: is --data an older final-data folder?")
    pe = np.load(data / "embeddings" / "products.npy")
    pn = np.load(final / "embeddings" / "products_new.npy")
    if len(pe) != len(cat) or len(pn) != len(new):
        sys.exit("The embeddings do not match the catalogue: download the files again.")

    # The queries: the course's (test renamed course-test) and the final queries.
    q = pd.read_csv(data / "queries.csv", keep_default_na=False, dtype=str)
    q.loc[q["split"] == "test", "split"] = "course-test"
    fq = pd.read_csv(final / "queries.csv", keep_default_na=False, dtype=str)
    fq = fq.assign(split="test", source="final", base_query_id="", query_class="", qtype="", band="tail",
                   has_number=fq["query"].str.contains(r"\d").map(str), planted="False", log_searches="0")
    if a.splits:
        sp = pd.read_csv(a.splits, keep_default_na=False, dtype=str)
        if "query_id" not in sp.columns or "part" not in sp.columns:
            sys.exit(f"{a.splits}: needs the columns query_id and part (dev or heldout).")
        unknown = set(sp["query_id"]) - set(fq["query_id"])
        if unknown:
            sys.exit(f"{a.splits}: these IDs are not final queries: {sorted(unknown)[:5]}")
        if not set(sp["part"]) <= {"dev", "heldout"}:
            sys.exit(f"{a.splits}: part must be dev or heldout.")
        part = dict(zip(sp["query_id"], sp["part"]))
        names = {"dev": "dev", "heldout": "test"} if a.heldout else {"dev": "test", "heldout": "heldout"}
        fq["split"] = [names[part[i]] if i in part else "final" for i in fq["query_id"]]
        for col in sp.columns:
            if col in ("query_id", "part"):
                continue
            if col in QUERY_COLUMNS:
                sys.exit(f"{a.splits}: the column {col} is a course column; give your slice another name.")
            fq[col] = fq["query_id"].map(dict(zip(sp["query_id"], sp[col]))).fillna("")
            q[col] = ""
    allq = pd.concat([q, fq], ignore_index=True).fillna("")
    qe = np.load(data / "embeddings" / "queries.npy")
    qn = np.load(final / "embeddings" / "queries.npy")
    if len(qe) != len(q) or len(qn) != len(fq):
        sys.exit("The query embeddings do not match the queries: download the files again.")

    # The judgments: the course's, and yours for the final queries.
    j = pd.read_csv(data / "judgments.csv.gz")
    mine = read_judgments(a.judgments) if a.judgments else pd.DataFrame(columns=["query_id", "product_id", "grade"])
    if len(mine):
        if not set(mine["query_id"]) <= set(fq["query_id"]):
            sys.exit("Your judgments must be for the final queries (N-...) only.")
        known = set(cat["product_id"]) | set(new["product_id"])
        if not set(mine["product_id"]) <= known:
            sys.exit(f"Unknown product IDs in your judgments: {sorted(set(mine['product_id']) - known)[:5]}")

    if out.exists():
        shutil.rmtree(out)
    (out / "embeddings").mkdir(parents=True)
    pd.concat([cat, new], ignore_index=True).to_csv(out / "catalogue.csv.gz", index=False,
                                                    compression={"method": "gzip", "mtime": 0})
    allq.to_csv(out / "queries.csv", index=False)
    pd.concat([j, mine], ignore_index=True).to_csv(out / "judgments.csv.gz", index=False,
                                                   compression={"method": "gzip", "mtime": 0})
    np.save(out / "embeddings" / "products.npy", np.concatenate([pe, pn]))
    np.save(out / "embeddings" / "queries.npy", np.concatenate([qe, qn]))
    meta = json.loads((data / "embeddings" / "model.json").read_text())
    meta.update({"products": len(cat) + len(new), "queries": len(allq)})
    (out / "embeddings" / "model.json").write_text(json.dumps(meta, indent=1) + "\n")
    for name in ("log", "recorded"):
        shutil.copytree(data / name, out / name)
    for name in ("synonyms.csv", "costs.json", "expected.json", "dataset-card.md"):
        if (data / name).exists():
            shutil.copyfile(data / name, out / name)
    files = sorted(x for x in out.rglob("*") if x.is_file())
    (out / "SHA256SUMS").write_text("".join(f"{sha(x)}  {x.relative_to(out).as_posix()}\n" for x in files))

    counts = allq["split"].value_counts()
    print(f"Wrote {out}/: {len(cat) + len(new):,} products ({len(new):,} new), {len(fq)} final queries, "
          f"{len(mine):,} of your judgments.")
    print("Splits: " + ", ".join(f"{k} {counts[k]}" for k in ["train", "validation", "course-test", "test", "dev",
                                                               "heldout", "final"] if k in counts))
    test = fq[fq["split"] == "test"]
    if not a.judgments:
        print("No judgments yet: search eval prints nan for the final queries until you add yours.")
    elif len(test):
        graded = mine[mine["grade"] > 0].groupby("query_id").size()
        empty = [i for i in test["query_id"] if i not in graded.index]
        if empty:
            print(f"Warning: {len(empty)} test queries have no exact or partial product in your judgments, "
                  f"so they have no NDCG: {', '.join(empty[:8])}")
    if a.heldout:
        print("This is the run on your held-out part. Measure each design once, write the numbers down, and do "
              "not change a design after this.")
    print("Note: search check compares with the course data, so it fails on this folder. Use search info.")


if __name__ == "__main__":
    main()
