"""match splink: train Splink without labels and show what it learned."""

from .. import splinkmodel

NAME = "splink"
HELP = "Train a Splink model on DuckDB without labels, save it to outputs/models/splink.json and show its weights."


def add(p):
    p.add_argument("--show", action="store_true", help="show the saved model without training again")


def run(args):
    if not args.show:
        linker, secs = splinkmodel.train()
        path = splinkmodel.save(linker)
        print(f"Trained Splink in {secs:.1f} s; saved to {path}")
    t, prior = splinkmodel.weights_table()
    print(f"Probability that two random records match: {prior:.2e}")
    print(t.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
