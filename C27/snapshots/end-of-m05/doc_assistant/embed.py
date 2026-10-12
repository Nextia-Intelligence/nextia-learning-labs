"""Embedding models: turn a text into 384 numbers, so that texts with a similar meaning are close.

- LocalEmbedder: the RAG course's model, intfloat/multilingual-e5-small (MIT licence, 118 million
  parameters, about 470 MB, downloaded once into the Hugging Face cache, ~/.cache/huggingface).
  It runs on the CPU. e5 models expect "query: " before a question and "passage: " before a
  document text. The revision is pinned: another revision gives other vectors.
- HashEmbedder: a stand-in for the tests (no download, no meaning): each word adds 1 to one of
  384 places. Texts that share words are close; synonyms are not.

The index must be searched with the SAME model that built it: vectors of two models are not
comparable, even when they have the same length. Each document records the model that made its
vectors (documents.embedder), and a search reads only the chunks of its own model.
"""

import hashlib
import re
import threading

import numpy as np

DIM = 384
LOCAL_MODEL = "intfloat/multilingual-e5-small"
LOCAL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"   # the model's Hugging Face commit


def normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return (vectors / np.where(norms == 0, 1, norms)).astype(np.float32)


class LocalEmbedder:
    name = f"{LOCAL_MODEL}@{LOCAL_REVISION[:7]}"

    def __init__(self, threads: int = 2):
        self.threads = threads
        self._model = None
        self._lock = threading.Lock()

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                import torch
                from sentence_transformers import SentenceTransformer  # slow import: only when needed

                torch.set_num_threads(self.threads)
                self._model = SentenceTransformer(LOCAL_MODEL, revision=LOCAL_REVISION, device="cpu")
        return self._model

    def _encode(self, texts: list[str]) -> np.ndarray:
        return normalise(self.model.encode(list(texts), batch_size=16, normalize_embeddings=True,
                                                   show_progress_bar=False))

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self._encode(["query: " + t for t in texts])

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return self._encode(["passage: " + t for t in texts])


class HashEmbedder:
    """For the tests only: fast and repeatable, but it does not understand meaning."""

    name = "hash-384"

    def _one(self, text: str) -> np.ndarray:
        v = np.zeros(DIM, dtype=np.float32)
        for w in re.findall(r"\w+", text.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1.0
        return v

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return normalise(np.array([self._one(t) for t in texts]))

    embed_passages = embed_queries


def make_embedder(name: str, threads: int = 2):
    if name == "e5":
        return LocalEmbedder(threads)
    if name == "hash":
        return HashEmbedder()
    raise ValueError(f"Unknown EMBEDDER {name!r}: use e5 (or hash in the tests).")
