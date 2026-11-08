# Dataset card: Open Images V7, windows and cars (a fixed sample for counting)

Used by: the case study *Count and detect in crowded scenes* of the course *Vision AI: See, Count and Inspect*, `count-and-detect-in-crowded-scenes.ipynb`

| Field | Value |
|---|---|
| Source | Open Images Dataset V7, <https://storage.googleapis.com/openimages/web/index.html>; photos from the official bucket `https://open-images-dataset.s3.amazonaws.com/{validation,test}/<ImageID>.jpg` |
| Publisher / creator | Boxes: Google LLC. Photos: the Flickr author of each photo (`author`, `author_url` and `landing_url` in `crowd/manifest.csv`) |
| Licence | Photos: [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/), each photo by its author. Boxes: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), Google LLC. ("The annotations are licensed by Google LLC under CC BY 4.0 license. The images are listed as having a CC BY 2.0 license.", Open Images facts page) |
| Attribution text | "Photos from Open Images V7 by their Flickr authors (listed in manifest.csv), CC BY 2.0; boxes by Google LLC, CC BY 4.0. Sample resized and boxes converted to pixels by Nextia Learning." |
| Version or access date | Open Images V7, validation and test splits; photos downloaded on 2026-11-07 (each photo's SHA-256 in `manifest.csv`, `source_sha256`) |
| File used | `crowd.zip`, kept next to the notebook: yes (CC BY 2.0 and CC BY 4.0 allow sharing the changed copies with attribution) |
| SHA-256 | `crowd.zip`: `0cf4aad01fc379c0e1d7c86eb169b6f5db013503585590f48a8b4e87c24fae68` |
| Size | 198 photos (640 pixels on the long side), 2,153 boxes, 14.5 MB; plus `vlm-counts.jsonl` (112 recorded answers of a hosted model) |

## What one row means

One row of `crowd/manifest.csv` is one photo. `class` says what is counted in it: `window` (windows of buildings) or `car`. `count` is the number of boxes of that class that Open Images' annotators drew: the true count for this case study. `band` is the crowding band by that count: `3-5`, `6-9` or `10+`.

One row of `crowd/boxes.csv` is one box of the photo's class: `x`, `y`, `w`, `h` in pixels of the resized photo, and Open Images' flags `occluded` (partly hidden) and `truncated` (cut by the edge of the photo).

One line of `crowd/vlm-counts.jsonl` is one recorded answer of a hosted vision-language model (Azure `chat-strong`) to the question in `prompt`, for one photo of the validation, test or new split: `answer` (the text), `parsed` (the count read from it), tokens and cost.

| Split | Windows | Cars | Use |
|---|---|---|---|
| train | 39 | 28 | the fine-tuned detector and the density estimate learn from these |
| val | 24 | 19 | choose the score lines, the "send to a person" line and the method |
| test | 36 | 31 | measure once |
| new | 12 | 9 | the end-to-end run on photos no step has seen |

## Why this dataset

Counting in crowded scenes needs real photos where every object has its own box, under a licence that allows reuse. Open Images' validation and test boxes are drawn and checked by people, and every photo has an author and a CC BY 2.0 licence. Windows and cars give two kinds of difficulty: windows are small (median about 23 pixels across at 640 wide) and some facades have more than 100; cars are larger, and COCO (the data that public detectors learn from) has a "car" class but no "window" class.

Alternatives compared (`DATASET-RESEARCH.md` in the course's research notes): SKU-110K, crowded shelves ("solely for academic and non-commercial purposes": not allowed); CARPK and PUCPR+, car parks from a drone ("for academic research purpose only": not allowed); COCO (each photo keeps its own Flickr licence, some non-commercial: a second choice only after filtering).

## Changes we made

- Chose photos from Open Images' validation and test splits with at least 3 boxes of Window or Car, **no group box** of the class (Open Images draws one box around a touching crowd of more than 5: that box has no count), no depiction, rotation 0, and no catalogue photo of the course (`select_sample.py`). A window photo has no vehicle in it (Open Images also boxes car windows).
- **No person:** removed every photo whose image-level labels or boxes show a person or a body part; every photo where a person detector (torchvision Faster R-CNN, COCO, score 0.4 or more) or the YuNet face detector found one on the whole photo or a quarter of it; and 17 more after a look at every photo by eye (a driver, a racing driver, toy cars, a video game picture, a drawing, a screenshot, statues and stained glass with figures). Of 552 candidates, 352 were removed (`people_excluded.csv` gives each reason), and 198 of the other 200 are used. If you still find a person, please tell us.
- Dealt the photos of each class and band to the splits in a fixed order (a hash of the image ID): test 12, val 8, new 4, train 14 per band; the crowded car band has only 15 photos in all (test 7, val 3, new 1, train 4).
- Resized every photo so its long side is 640 pixels (JPEG quality 85, no metadata). Converted the boxes from fractions to pixels. Kept only the boxes of the photo's class (a car photo's window boxes are dropped).
- Renamed the files to a short hash (`O-xxxxxxxx`); the Open Images ID is in `source_id`.

## Limitations and cautions

- **The most crowded real scenes are missing.** A car park full of cars usually has a group box in Open Images, so it cannot be in a counting set. Our crowded car band (10 or more) has only 15 photos and at most 30 cars. Real crowded scenes are harder than this sample.
- **The true counts are people's boxes.** Annotators can miss a far window or split a large window in two. Some counts are surely off by one or two.
- **Small splits.** 36 window and 31 car test photos; 7 crowded car test photos. One photo moves a band's error a lot. Treat small differences as noise.
- **Photographers' photos, not customers' photos.** Flickr photos are framed and sharp. A customer's phone photo of a building can be darker, tilted or partly hidden.
- Some car photos show number plates. They are not used for anything here; do not read or store them.
