# Final assignment: a second warehouse and a new category

Larkfield opens a second returns warehouse. Its camera is not the camera of the first warehouse. At the same time, Omar adds a new product category: kettles and teapots. Hamid asks you for a vision pack for returns inspection and catalogue matching, before the second warehouse starts to work.

## What you get

| Folder or file | What |
|---|---|
| `data/returns/` and `data/returns_manifest.csv` | 95 photos of returned tea lights from the second warehouse, one month, **no labels**. |
| `data/catalogue/kettle/` and `data/catalogue_manifest.csv` | 102 catalogue photos of the new category: 64 for training, 38 for your test. |
| `data/customer_photos/` and `data/customer_photos_manifest.csv` | 102 customer photos of the new kettles, **without the answer**: which catalogue photo each one shows. |
| `data/credits.csv` | The authors and licences of the kettle photos. |
| `../data/` | The course data of the first warehouse and the eight earlier categories. |

The course team keeps the answers (which returns are damaged, which kettle each customer photo shows) and a hidden test. Your mentor scores your final numbers on them once.

## What you deliver

1. **A framing note**: the kind of answer, the camera set-up, the cost of each mistake and the daily review budget.
2. **A comparison table** with a baseline and at least three method families, on the same images with the same evaluation, with results by class and by camera.
3. **An inspection method** with thresholds set from the review budget. Say how you set them without labels from the new camera, and what you would label first.
4. **The image service run over the second warehouse's month**: unsure and privacy-sensitive photos sent to review, latency on a laptop CPU, and the camera shift found and handled.
5. **A one-page recommendation for Hamid**, including what the system cannot see and what a person still checks.

The assignment page on the course site gives the full rules. Two rules matter most: never tune a threshold on a test set, and never send a photo with a person in it to a hosted model without blurring it first.

## Licences

The returns photos come from the VisA inspection set (CC BY 4.0) and were changed by our code to look like another camera. The kettle photos are cut from Open Images photos (CC BY 2.0, authors in `data/credits.csv`); the customer photos were simulated from them by code. See `data/dataset-card.md`.
