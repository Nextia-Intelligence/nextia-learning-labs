# The document assistant's image: the API, the worker thread, the practice identity provider,
# the scripts and the data pack, and the two local models (downloaded at build time, so the
# container needs no internet when it runs).
FROM python:3.12.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/hf PIP_NO_CACHE_DIR=1
WORKDIR /app

# The CPU build of torch first (the default build on Linux is the much larger CUDA one).
RUN pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN grep -v -E '^(pytest|ruff)==' requirements.txt > requirements-run.txt && pip install -r requirements-run.txt

# The models, pinned to the revisions in doc_assistant/embed.py and rerank.py
COPY doc_assistant/embed.py doc_assistant/rerank.py /tmp/models/
RUN python -c "import sys; sys.path.insert(0, '/tmp/models'); import embed, rerank; \
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer(embed.LOCAL_MODEL, revision=embed.LOCAL_REVISION); \
CrossEncoder(rerank.RERANK_MODEL, revision=rerank.RERANK_REVISION)" && rm -rf /tmp/models

COPY doc_assistant doc_assistant
COPY idp idp
COPY migrations migrations
COPY recordings recordings
COPY scripts scripts
COPY data data
COPY evaluation evaluation
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION} HF_HUB_OFFLINE=1

RUN useradd --create-home --uid 10001 app && mkdir -p traces && chown app traces
USER app
EXPOSE 8000
CMD ["fastapi", "run", "doc_assistant/main.py", "--host", "0.0.0.0", "--port", "8000"]
