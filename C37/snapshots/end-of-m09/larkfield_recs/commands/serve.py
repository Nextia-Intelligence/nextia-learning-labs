"""recs serve: run the recommendation service on this computer (stop it with Ctrl+C)."""

NAME = "serve"
HELP = "Run the recommendation service (FastAPI) on 127.0.0.1; stop it with Ctrl+C."


def add(p):
    p.add_argument("--port", type=int, default=8037)


def run(args):
    import uvicorn

    from ..service import create_app
    print(f"Larkfield recommendations on http://127.0.0.1:{args.port}/  (try /health, /recommend/C100123, "
          f"/similar/P10020). Stop with Ctrl+C.")
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning")
