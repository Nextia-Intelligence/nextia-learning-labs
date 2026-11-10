"""larkfield-recs: Larkfield's recommender (the project of the Recommendation and Personalisation course).

One thread for the numeric libraries: the results are the same on every computer, the timings are fair, and the
OpenMP libraries of LightGBM and implicit do not fight on macOS. Set LARKFIELD_THREADS to use more.
"""
import os

_threads = os.environ.get("LARKFIELD_THREADS", "1")
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, _threads)

__version__ = "1.0.0"
