"""Models that the project downloads once, each pinned by URL and SHA-256 (licences in the course README)."""
import hashlib
import urllib.request

from larkspeech.paths import models_dir

HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
FILES = {
    # Speaker embeddings: WeSpeaker ResNet-34 trained on VoxCeleb (Apache-2.0), the sherpa-onnx ONNX copy.
    "spk/wespeaker_en_voxceleb_resnet34_LM.onnx": (
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"
        "wespeaker_en_voxceleb_resnet34_LM.onnx",
        "e9848563da86f263117134dfd7ad63c92355b37de492b55e325400c9d9c39012"),
    # The IVR's voices (Piper, MIT): LJ Speech (public domain) and SIWIS (CC BY 4.0).
    "piper/en_US-ljspeech-medium.onnx": (
        HF + "en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx",
        "6f52a751e2349abe7a76735eb09dc1875298c77ea2342ffd2fef79ff81b87f22"),
    "piper/en_US-ljspeech-medium.onnx.json": (HF + "en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx.json", None),
    "piper/fr_FR-siwis-medium.onnx": (
        HF + "fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx",
        "641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99"),
    "piper/fr_FR-siwis-medium.onnx.json": (HF + "fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json", None),
}


def path(name):
    """The local file of a model, downloaded and checked the first time."""
    p = models_dir() / name
    if not p.exists():
        url, digest = FILES[name]
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".part")
        print(f"Downloading {name} ...", flush=True)
        urllib.request.urlretrieve(url, tmp)
        if digest and hashlib.sha256(tmp.read_bytes()).hexdigest() != digest:
            tmp.unlink()
            raise RuntimeError(f"{name}: the download does not match its SHA-256; try again")
        tmp.rename(p)
    return p
