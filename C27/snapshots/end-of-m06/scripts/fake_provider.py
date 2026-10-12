"""A practice model provider on your computer that misbehaves on purpose (Module 4).

    python -m scripts.fake_provider --mode slow --delay 30     answers after 30 seconds
    python -m scripts.fake_provider --mode error               HTTP 500 every time
    python -m scripts.fake_provider --mode busy                HTTP 429 with Retry-After: 1
    python -m scripts.fake_provider --mode ok                  a valid answer at once

It speaks just enough of the OpenAI-compatible Chat Completions API for the assistant's live
provider: point the API at it with ANSWER_PROVIDER=live LLM_BASE_URL=http://127.0.0.1:8401/v1.
Every response is constructed: nothing here is a real model.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OK_BODY = {"answerable": False, "answer": "The documents do not say. (fake provider)", "claims": []}


def make_handler(mode: str, delay: float, calls: list):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            length = int(self.headers.get("content-length", 0))
            self.rfile.read(length)
            calls.append(time.monotonic())
            if mode == "slow":
                time.sleep(delay)
            if mode == "error":
                return self._send(500, {"error": {"message": "constructed failure"}})
            if mode == "busy":
                return self._send(429, {"error": {"message": "constructed rate limit"}}, {"Retry-After": "1"})
            self._send(200, {"id": "fake", "object": "chat.completion", "model": "fake",
                             "choices": [{"index": 0, "finish_reason": "stop",
                                          "message": {"role": "assistant", "content": json.dumps(OK_BODY)}}],
                             "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

        def _send(self, status: int, body: dict, headers: dict | None = None):
            data = json.dumps(body).encode()
            try:
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass   # the client gave up (its timeout): that is the point of "slow"

    return Handler


class FakeProvider:
    """Runs in a thread (for scripts and tests). `calls` records when each request arrived."""

    def __init__(self, mode: str, delay: float = 30.0, port: int = 0):
        self.calls: list[float] = []
        self.server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(mode, delay, self.calls))
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}/v1"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m scripts.fake_provider")
    parser.add_argument("--mode", choices=["slow", "error", "busy", "ok"], default="slow")
    parser.add_argument("--delay", type=float, default=30.0)
    parser.add_argument("--port", type=int, default=8401)
    args = parser.parse_args()
    with FakeProvider(args.mode, args.delay, args.port) as fake:
        print(f"Fake provider ({args.mode}) on {fake.url}. Ctrl+C stops it.")
        try:
            fake.thread.join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
