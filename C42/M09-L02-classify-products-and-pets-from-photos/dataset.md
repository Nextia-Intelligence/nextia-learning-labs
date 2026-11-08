# Dataset card: Oxford-IIIT Pet Dataset (subset for case study 2)

Used by: Vision AI, case study 2 *Classify products and pets from photos*, `classify-products-and-pets-from-photos.ipynb`

| Field | Value |
|---|---|
| Source | <https://www.robots.ox.ac.uk/~vgg/data/pets/> |
| Publisher / creator | Omkar M. Parkhi, Andrea Vedaldi, Andrew Zisserman, C. V. Jawahar (Visual Geometry Group, University of Oxford; IIIT Hyderabad) |
| Licence | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) ("available to download for commercial/research purposes"); the copyright of each photo remains with its owner |
| Attribution text | "The Oxford-IIIT Pet Dataset" by O. M. Parkhi, A. Vedaldi, A. Zisserman and C. V. Jawahar, https://www.robots.ox.ac.uk/~vgg/data/pets/, CC BY-SA 4.0. Paper: "Cats and Dogs", IEEE CVPR 2012. |
| Version or access date | `images.tar.gz` of 29 July 2022 (Last-Modified on the server) |
| File used | `https://thor.robots.ox.ac.uk/pets/images.tar.gz`, kept in `data/`: **no**. Labs hosts no photo and no file made from the photos: the notebook downloads the archive from the original site (lead decision, to keep share-alike away from the course's own files). |
| SHA-256 | `67195c5e1c01f1ab5f9b6a5d22b8c27a580d896ece458917e61d459337fa318d` (images.tar.gz, 791,918,971 bytes) |
| Size | 7,349 photos of 37 breeds (12 cats, 25 dogs) in the archive; this case study uses 2,183 |

## What one photo means

One photo shows one cat or dog, mostly one animal and often its head. The label is its breed, from the file name (`Abyssinian_26.jpg`: breed Abyssinian, photo 26). In the dataset, cat breeds start with a capital letter.

## Why this dataset

It is the standard fine-grained set: 37 classes, several pairs that look alike (bull terrier types, grey short-haired cats, pointed long-haired cats), about 100 photos per breed in each official list, and a licence that allows commercial use. Candidates that were not allowed: Food-101 (no licence for the images), Caltech-UCSD Birds and FGVC-Aircraft (non-commercial), Oxford 102 Flowers (no licence stated), Stanford Dogs (ImageNet terms).

## Changes we made

- **A fixed subset**, chosen by a seeded shuffle of the official lists: per breed, 20 pool and 10 validation photos (official trainval list), 25 test and 4 new photos (official test list). The photo numbers are in the notebook's `SUBSET` (a list made from the dataset: CC BY-SA 4.0).
- **People removed.** 2,443 candidate photos were checked by a person detector (torchvision Faster R-CNN MobileNetV3, COCO, class person, score 0.4 or more); 260 with a person found were not used. A detector can miss a hand or a leg: the photos that the notebook and the lesson show were also looked at by eye.
- No photo is changed. The notebook resizes them in memory for each model.

## Limitations and cautions

- **Pure-bred, typical photos from the internet.** Real shelter or customer photos show mixed breeds, puppies, bad light and odd angles. The accuracy here is higher than you should expect there.
- **Labels are breed names given by the photo owners and checked by the dataset authors.** A few look wrong (for example a white cat labelled Abyssinian). Breed is a guess about looks, not about ancestry or behaviour.
- **Pretrained models have seen these breeds.** ImageNet-1k has 25 of the 37 as classes (22 of the 25 dogs), and CLIP learned from captions of internet photos. This makes the task easier for them than a shop's own categories.
- Some photos carry a photographer's watermark or a cat-show logo.
