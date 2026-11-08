"""Blur by default: find faces with YuNet (OpenCV Zoo, MIT) and blur them before any copy of a photo is kept."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


class FaceFinder:
    def __init__(self, model_path, threshold=0.6):
        import cv2
        try:  # OpenCV 5 prints a harmless warning about its new graph engine: keep the output clean
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        except AttributeError:
            pass
        self.cv2 = cv2
        self.det = cv2.FaceDetectorYN.create(str(model_path), "", (320, 320), threshold)

    def __call__(self, img):
        a = self.cv2.cvtColor(np.asarray(img.convert("RGB")), self.cv2.COLOR_RGB2BGR)
        self.det.setInputSize((a.shape[1], a.shape[0]))
        _, faces = self.det.detect(a)
        if faces is None:
            return []
        return [[int(v) for v in f[:4]] for f in faces]


def blur(img, boxes, margin=0.3):
    """A copy of the photo with each box (x, y, w, h) and a margin around it blurred beyond recognition."""
    out = img.convert("RGB").copy()
    for x, y, w, h in boxes:
        m = int(margin * max(w, h))
        x0, y0 = max(0, x - m), max(0, y - m)
        x1, y1 = min(out.width, x + w + m), min(out.height, y + h + m)
        if x1 <= x0 or y1 <= y0:
            continue
        region = out.crop((x0, y0, x1, y1))
        small = region.resize((max(1, region.width // 12), max(1, region.height // 12)), Image.BILINEAR)
        out.paste(small.resize(region.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(4)), (x0, y0))
    return out


def default_finder(models):
    p = Path(models) / "faces/face_detection_yunet_2023mar.onnx"
    return FaceFinder(p)
