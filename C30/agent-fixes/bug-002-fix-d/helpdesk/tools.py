"""The assistant's tools. Each tool acts for the signed-in customer only."""

from datetime import date

from . import config, store

# What the model sees about each tool (live mode sends these as function definitions).
TOOL_SPECS = [
    {"name": "lookup_order", "description": "Look up one of the signed-in customer's orders: status, dates and items.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "LK- and 6 digits"}},
                    "required": ["order_id"]}},
    {"name": "cancel_order",
     "description": "Cancel one of the signed-in customer's orders while it is Processing. Only after the customer "
                    "said yes to a question that named the order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"},
                                                     "confirmed": {"type": "boolean"}},
                    "required": ["order_id", "confirmed"]}},
    {"name": "start_refund",
     "description": "Start the return and refund of one item of a delivered order. Only after the customer said yes "
                    "to a question that named the item and the amount.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "sku": {"type": "string"},
                                                     "confirmed": {"type": "boolean"}},
                    "required": ["order_id", "sku", "confirmed"]}},
    {"name": "product_reviews", "description": "Read the customer reviews of a product, by product code (for "
                                               "example GR-310).",
     "parameters": {"type": "object", "properties": {"product": {"type": "string"}}, "required": ["product"]}},
]

RETURN_SHIPPING = 12.95
PICKUP_FEE = 49.0


def _days_since(day: str) -> int:
    return (date.fromisoformat(config.TODAY) - date.fromisoformat(day)).days


def return_window(delivered: str) -> int:
    """Days to return an unused item: 45 for deliveries from 1 November 2026 (returns policy v4), else 30."""
    return 45 if delivered >= "2026-11-01" else 30


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = store.get_order(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"ok": False, "error": "not_found", "message": f"No order {order_id.upper()} on this account."}
    return {"ok": True, "order": order}


def cancel_order(customer_id: str, order_id: str, confirmed: bool) -> dict:
    found = lookup_order(customer_id, order_id)
    if not found["ok"]:
        return found
    if not confirmed:
        return {"ok": False, "error": "not_confirmed", "message": "The customer has not confirmed."}
    order = found["order"]
    if order["status"] != "Processing":
        return {"ok": False, "error": "not_cancellable",
                "message": f"Order {order['id']} is {order['status']}; only Processing orders can be cancelled."}
    store.set_status(order["id"], "Cancelled")
    return {"ok": True, "order_id": order["id"], "status": "Cancelled"}


def free_return_label(order: dict) -> bool:
    """Returns policy v4: Rewards members get a free return label for orders delivered from 1 November 2026."""
    customer = store.get_customer(order["customer_id"]) or {}
    return customer.get("rewards") in ("member", "gold") and (order["delivered"] or "") >= "2026-11-01"


def refund_amount(order: dict, sku: str, reason: str = "changed_mind") -> float:
    item = next(i for i in order["items"] if i["sku"] == sku)
    amount = item["price"] * item["qty"]
    if reason != "changed_mind":
        return round(amount, 2)
    if item.get("weight_kg", 0) > 30:
        amount -= PICKUP_FEE  # items over 30 kg: a pickup instead of a label, also for Rewards members
    elif not free_return_label(order):
        amount -= RETURN_SHIPPING
    return round(amount, 2)


def start_refund(customer_id: str, order_id: str, sku: str, confirmed: bool, conversation_id: str) -> dict:
    found = lookup_order(customer_id, order_id)
    if not found["ok"]:
        return found
    if not confirmed:
        return {"ok": False, "error": "not_confirmed", "message": "The customer has not confirmed."}
    order = found["order"]
    if order["status"] != "Delivered" or not order["delivered"]:
        return {"ok": False, "error": "not_delivered", "message": "Only delivered orders can be returned."}
    if _days_since(order["delivered"]) > return_window(order["delivered"]):
        return {"ok": False, "error": "outside_window", "message": "The return window has ended."}
    if not any(i["sku"] == sku for i in order["items"]):
        return {"ok": False, "error": "no_such_item", "message": f"No item {sku} in order {order['id']}."}
    amount = refund_amount(order, sku)
    rid = store.add_refund(order["id"], sku, amount, conversation_id)
    return {"ok": True, "refund_id": rid, "order_id": order["id"], "sku": sku, "amount": amount}


def product_reviews(product: str) -> dict:
    rows = store.reviews(product.upper())
    return {"ok": True, "product": product.upper(), "reviews": [{"rating": r["rating"], "text": r["text"]} for r in rows]}
