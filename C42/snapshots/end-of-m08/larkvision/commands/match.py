"""`vision match`: find the catalogue photo of each customer photo with embeddings (recall at k)."""
from pathlib import Path

import numpy as np

from larkvision import data as D
from larkvision.commands.compare import add_row
from larkvision.compare import match_row, recall_at_k
from larkvision.embeddings import MODELS, load, matrix
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("match", help="match customer photos to the catalogue")
    p.add_argument("--embeddings", choices=sorted(MODELS), default="dinov2")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--show", type=int, default=0, help="print the top k for the first N customer photos")
    p.set_defaults(run=run)


def rank(emb, gallery_ids, query_ids, k):
    G, Q = matrix(emb, gallery_ids), matrix(emb, query_ids)
    S = Q @ G.T
    return [[gallery_ids[j] for j in np.argsort(-s, kind="mergesort")[:k]] for s in S], S


def run(args):
    d = data_dir(args.data)
    emb = load(d, args.embeddings)
    gallery = [r["image_id"] for r in D.catalogue(d)]
    q = D.read_csv(Path(d) / "customer_photos/manifest.csv")
    ranked, S = rank(emb, gallery, [r["photo_id"] for r in q], max(args.k, 5))
    truth = [r["catalogue_image_id"] for r in q]
    print(f"{MODELS[args.embeddings]}: {len(q)} customer photos against {len(gallery)} catalogue photos; "
          f"recall at 1 {recall_at_k(ranked, truth, 1):.3f}, at {args.k} {recall_at_k(ranked, truth, args.k):.3f}")
    for r, top in list(zip(q, ranked))[:args.show]:
        mark = ["*" if t == r["catalogue_image_id"] else " " for t in top[:args.k]]
        print(f"  {r['photo_id']} ({r['label']}): " + ", ".join(f"{m}{t}" for m, t in zip(mark, top[:args.k])))
    add_row(match_row(f"{args.embeddings} embeddings", ranked, truth, [r["label"] for r in q], "customer photos", None,
                      None, "see the model card"))
