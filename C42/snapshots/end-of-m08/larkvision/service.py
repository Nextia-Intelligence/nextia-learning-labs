"""The image service: POST a photo of a returned item, get pass, check or fail with a confidence.

    vision serve                       # http://127.0.0.1:8042
    curl -F "file=@data/returns/test/R-xxxx.jpg" "http://127.0.0.1:8042/inspect?item_id=R-xxxx"
"""
import io
import re

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError

from larkvision.review import judge

ITEM_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def create_app(inspector, find_faces, review_dir="review"):
    app = FastAPI(title="Larkfield returns inspector")

    @app.get("/health")
    def health():
        c = inspector.config
        return {"status": "ok", "model_version": inspector.version, "check_line": c["check_line"],
                "fail_line": c["fail_line"]}

    @app.post("/inspect")
    async def inspect(file: UploadFile = File(...), item_id: str = Query("upload")):
        if not ITEM_ID.match(item_id):
            raise HTTPException(422, "item_id: letters, digits, '-' and '_' only, at most 40")
        raw = await file.read()
        if len(raw) > 10_000_000:
            raise HTTPException(413, "the photo is larger than 10 MB")
        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except (UnidentifiedImageError, OSError):
            raise HTTPException(422, "the file is not a photo that we can read") from None
        return judge(img.convert("RGB"), item_id, inspector, find_faces, review_dir)

    return app


def default_app():
    from larkvision.inspector import Inspector
    from larkvision.paths import models_dir
    from larkvision.privacy import default_finder
    m = models_dir()
    return create_app(Inspector(m / "inspector"), default_finder(m))
