import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from larkvision.privacy import blur
from larkvision.review import judge
from larkvision.service import create_app


class FakeInspector:
    """Scores a photo by its darkest pixel (a dark spot = damage), with the real inspector's config keys."""
    version = "test"
    config = {"check_line": 0.4, "fail_line": 0.8, "validation_good_scores": [0.1, 0.12, 0.15, 0.2, 0.25] * 4}

    def score(self, img):
        return float(1 - np.asarray(img.convert("L")).min() / 255) if img.width != 333 else 0.6


def no_faces(img):
    return []


def one_face(img):
    return [[10, 10, 30, 30]]


def png(img):
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


def test_pass_check_fail_and_review_folder(tmp_path):
    app = TestClient(create_app(FakeInspector(), no_faces, tmp_path / "review"))
    good = Image.new("RGB", (200, 200), (230, 220, 200))
    r = app.post("/inspect?item_id=R-1", files={"file": ("a.png", png(good))}).json()
    assert r["zone"] == "pass" and not r["review"] and r["confidence"] > 0
    unsure = Image.new("RGB", (333, 200), (230, 220, 200))
    r = app.post("/inspect?item_id=R-2", files={"file": ("a.png", png(unsure))}).json()
    assert r["zone"] == "check" and r["review"] and (tmp_path / "review/today/R-2.jpg").exists()
    bad = good.copy()
    bad.putpixel((5, 5), (0, 0, 0))
    assert app.post("/inspect?item_id=R-3", files={"file": ("a.png", png(bad))}).json()["zone"] == "fail"


def test_fallback_for_a_dark_photo_and_bad_input(tmp_path):
    app = TestClient(create_app(FakeInspector(), no_faces, tmp_path / "review"))
    dark = Image.new("RGB", (200, 200), (5, 5, 5))
    r = app.post("/inspect", files={"file": ("a.png", png(dark))}).json()
    assert r["zone"] == "check" and r["reasons"][0].startswith("fallback: photo too dark")
    assert app.post("/inspect", files={"file": ("a.txt", b"not a photo")}).status_code == 422
    assert app.post("/inspect?item_id=../x", files={"file": ("a.png", png(dark))}).status_code == 422
    assert app.get("/health").json()["model_version"] == "test"


def test_a_face_sends_the_photo_to_review_blurred(tmp_path):
    img = Image.fromarray(np.random.default_rng(0).integers(0, 255, (120, 120, 3), dtype=np.uint8))
    r = judge(img, "R-9", FakeInspector(), one_face, tmp_path / "review", day="2026-03-02")
    assert r["review"] and r["faces"] == 1
    saved = np.asarray(Image.open(tmp_path / "review/2026-03-02/R-9.jpg")).astype(float)
    original = np.asarray(img).astype(float)
    face = (slice(15, 35), slice(15, 35))
    assert saved[face].std() < original[face].std() / 3  # the face region lost its detail


def test_blur_leaves_the_rest_of_the_photo():
    img = Image.fromarray(np.random.default_rng(1).integers(0, 255, (100, 100, 3), dtype=np.uint8))
    out = np.asarray(blur(img, [[0, 0, 10, 10]]))
    assert (out[60:, 60:] == np.asarray(img)[60:, 60:]).all()
