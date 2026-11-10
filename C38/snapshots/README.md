# The course project at each stage

`larkfield-search` is the project of the course: Larkfield's product search, with the `search` command. Each
folder here is the whole project at one point of the course. Open the folder of the module you are starting,
follow its README, and compare your own work with the next folder when you finish the module.

| Folder | What it is |
|---|---|
| `start` | the setup lesson of Module 1: the data, the comparison helper, Larkfield's search today and BM25 |
| `end-of-m02` | + relevance judgments and paired comparisons with intervals |
| `end-of-m03` | + BM25 per field, `search explain`, the product-code rule |
| `end-of-m04` | + normalising, spelling, synonyms, recorded rewrites, detection |
| `end-of-m05` | + dense and hybrid search |
| `end-of-m06` | + the cross-encoder, learning to rank, clicks |
| `end-of-m07` | + autocomplete, facets, business rules and the search page |
| `end-of-m08` | + latency and cost, interleaving: the course-end project |

Every folder needs Python 3.12 and the course data in `../../data` (it is there in this repository). Each has its
own `requirements.txt`: later stages need more packages (PyTorch from Module 5, LightGBM from Module 6).
