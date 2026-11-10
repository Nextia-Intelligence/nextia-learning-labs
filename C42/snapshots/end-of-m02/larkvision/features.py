"""Hand-made features: a colour histogram and HOG (Module 2)."""
import numpy as np
from PIL import Image


def colour_histogram(path, bins=(8, 4, 4)):
    """Hue, saturation and value in 8 x 4 x 4 bins; the square root, so that distances compare histograms fairly."""
    hsv = np.asarray(Image.open(path).convert("RGB").resize((128, 128)).convert("HSV")).reshape(-1, 3)
    h, _ = np.histogramdd(hsv, bins=bins, range=((0, 256), (0, 256), (0, 256)))
    return np.sqrt(h.ravel() / h.sum())


def hog_features(path, size=128):
    from skimage.feature import hog
    g = np.asarray(Image.open(path).convert("L").resize((size, size)), float) / 255
    return hog(g, orientations=9, pixels_per_cell=(16, 16), cells_per_block=(2, 2), feature_vector=True)
