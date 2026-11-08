# Models of the image service

| File | What it is | Licence |
|---|---|---|
| `inspector/model.onnx` | ResNet-18 (timm `resnet18.a1_in1k`) up to its third block, exported to ONNX and quantised to int8. It turns a 224 x 224 photo into 784 patch vectors. | Apache-2.0 (the weights' model card) |
| `inspector/bank.npy` | A memory of 20,000 patch vectors from the 380 good training candles. | made by the course team from VisA photos (CC BY 4.0) |
| `inspector/config.json` | The check line and the fail line (chosen on the validation photos for 100 checks a day), and the scores of the good validation photos (for the drift check). | |
| `faces/face_detection_yunet_2023mar.onnx` | YuNet, a small face detector from the OpenCV Zoo. The service uses it only to blur faces. | MIT (`faces/LICENSE`) |

The inspector is a small PatchCore: the score of a photo is the largest distance from one of its patches to the nearest patch in the memory. A high score means "this part of the photo looks like no good candle we have seen".

The ResNet-18 weights were trained on ImageNet. Check the terms of the training data as well as the licence of the weights before you use a pretrained model in a product.
