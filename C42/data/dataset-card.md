# Larkfield images: dataset card

Larkfield is a fictional online shop for home and garden products. These images are for learning only. They come from open sources or are made by our code, and every file says which.

## The sets

| Set | Folder | What | Labels |
|---|---|---|---|
| Catalogue | `catalogue/train`, `val`, `test` | Product photos, 256 x 256 pixels, in 8 categories: bowl, candle, chair, cushion, lamp, mug, plant pot, vase. Cut from Open Images photos. | `catalogue/manifest.csv`: label, split, source, licence, author |
| New studio | `catalogue/new_studio` | The test photos again, with warmer and brighter light (changed by code). | `catalogue/new_studio_manifest.csv` |
| Returns | `returns/train`, `val`, `test` | Photos of four tea light candles, 320 pixels wide, good or damaged, from the VisA inspection set. Damaged photos have a mask of the damage in `masks/`. | `returns/manifest.csv`: status, damage type, mask |
| Month | `returns/month` | 30 days of returns photos, with no labels. The returns camera changes in the middle of the month (changed by code). | `returns/month_manifest.csv` |
| Pallets | `pallets/train`, `val`, `test` | Boxes on pallets, 512 x 384 pixels, drawn by our code: from loose to very tight. Every box has an exact box and mask. | `pallets/<split>.json` (COCO format): boxes, masks, count, crowding |
| Customer photos | `customer_photos` | A phone photo of each catalogue test product: another angle, poor light, blur and noise (simulated from the catalogue photo by code). | `customer_photos/manifest.csv`: the catalogue photo it shows |

Other files: `costs.json` (the cost table: assumptions), `comparison_table.json` (the course's measured rows), `embeddings/` (embeddings of the catalogue and customer photos by three pinned models), `predictions/` (recorded detector boxes and anomaly scores), `recordings/` (recorded answers of two vision-language models, and the attribute labels of 50 catalogue photos), `sealed-key.txt` (see below), `SHA256SUMS`.

## Sources and licences

- **Open Images V7** (Google): the catalogue photos are cut from photos of the validation and test splits. The images are listed as CC BY 2.0; each photo's author and its Flickr page are in `catalogue/manifest.csv`. When you show a photo, name its author and the licence. The box labels are CC BY 4.0 (Google LLC). Open Images says that it cannot guarantee the licence of every photo.
- **VisA** (Zou, Jeong, Pemula, Zhang and Dabeer, Amazon, "SPot-the-Difference Self-supervised Pre-training for Anomaly Detection and Segmentation", ECCV 2022): the returns photos are the candle class, resized. CC BY 4.0. Source: https://github.com/amazon-science/spot-diff
- **Pallet photos**: drawn by our code, CC0 1.0.
- **Faces**: three faces from paintings in the public domain (Vermeer, van Gogh, Leonardo da Vinci, from Wikimedia Commons) appear in the background of three month photos. No photo of a real person is in these sets.

## How the sets were made

- Catalogue: photos with a single, clear object of the category, at least 5% of the photo. We removed every photo with a person in it: by the people labels of Open Images, by a face detector and by a person detector, and then by looking at every photo. If you still find a person, tell us.
- The splits are fixed. A photo is never in two splits. The candle category has only 15 training photos on purpose.
- Changes made by code are marked `synthetic: yes` in the manifests: the new studio, the customer photos, the second half of the month and the photos with a painted face.

## Problems we planted

The course tells you about each one when you meet it: a category with only 15 training photos; some wrong labels in one category; some photos in the catalogue twice; warmer light in the new studio; boxes stacked so tight that they touch; a damage smaller than one pixel at 224 pixels; a camera change in the month; a face in the background of a few photos.

`sealed-key.txt` holds the answers for the wrong labels and the double photos, packed (zlib and base64) so that you do not read them by chance. It is not a secret: `compare.reveal()` unpacks it, so that you can score your own search.

## Hidden sets

The course team keeps a hidden test set of each kind (catalogue, returns, pallets, customer photos) and the final assignment's images. They are not here, so that your final scores are honest.
