# Final assignment images: dataset card

These images are for the final assignment of the Vision AI course. Larkfield is a fictional shop.

| Set | Count | Source | Licence | Changed by code? |
|---|---|---|---|---|
| Returns of the second warehouse (`returns/`) | 95 photos, one month, no labels | VisA candle photos (Zou, Jeong, Pemula, Zhang and Dabeer, Amazon) | CC BY 4.0 | Yes: yellow light, zoomed out, noise (the new camera). A few photos have a painted face from a public-domain portrait in the background. |
| Kettles and teapots (`catalogue/kettle/`) | 102 photos, 256 x 256 (64 train, 38 test) | Open Images V7, class Kettle (it also holds teapots and coffee pots) | CC BY 2.0, authors in `credits.csv`; boxes CC BY 4.0 (Google LLC) | No (cut and resized) |
| Customer photos of kettles (`customer_photos/`) | 102 photos, 320 x 240 | Simulated from the kettle photos | CC BY 2.0 (the kettle photos' authors) | Yes |

We removed every kettle photo with a person in it (labels, a face detector, a person detector and a look at each photo). The photo IDs here are new: they do not show which photo is damaged or which kettle a customer photo shows. The answers stay with the course team.
