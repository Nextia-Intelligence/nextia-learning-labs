"""Embeddings computed by the course team with pinned models (data/embeddings/<model>.npz, one row per photo ID),
so that the commands run in seconds without a model download."""
from pathlib import Path

import numpy as np

MODELS = {"clip": "CLIP ViT-B/32 (OpenCLIP, laion2b_s34b_b79k)", "dinov2": "DINOv2 small",
          "resnet18": "ResNet-18 (timm resnet18.a1_in1k)"}


def load(data, kind):
    z = np.load(Path(data) / f"embeddings/{kind}.npz")
    return {k: z[k].astype(np.float32) for k in z.files}


def matrix(emb, ids):
    X = np.stack([emb[i] for i in ids])
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
