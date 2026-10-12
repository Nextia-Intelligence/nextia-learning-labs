"""Reranking with a cross-encoder (Module 5): read the question and each candidate chunk TOGETHER.

An embedding model reads the question and the chunk separately; a cross-encoder reads both at
once, so it sees that "after 45 days" and "within 30 days" do not fit. It is slower (one model
run per candidate), so it rereads only the best candidates of the first search.

The model is the RAG course's: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (Apache-2.0 on its
model card, about 470 MB, multilingual), pinned to one revision. WordOverlapReranker is a
stand-in for the tests (no download).
"""

import re
import threading

RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANK_REVISION = "1427fd652930e4ba29e8149678df786c240d8825"


class Reranker:
    name = f"{RERANK_MODEL}@{RERANK_REVISION[:7]}"

    def __init__(self, threads: int = 2):
        self.threads = threads
        self._model = None
        self._lock = threading.Lock()

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                import torch
                from sentence_transformers import CrossEncoder

                torch.set_num_threads(self.threads)
                self._model = CrossEncoder(RERANK_MODEL, revision=RERANK_REVISION, device="cpu")
        return self._model

    def scores(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        return [float(s) for s in self.model.predict([(query, t) for t in texts], batch_size=16)]


class WordOverlapReranker:
    """For the tests only: the share of the question's words that the text contains."""

    name = "word-overlap"

    def scores(self, query: str, texts: list[str]) -> list[float]:
        q = set(re.findall(r"\w+", query.lower()))
        return [len(q & set(re.findall(r"\w+", t.lower()))) / (len(q) or 1) for t in texts]


def make_reranker(embedder_name: str, threads: int = 2):
    """The real cross-encoder with the real embedder; the stand-in with the tests' hash embedder."""
    return WordOverlapReranker() if embedder_name == "hash" else Reranker(threads)
