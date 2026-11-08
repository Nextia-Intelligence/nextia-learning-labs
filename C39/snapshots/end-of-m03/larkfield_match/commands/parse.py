"""match parse: split a name, an address or a product title into parts."""

from .. import parse

NAME = "parse"
HELP = "Split a value into parts: match parse name|address|title \"TEXT\"."


def add(p):
    p.add_argument("kind", choices=["name", "address", "title"])
    p.add_argument("text")


def run(args):
    fn = {"name": parse.split_name, "address": parse.split_address, "title": parse.parse_title}[args.kind]
    for k, v in fn(args.text).items():
        print(f"  {k:<10} {v!r}")
