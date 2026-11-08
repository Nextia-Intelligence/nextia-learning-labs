"""`vision serve`: run the image service on this computer."""


def register(sub):
    p = sub.add_parser("serve", help="run the image service (FastAPI)")
    p.add_argument("--port", type=int, default=8042)
    p.set_defaults(run=run)


def run(args):
    import uvicorn

    from larkvision.service import default_app
    uvicorn.run(default_app(), host="127.0.0.1", port=args.port)
