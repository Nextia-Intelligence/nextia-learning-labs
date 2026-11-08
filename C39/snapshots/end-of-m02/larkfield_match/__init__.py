"""larkfield-match: the matching tool of the Entity Resolution and Record Matching course (Larkfield's records)."""

import os

# scikit-learn and LightGBM each bring their own copy of the OpenMP library on macOS. Two copies running many
# threads in one program can crash it, so they run on one thread here. The embedding model sets its own threads.
os.environ.setdefault("OMP_NUM_THREADS", "1")


def torch_first():
    """Load PyTorch (when it is installed) before scikit-learn or LightGBM. On macOS each brings its own OpenMP
    library; when PyTorch's is loaded last, the program can crash. Call this before importing those two."""
    try:
        import torch  # noqa: F401
    except ImportError:
        pass


__version__ = "1.0.0"
