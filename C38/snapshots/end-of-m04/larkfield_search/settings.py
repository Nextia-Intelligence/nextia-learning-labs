"""Settings that you can change from the command line without editing code: `--set title=2 --set alpha=0.3`.

The runs read their settings here, so `search eval --run bm25-fields --set title=2` measures another field
weight, and `search eval --run hybrid-blend --set alpha=0.3` another blend.
"""

VALUES = {}


def parse(pairs):
    for pair in pairs or []:
        key, _, value = pair.partition("=")
        VALUES[key.strip()] = float(value)


def get(key, default):
    return VALUES.get(key, default)


def weights(defaults):
    """Field weights with any --set field=value applied."""
    return {f: VALUES.get(f, w) for f, w in defaults.items()}
