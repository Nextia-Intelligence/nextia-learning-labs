"""Command line: python -m helpdesk <command>. Run python -m helpdesk --help for the list."""

import argparse
import json
import sys
from pathlib import Path

from . import APP_VERSION, MODEL_NAME, PROMPT_VERSION, assistant, config, export, store


def _mode(args) -> str:
    return "live" if getattr(args, "live", False) else "sim"


def cmd_version(args) -> None:
    print(f"larkfield-helpdesk {APP_VERSION} | model {MODEL_NAME} (simulated) | prompt {PROMPT_VERSION} | "
          f"app date {config.TODAY}")


def cmd_reset(args) -> None:
    store.reset()
    print("The store is reset: 4 test customers, 8 orders, 8 reviews, no conversations.")


def cmd_ask(args) -> None:
    cid = assistant.start(args.customer, args.seed, _mode(args))
    out = assistant.send(cid, args.message)
    seed = store.get_conversation(cid)["seed"]
    print(out["reply"])
    print(f"\n[conversation {cid} | trace {out['trace_id']} | seed {seed}]")


def cmd_chat(args) -> None:
    cid = assistant.start(args.customer, args.seed, _mode(args))
    conv = store.get_conversation(cid)
    print(f"Larkfield help desk {APP_VERSION} ({'live model' if conv['mode'] == 'live' else 'simulated model sim-1'}).")
    print(f"Signed in as test customer {conv['customer_id']}. Conversation {cid}, seed {conv['seed']}.")
    print("Type a message. Commands: /trace, /export, /new, /quit")
    last = None
    while True:
        try:
            line = input("\nyou> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() == "/quit":
            break
        if line.strip() == "/new":
            cid = assistant.start(args.customer, None, _mode(args))
            print(f"New conversation {cid}, seed {store.get_conversation(cid)['seed']}.")
            continue
        if line.strip() == "/trace":
            print(json.dumps(store.get_trace(last), indent=2, ensure_ascii=False) if last else "No trace yet.")
            continue
        if line.strip() == "/export":
            path = Path(f"{cid}.json")
            path.write_text(export.dumps(export.export(cid)), encoding="utf-8")
            print(f"Exported to {path}")
            continue
        try:
            out = assistant.send(cid, line)
        except Exception as e:
            print(f"\nERROR: {type(e).__name__}: {e} (the trace keeps the error)")
            continue
        last = out["trace_id"]
        print(f"\nassistant> {out['reply']}\n[trace {last}]")


def cmd_trace(args) -> None:
    t = store.get_trace(args.trace_id)
    if t is None:
        sys.exit(f"No trace {args.trace_id}. (python -m helpdesk reset deletes all traces.)")
    print(json.dumps(t, indent=2, ensure_ascii=False))


def cmd_export(args) -> None:
    try:
        data = export.export(args.conversation_id)
    except KeyError:
        sys.exit(f"No conversation {args.conversation_id}.")
    text = export.dumps(data)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Exported {args.conversation_id} to {args.output}")
    else:
        print(text, end="")


def cmd_replay(args) -> None:
    """Runs the customer messages of an export again with the same seed, and compares the replies."""
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if data.get("mode") == "live":
        print("Note: this export is from live mode. A real model does not replay exactly; this replay uses sim-1.")
    if args.reset:
        store.reset()
    cid = assistant.start(data["customer_id"], data["seed"], "sim")
    same = 0
    users = [m for m in data["messages"] if m["role"] == "user"]
    olds = {m["turn"]: m["text"] for m in data["messages"] if m["role"] == "assistant"}
    for t in data.get("traces", []):  # a turn that ended in an app error has no reply, only the error in its trace
        if t.get("error") and t["turn"] not in olds:
            olds[t["turn"]] = f"ERROR: {t['error']}"
    for m in users:
        try:
            new = assistant.send(cid, m["text"])["reply"]
        except Exception as e:
            new = f"ERROR: {type(e).__name__}: {e}"
        old = olds.get(m["turn"], "(no reply: the app failed)")
        ok = new == old
        same += ok
        label = ("same error" if new.startswith("ERROR: ") else "same reply") if ok else "DIFFERENT reply"
        print(f"turn {m['turn']}: {label}")
        if not ok:
            print(f"  before: {old[:200]}\n  now:    {new[:200]}")
    print(f"{same} of {len(users)} replies are the same (seed {data['seed']}, new conversation {cid}).")


def cmd_serve(args) -> None:
    from . import server
    server.serve(args.port, args.seed, _mode(args))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m helpdesk", description="Larkfield help desk (practice app).")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        s = sub.add_parser(name, help=help_)
        s.set_defaults(fn=fn)
        return s

    def common(s):
        s.add_argument("--customer", default=None, help="test customer ID (default C-1001)")
        s.add_argument("--seed", type=int, default=None, help="seed for the simulated model (default: random)")
        s.add_argument("--live", action="store_true", help="use a real model (see the README)")

    s = add("serve", cmd_serve, "start the web app on http://localhost:8730")
    s.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    s.add_argument("--seed", type=int, default=None, help="use this seed for every new conversation")
    s.add_argument("--live", action="store_true")
    common(add("chat", cmd_chat, "chat in the terminal"))
    s = add("ask", cmd_ask, "send one message in a new conversation")
    s.add_argument("message")
    common(s)
    add("trace", cmd_trace, "show a trace").add_argument("trace_id")
    s = add("export", cmd_export, "export a conversation as JSON")
    s.add_argument("conversation_id")
    s.add_argument("-o", "--output")
    s = add("replay", cmd_replay, "run an exported conversation again with its seed")
    s.add_argument("file")
    s.add_argument("--reset", action="store_true", help="reset the store first (for actions)")
    add("reset", cmd_reset, "restore the test data and delete conversations and traces")
    add("version", cmd_version, "show the versions")
    args = p.parse_args(argv)
    try:
        args.fn(args)
    except assistant.HelpdeskError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
