"""The local store (SQLite): test customers, their orders, product reviews, conversations and traces.

Every customer and order here is test data. `python -m helpdesk reset` restores it.
"""

import json
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
create table customers (id text primary key, name text, email text, language text, rewards text);
create table orders (id text primary key, customer_id text, status text, placed text, delivered text, shipped text,
                     province text, shipping_fee real, items text);
create table reviews (id integer primary key, product text, rating integer, text text);
create table conversations (id text primary key, customer_id text, seed integer, mode text, created_at text);
create table messages (conversation_id text, turn integer, role text, text text, trace_id text);
create table traces (id text primary key, conversation_id text, turn integer, body text);
create table actions (id integer primary key, conversation_id text, turn integer, tool text, args text, result text);
create table refunds (id integer primary key, order_id text, sku text, amount real, conversation_id text);
create table counters (name text primary key, value integer);
"""


def db_path():
    return config.home() / "store.sqlite"


def reset() -> None:
    p = db_path()
    if p.exists():
        p.unlink()
    seed = json.loads((config.DATA / "seed.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(p)
    con.executescript(SCHEMA)
    for c in seed["customers"]:
        con.execute("insert into customers values (?,?,?,?,?)",
                    (c["id"], c["name"], c["email"], c["language"], c["rewards"]))
    for o in seed["orders"]:
        con.execute("insert into orders values (?,?,?,?,?,?,?,?,?)",
                    (o["id"], o["customer_id"], o["status"], o["placed"], o["delivered"], o.get("shipped"),
                     o["province"], o["shipping_fee"], json.dumps(o["items"])))
    for r in seed["reviews"]:
        con.execute("insert into reviews (product, rating, text) values (?,?,?)", (r["product"], r["rating"], r["text"]))
    con.execute("insert into counters values ('conversation', 0)")
    con.commit()
    con.close()


@contextmanager
def connect():
    if not db_path().exists():
        reset()
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _order(row) -> dict | None:
    if row is None:
        return None
    o = dict(row)
    o["items"] = json.loads(o["items"])
    return o


def get_order(order_id: str) -> dict | None:
    with connect() as con:
        return _order(con.execute("select * from orders where id = ?", (order_id.upper(),)).fetchone())


def orders_of(customer_id: str) -> list[dict]:
    with connect() as con:
        rows = con.execute("select * from orders where customer_id = ? order by id", (customer_id,)).fetchall()
        return [_order(r) for r in rows]


def get_customer(customer_id: str) -> dict | None:
    with connect() as con:
        r = con.execute("select * from customers where id = ?", (customer_id,)).fetchone()
        return dict(r) if r else None


def customers() -> list[dict]:
    with connect() as con:
        return [dict(r) for r in con.execute("select * from customers order by id")]


def set_status(order_id: str, status: str) -> None:
    with connect() as con:
        con.execute("update orders set status = ? where id = ?", (status, order_id))


def add_refund(order_id: str, sku: str, amount: float, conversation_id: str) -> int:
    with connect() as con:
        cur = con.execute("insert into refunds (order_id, sku, amount, conversation_id) values (?,?,?,?)",
                          (order_id, sku, amount, conversation_id))
        return cur.lastrowid


def refunds(order_id: str | None = None) -> list[dict]:
    with connect() as con:
        q = "select * from refunds" + (" where order_id = ?" if order_id else "") + " order by id"
        return [dict(r) for r in con.execute(q, (order_id,) if order_id else ())]


def reviews(product: str) -> list[dict]:
    with connect() as con:
        rows = con.execute("select * from reviews where product = ? order by id", (product,)).fetchall()
        return [dict(r) for r in rows]


def new_conversation(customer_id: str, seed: int, mode: str, created_at: str) -> str:
    with connect() as con:
        con.execute("update counters set value = value + 1 where name = 'conversation'")
        n = con.execute("select value from counters where name = 'conversation'").fetchone()[0]
        cid = f"c-{n:04d}"
        con.execute("insert into conversations values (?,?,?,?,?)", (cid, customer_id, seed, mode, created_at))
        return cid


def get_conversation(cid: str) -> dict | None:
    with connect() as con:
        r = con.execute("select * from conversations where id = ?", (cid,)).fetchone()
        if not r:
            return None
        c = dict(r)
        c["messages"] = [dict(m) for m in con.execute(
            "select turn, role, text, trace_id from messages where conversation_id = ? order by rowid", (cid,))]
        return c


def add_message(cid: str, turn: int, role: str, text: str, trace_id: str | None) -> None:
    with connect() as con:
        con.execute("insert into messages values (?,?,?,?,?)", (cid, turn, role, text, trace_id))


def save_trace(trace: dict) -> None:
    with connect() as con:
        con.execute("insert or replace into traces values (?,?,?,?)",
                    (trace["trace_id"], trace["conversation_id"], trace["turn"], json.dumps(trace)))


def get_trace(trace_id: str) -> dict | None:
    with connect() as con:
        r = con.execute("select body from traces where id = ?", (trace_id,)).fetchone()
        return json.loads(r[0]) if r else None


def traces_of(cid: str) -> list[dict]:
    with connect() as con:
        rows = con.execute("select body from traces where conversation_id = ? order by turn", (cid,)).fetchall()
        return [json.loads(r[0]) for r in rows]


def log_action(cid: str, turn: int, tool: str, args: dict, result: dict) -> None:
    with connect() as con:
        con.execute("insert into actions (conversation_id, turn, tool, args, result) values (?,?,?,?,?)",
                    (cid, turn, tool, json.dumps(args), json.dumps(result)))
