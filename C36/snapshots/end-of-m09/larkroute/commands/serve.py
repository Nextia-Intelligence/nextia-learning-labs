"""route serve: run the routing service on this computer (stop it with Ctrl+C)."""


def run(args):
    import uvicorn
    uvicorn.run("larkroute.service:app", host="127.0.0.1", port=args.port)


def add(sub):
    p = sub.add_parser("serve", help="run the routing service (FastAPI) on 127.0.0.1")
    p.add_argument("--port", type=int, default=8036)
    p.set_defaults(func=run)
