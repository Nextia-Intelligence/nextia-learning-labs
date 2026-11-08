"""Judge one photo and keep a copy for a person when needed (the review folder). Used by the service and the CLI."""
import json
import time
from pathlib import Path

from larkvision.inspector import confidence, photo_problem, zone
from larkvision.privacy import blur


def judge(img, item_id, inspector, find_faces, review_dir="review", day=None):
    """The decision for one returned item. Every saved copy is blurred first; the original is never written."""
    t0 = time.perf_counter()
    cfg = inspector.config
    faces = find_faces(img)
    reasons = []
    problem = photo_problem(img)
    score = None
    if problem:
        z, conf = "check", 0.0
        reasons.append(f"fallback: {problem}")
    else:
        try:
            score = inspector.score(img)
            z = zone(score, cfg["check_line"], cfg["fail_line"])
            conf = confidence(score, cfg["check_line"], cfg["fail_line"])
            if z == "check":
                reasons.append("unsure: the score is between the two lines")
        except Exception as e:  # the model failed: a person decides
            z, conf = "check", 0.0
            reasons.append(f"fallback: model error ({type(e).__name__})")
    if faces:
        reasons.append(f"a person in the photo ({len(faces)} face(s), blurred)")
    result = {"item_id": item_id, "zone": z, "score": None if score is None else round(score, 4),
              "confidence": conf, "faces": len(faces), "review": bool(reasons), "reasons": reasons,
              "model_version": inspector.version, "latency_ms": round(1000 * (time.perf_counter() - t0), 1)}
    if reasons:
        folder = Path(review_dir) / (day or "today")
        folder.mkdir(parents=True, exist_ok=True)
        blur(img, faces).save(folder / f"{item_id}.jpg", quality=90)
        (folder / f"{item_id}.json").write_text(json.dumps(result, indent=1) + "\n")
    return result
