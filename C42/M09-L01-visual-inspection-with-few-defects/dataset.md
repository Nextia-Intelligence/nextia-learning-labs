# Dataset card: VisA circuit boards (pcb1 and pcb4), a fixed sample

Used by: the case study *Visual inspection with few defects* of the course *Vision AI: See, Count and Inspect*, `visual-inspection-with-few-defects.ipynb`

| Field | Value |
|---|---|
| Source | VisA (Visual Anomaly dataset), <https://github.com/amazon-science/spot-diff>; archive <https://amazon-visual-anomaly.s3.us-west-2.amazonaws.com/VisA_20220922.tar> |
| Publisher / creator | Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang and Onkar Dabeer (Amazon) |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (the README's licence section and the archive's file `LICENSE-DATASET`) |
| Attribution text | "VisA dataset by Y. Zou, J. Jeong, L. Pemula, D. Zhang and O. Dabeer (Amazon), CC BY 4.0. Sample resized by Nextia Learning." Paper: Zou et al., *SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection and Segmentation*, ECCV 2022. |
| Version or access date | Archive `VisA_20220922.tar` (the only release) |
| File used | `visa-pcb.zip`, kept next to the notebook: yes (CC BY 4.0 allows sharing the changed photos with attribution) |
| SHA-256 | `visa-pcb.zip`: `54563c3066fb6485e2e2801895f143dd63836f49ea8293db50b7630c0cd8181d`; each source photo's SHA-256 is in `manifest.csv` (`source_sha256`) |
| Size | 1,600 photos (800 per board type) and 220 damage masks, 320 pixels wide, 37 MB |

## What one row means

One row of `visa-pcb/manifest.csv` is one photo of one circuit board, taken from above on a fixed rig. `status` is `good` or `damaged`; for a damaged board, `damage` lists VisA's damage types (`; ` between several) and `mask_file` is the true damage area as a black-and-white picture.

Columns: `item_id` (a short hash of the source file name: it does not show the status), `part` (`pcb1` or `pcb4`, VisA's class names), `split` (`train`, `val`, `test`, `new`, `extra`), `status`, `damage`, `file`, `mask_file`, `source_file` (the path in the VisA archive), `source_width`, `source_height`, `source_mask_pixels` (damage pixels at full size), `source_sha256`.

| Split | Per board type | Use |
|---|---|---|
| train | 200 good + 10 damaged | the supervised classifier learns from both; PatchCore and the baseline from the good photos only |
| val | 100 good + 20 damaged | choose the method and the pass, check and fail lines |
| test | 300 good + 40 damaged | measure once |
| new | 100 good + 10 damaged | the end-to-end run on boards that no step has seen |
| extra | 20 damaged | one experiment: the supervised classifier with 30 damaged photos |

## Why this dataset

Inspection with few defects needs real photos of one product, many good and a few damaged, with damage masks, under a licence that allows reuse. VisA has all of it, under CC BY 4.0. Its circuit boards are a different product from the course's candles (VisA's `candle` class), so the case study is new data. `pcb1` (four damage types: bent, melt, missing, scratch; boards lined up from photo to photo) and `pcb4` (seven types, among them extra, missing or wrongly placed parts; boards less regular) give one easy and one harder case for simple methods.

Alternatives compared (details in the course's research notes): MVTec AD (CC BY-NC-SA 4.0: no commercial use, so not used), MPDD metal parts (CC BY-NC-SA 4.0: not used), KolektorSDD2 (CC BY-NC-SA 4.0: not used), BTAD (CC BY-SA 4.0 by its repository's README; share-alike and only three products: not chosen). Other VisA classes: `capsules` has only one damage type (bubble); the food classes are further from an electronics business.

## Changes we made

- Took two of VisA's twelve classes, `pcb1` and `pcb4`, by streaming the archive (1.8 GB) and keeping only these folders.
- Chose 700 good photos of each board at random (seed `pcb1-0` / `pcb4-0`) and all 100 damaged photos, dealt to the splits above. Damaged photos are sorted by damage type first, so each split gets each type in about the same share. VisA's own splits (`split_csv/`) are not used.
- Resized every photo to 320 pixels wide (the height keeps the shape: 244 for `pcb1`, 260 for `pcb4`), saved as JPEG quality 85 with no metadata; masks resized with nearest neighbour to the same size, saved as black (0) and white (255) PNG.
- Renamed the files to a short hash (`B-xxxxxxxx`). VisA's labels are kept; several types in one photo are written with `; `.

## Limitations and cautions

- **Easier than a real line in one way:** fixed camera, fixed light, one board per photo, centred. A real line has more variation (new batches, dust, another camera).
- **Harder than a real line in another:** one damaged board in 8.5 in the test photos. A real line has far fewer faulty boards, so the costs per 1,000 boards are higher here than on a real line, and the best lines differ.
- 20 damaged validation photos per board are few: one damaged board more or less on the wrong side of a line moves the validation cost by 500 dollars per 1,000 boards. Treat small differences as noise.
- Damage types have few examples each (1–22 per type and split). A per-type result is a hint, not a measurement.
- 320 pixels wide is small: at that size the smallest damage covers about 60 pixels (median 312), and the models see the photo at 224 × 224.
- The photos show no person.
