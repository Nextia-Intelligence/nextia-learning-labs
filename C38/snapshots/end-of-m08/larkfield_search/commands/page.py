"""search suggest, search facets and search serve: the parts of search that people see."""

from .. import facets, runs, suggest


class Suggest:
    NAME = "suggest"
    HELP = "Show autocomplete suggestions for what someone has typed so far."

    @staticmethod
    def add(p):
        p.add_argument("prefix")
        p.add_argument("-n", type=int, default=8)

    @staticmethod
    def run(args):
        for text, weight in suggest.suggest(args.prefix, args.n):
            print(f"{weight:6}  {text}")


class Facets:
    NAME = "facets"
    HELP = "Show the facet counts (class, colour, price, availability) of a query's top 100 results."

    @staticmethod
    def add(p):
        p.add_argument("text")
        p.add_argument("--run", default="ltr")

    @staticmethod
    def run(args):
        res = runs.get(args.run)(args.text, None, 100)
        print(f'{args.run}: "{args.text}" -> {len(res)} results')
        for name, values in facets.facets([p for p, _ in res]).items():
            print(f"{name}: " + ", ".join(f"{v} ({n})" for v, n in values))


class Serve:
    NAME = "serve"
    HELP = "Serve the ready-made search page on this computer (http://127.0.0.1:8038/)."

    @staticmethod
    def add(p):
        p.add_argument("--port", type=int, default=8038)
        p.add_argument("--run", default="ltr")

    @staticmethod
    def run(args):
        from ..app import serve
        serve(args.port, args.run)


COMMANDS = [Suggest, Facets, Serve]
