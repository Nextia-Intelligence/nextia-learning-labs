"""The text of a product that the models read (the bi-encoder and the cross-encoder)."""

DESCRIPTION_WORDS = 40


def product_text(title, product_class, description):
    """Title, product class and the first 40 words of the description."""
    words = str(description).split()[:DESCRIPTION_WORDS]
    return f"{title}. {product_class}. {' '.join(words)}"
