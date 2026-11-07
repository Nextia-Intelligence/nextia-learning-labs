# The ready fine-tuned encoder

`finetuned-encoder/` is the small multilingual encoder of the lesson *Fine-tune a small encoder on CPU*, already fine-tuned on the 6,000 training messages, for learners who skip the training.

It keeps only the weights that the training changed (in 16-bit numbers): the 12 layers and the classification head. The word table did not change, so it is not here. To load it, download the base model from Hugging Face and put these weights on top (code below):

- base model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0), at the revision in `routes.json`;
- `changed_weights.safetensors`: the changed weights;
- `routes.json`: the base model, its revision, the order of the routes and the longest input in tokens.

```python
import json, torch
from safetensors.torch import load_file
from transformers import AutoModelForSequenceClassification, AutoTokenizer

meta = json.load(open("finetuned-encoder/routes.json"))
tok = AutoTokenizer.from_pretrained(meta["base_model"], revision=meta["revision"])
model = AutoModelForSequenceClassification.from_pretrained(
    meta["base_model"], revision=meta["revision"], num_labels=len(meta["routes"]))
weights = {k: v.float() for k, v in load_file("finetuned-encoder/changed_weights.safetensors").items()}
model.load_state_dict(weights, strict=False)  # the word table comes from the base model
model.eval()
with torch.no_grad():
    enc = tok(["My parcel never came."], truncation=True, max_length=meta["max_length"], return_tensors="pt")
    probs = torch.softmax(model(**enc).logits, -1)[0]
print(dict(zip(meta["routes"], probs.round(decimals=3).tolist())))
```

Licence: Apache-2.0, as the base model.
