"""Make the course's document set: receipts, scans, photos, a price list, a spreadsheet, policies.

    python -m doc_extract.generate            # writes data/documents/ and data/truth.jsonl
    python -m doc_extract.generate --check    # also compares every file with data/SHA256SUMS

Every document is made up by this program. No real customer, shop receipt or person is in it.
The same program and the same package versions write the same bytes, so the course's numbers
can be checked. The true value of every field is known because this program wrote it: it is in
data/truth.jsonl.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = Path(__file__).resolve().parent / "sources"
SEED = 13
NOTE = "Made-up document for a course. Not a real receipt."
NOTE_FR = "Document fictif pour un cours. Ce n'est pas un vrai reçu."
CENT = Decimal("0.01")

# The shop's products (the same catalogue as the earlier courses), price in CAD.
PRODUCTS = [
    ("BBQ-GR310", "Ember GR-310 gas BBQ", "Barbecue au gaz Ember GR-310", "449.00"),
    ("BENCH-WD", "Wooden garden bench", "Banc de jardin en bois", "249.00"),
    ("CAN-10", "Watering can", "Arrosoir", "19.95"),
    ("CHAIR-G", "Garden chair", "Chaise de jardin", "54.00"),
    ("COMPOST", "Compost bin", "Bac à compost", "64.00"),
    ("CUSH-4", "Cushion covers (set of 4)", "Housses de coussin (4)", "36.00"),
    ("FEEDER", "Bird feeder", "Mangeoire à oiseaux", "22.00"),
    ("HOSE-25", "Garden hose (25 m)", "Tuyau d'arrosage (25 m)", "34.50"),
    ("HR-30", "AquaFlow HR-30 hose reel", "Dévidoir AquaFlow HR-30", "59.00"),
    ("HT-550", "HT-550 hedge trimmer", "Taille-haie HT-550", "99.00"),
    ("KT-180", "KT-180 electric kettle", "Bouilloire électrique KT-180", "49.00"),
    ("LADDER-3", "Step ladder", "Escabeau", "79.00"),
    ("LIGHTS-6", "Solar path lights (6)", "Lampes solaires (6)", "45.00"),
    ("PARASOL", "Patio parasol", "Parasol de terrasse", "129.00"),
    ("PLANTER", "Cedar planter", "Jardinière en cèdre", "89.00"),
    ("POT-TC3", "Terracotta pots (set of 3)", "Pots en terre cuite (3)", "27.50"),
    ("PW-2200", "PW-2200 pressure washer", "Nettoyeur haute pression PW-2200", "189.00"),
    ("SHEARS", "Pruning shears", "Sécateur", "24.95"),
    ("TOOLCHEST", "Tool chest", "Coffre à outils", "119.00"),
]
PARTNER_PRODUCTS = [
    ("Hose nozzle 10-pattern", "12.99"), ("Garden gloves L", "8.49"), ("Brass connector set", "15.75"),
    ("Pruning saw", "21.00"), ("Potting soil 30 L", "9.99"), ("Rake, steel", "27.45"),
]
STORES = {
    "ottawa": ("214 Bank St, Ottawa ON K2P 1X4", "ON", [("HST 13%", "0.13")]),
    "toronto": ("88 Queen St W, Toronto ON M5H 2M5", "ON", [("HST 13%", "0.13")]),
    "vancouver": ("1020 Main St, Vancouver BC V6A 2W1", "BC", [("GST 5%", "0.05"), ("PST 7%", "0.07")]),
    "montreal": ("4100 rue Saint-Denis, Montréal QC H2W 2M5", "QC", [("TPS 5 %", "0.05"), ("TVQ 9,975 %", "0.09975")]),
    "online": ("larkfield.example  ·  help desk 1-800-555-0199", "ON", [("HST 13%", "0.13")]),
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
PAYMENTS = ["Visa ****4821", "Mastercard ****1907", "Debit ****3310", "Cash", "Amex ****2004"]


def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(x: Decimal, lang: str = "en") -> str:
    s = f"{x:,.2f}"
    if lang == "fr":
        s = s.replace(",", " ").replace(".", ",")
    return s


@dataclass
class Receipt:
    doc_id: str
    layout: str  # till | online | partner
    lang: str
    store: str
    date: date
    order_number: str | None
    transaction: str
    items: list[tuple[str, int, Decimal, Decimal]]
    taxes: list[tuple[str, Decimal]]
    shipping: Decimal | None
    payment: str
    currency: str = "CAD"
    total_error: Decimal = Decimal("0")  # a printed total that does not add up
    show_date: bool = True
    vendor: str = "Larkfield"

    @property
    def subtotal(self) -> Decimal:
        return sum((t for *_, t in self.items), Decimal("0"))

    @property
    def tax(self) -> Decimal:
        return sum((a for _, a in self.taxes), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + (self.shipping or 0) + self.tax + self.total_error

    def date_text(self) -> str:
        d = self.date
        if self.lang == "fr":
            return f"{d.day:02d}/{d.month:02d}/{d.year}" if self.layout == "till" else f"{d.day} {MOIS[d.month - 1]} {d.year}"
        if self.layout == "till":
            return d.isoformat()
        if self.layout == "partner":
            return f"{MONTHS[d.month - 1]} {d.day} {d.year}"
        return f"{['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][d.month - 1]} {d.day}, {d.year}"

    def truth(self) -> dict:
        f = {
            "vendor": self.vendor,
            "order_number": self.order_number,
            "date": self.date.isoformat() if self.show_date else None,
            "currency": self.currency,
            "subtotal": str(self.subtotal),
            "shipping": str(self.shipping) if self.shipping is not None else None,
            "tax": str(self.tax),
            "total": str(self.total),
            "payment_method": self.payment.split(" ")[0] if self.payment else None,
        }
        items = [{"description": d, "quantity": q, "unit_price": str(u), "line_total": str(t)}
                 for d, q, u, t in self.items]
        return {"fields": f, "items": items,
                "absent": sorted(k for k, v in f.items() if v is None),
                "adds_up": self.total_error == 0,
                "printed": printed_lines(receipt_pdf(self))}


def make_receipt(doc_id: str, rng: random.Random, layout: str, lang: str = "en", store: str | None = None,
                 with_order: bool = True, currency: str = "CAD") -> Receipt:
    if store is None:
        store = "montreal" if lang == "fr" else rng.choice(["ottawa", "toronto", "vancouver", "online"])
    if layout == "online":
        store = "online" if lang == "en" else "montreal"
    d = date(2026, 6, 1) + timedelta(days=rng.randrange(0, 125))
    n = rng.choice([1, 1, 2, 2, 3, 4])
    items = []
    if layout == "partner":
        for desc, price in rng.sample(PARTNER_PRODUCTS, n):
            q = rng.choice([1, 1, 1, 2, 3])
            items.append((desc, q, Decimal(price), money(Decimal(price) * q)))
    else:
        for _sku, en, fr, price in rng.sample(PRODUCTS, n):
            q = rng.choice([1, 1, 1, 2, 3]) if Decimal(price) < 100 else 1
            items.append((fr if lang == "fr" else en, q, Decimal(price), money(Decimal(price) * q)))
    sub = sum((t for *_, t in items), Decimal("0"))
    shipping = None
    if layout == "online":
        shipping = Decimal("0.00") if sub >= 99 else Decimal("9.95")
    base = sub + (shipping or 0)
    taxes = [(label, money(base * Decimal(rate))) for label, rate in STORES[store][2]]
    if layout == "partner":
        taxes = [("Sales tax 13%", money(base * Decimal("0.13")))]
        store = "partner"
    order = f"LK-{rng.randint(100000, 999999)}" if with_order and layout != "partner" else None
    if layout == "partner":
        order = None
    r = Receipt(doc_id, layout, lang, store, d, order, f"{rng.randint(1, 9):02d}{rng.randint(10, 99)}-{rng.randint(100, 999)}",
                items, taxes, shipping, rng.choice(PAYMENTS), currency=currency)
    if layout == "partner":
        r.vendor = "Maple & Pine Hardware"
    return r


# ---------------------------------------------------------------- receipts as PDF (text layer)

def till_lines(r: Receipt) -> list[tuple[str, str, str]]:
    """The rows of a till receipt: (left text, right text, style)."""
    fr = r.lang == "fr"
    lines: list[tuple[str, str, str]] = []  # (left, right, style)
    rule = ("-" * 36, "", "")
    lines += [("LARKFIELD", "", "title"), ("Maison et jardin" if fr else "Home & Garden", "", "center")]
    for part in STORES[r.store][0].split(", ", 1):
        lines.append((part, "", "center"))
    lines.append(rule)
    if r.show_date:
        lines.append((("Date : " if fr else "Date: ") + r.date_text(), f"{r.date.day % 12 + 9:02d}:{r.date.month * 4 + 7:02d}", ""))
    if r.order_number:
        lines.append((("Commande : " if fr else "Order: ") + r.order_number, "", ""))
    lines.append((("Transaction : " if fr else "Transaction: ") + r.transaction, "", ""))
    lines.append((("Caisse 03" if fr else "Till 03"), "", ""))
    lines.append(rule)
    for desc, q, u, t in r.items:
        lines.append((desc[:34], "", ""))
        lines.append((f"  {q} x {fmt(u, r.lang)}", fmt(t, r.lang), ""))
    lines.append(rule)
    lines.append(("Sous-total" if fr else "Subtotal", fmt(r.subtotal, r.lang), ""))
    for label, amount in r.taxes:
        lines.append((label, fmt(amount, r.lang), ""))
    cur = f"{fmt(r.total, r.lang)} $" if fr else f"{r.currency} {fmt(r.total, r.lang)}"
    lines.append(("TOTAL", cur, "bold"))
    lines.append(rule)
    lines.append((r.payment, fmt(r.total, r.lang), ""))
    lines += [("", "", ""), ("Merci! Gardez ce reçu pour les" if fr else "Thank you! Keep this receipt", "", "center"),
              ("retours et la garantie." if fr else "for returns and warranty.", "", "center"),
              (NOTE_FR if fr else NOTE, "", "small")]
    return lines


TILL_STEP = 12.5


def till_cut(r: Receipt, word: str, top: bool = False) -> float:
    """The share of a till receipt to cut off so that the row starting with `word` and every row
    below it are gone (a photo that missed the bottom of the receipt), or, with top=True, every row
    above it (a photo that missed the top)."""
    lines = till_lines(r)
    i = next(k for k, (left, _, _) in enumerate(lines) if left.startswith(word))
    height = 18 * mm + TILL_STEP * len(lines)
    if top:
        return (12 * mm + (i - 1) * TILL_STEP + 4) / height
    return 1 - (12 * mm + i * TILL_STEP - 11) / height


def till_pdf(r: Receipt) -> bytes:
    """A narrow till receipt (80 mm), Courier, one page."""
    lines = till_lines(r)
    width, step = 80 * mm, TILL_STEP
    height = 18 * mm + step * len(lines)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height), invariant=1)
    c.setTitle(f"Receipt {r.order_number or r.transaction}")
    y = height - 12 * mm
    for left, right, style in lines:
        if style == "title":
            c.setFont("Courier-Bold", 14)
            c.drawCentredString(width / 2, y, left)
        elif style == "center":
            c.setFont("Courier", 8.5)
            c.drawCentredString(width / 2, y, left)
        elif style == "small":
            c.setFont("Courier", 5.5)
            c.drawCentredString(width / 2, y, left)
        else:
            c.setFont("Courier-Bold" if style == "bold" else "Courier", 9)
            c.drawString(5 * mm, y, left)
            if right:
                c.drawRightString(width - 5 * mm, y, right)
        y -= step
    c.showPage()
    c.save()
    return buf.getvalue()


def online_pdf(r: Receipt) -> bytes:
    """A letter-size order confirmation with an item table."""
    fr = r.lang == "fr"
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, invariant=1)
    c.setTitle(f"Order {r.order_number}")
    w, h = letter
    c.setFillColorRGB(0.13, 0.36, 0.25)
    c.rect(0, h - 70, w, 70, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, h - 45, "Larkfield")
    c.setFont("Helvetica", 11)
    c.drawRightString(w - 50, h - 45, "Confirmation de commande" if fr else "Order confirmation")
    c.setFillColorRGB(0, 0, 0)
    y = h - 110
    c.setFont("Helvetica", 10)
    rows = [("N° de commande" if fr else "Order number", r.order_number or "")]
    if r.show_date:
        rows.append(("Date de commande" if fr else "Order date", r.date_text()))
    rows += [("Client" if fr else "Customer", f"C-{int(r.transaction[-3:]):04d}"), ("Paiement" if fr else "Payment", r.payment)]
    for k, v in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, k)
        c.setFont("Helvetica", 10)
        c.drawString(170, y, v)
        y -= 16
    y -= 20
    cols = [50, 330, 400, 480]
    heads = ["Article", "Qté", "Prix unitaire", "Montant"] if fr else ["Item", "Qty", "Unit price", "Amount"]
    c.setFont("Helvetica-Bold", 10)
    c.drawString(cols[0], y, heads[0])
    c.drawRightString(cols[1] + 30, y, heads[1])
    c.drawRightString(cols[2] + 60, y, heads[2])
    c.drawRightString(w - 50, y, heads[3])
    c.line(50, y - 5, w - 50, y - 5)
    y -= 22
    c.setFont("Helvetica", 10)
    for desc, q, u, t in r.items:
        c.drawString(cols[0], y, desc)
        c.drawRightString(cols[1] + 30, y, str(q))
        c.drawRightString(cols[2] + 60, y, fmt(u, r.lang))
        c.drawRightString(w - 50, y, fmt(t, r.lang))
        y -= 18
    c.line(330, y + 8, w - 50, y + 8)
    y -= 8
    summary = [("Sous-total" if fr else "Subtotal", r.subtotal)]
    if r.shipping is not None:
        summary.append(("Livraison" if fr else "Shipping", r.shipping))
    summary += list(r.taxes)
    for label, amount in summary:
        c.drawString(360, y, label)
        c.drawRightString(w - 50, y, fmt(amount, r.lang))
        y -= 16
    c.setFont("Helvetica-Bold", 12)
    c.drawString(360, y - 4, f"Total ({r.currency})")
    c.drawRightString(w - 50, y - 4, (fmt(r.total, r.lang) + " $") if fr else ("$" + fmt(r.total, r.lang)))
    c.setFont("Helvetica", 8)
    c.drawString(50, 60, "Retours : 45 jours. Voir la politique de retour." if fr else "Returns: 45 days. See the returns policy at larkfield.example/returns.")
    c.drawString(50, 48, NOTE_FR if fr else NOTE)
    c.showPage()
    c.save()
    return buf.getvalue()


def partner_pdf(r: Receipt) -> bytes:
    """A receipt from another shop, with its own layout and words (the rules do not know it)."""
    width = 76 * mm
    lines = 16 + 2 * len(r.items)
    height = 20 * mm + 12 * lines
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height), invariant=1)
    c.setTitle("Sales slip")
    y = height - 12 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "MAPLE & PINE")
    y -= 12
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, y, "HARDWARE  -  Kingston ON")
    y -= 12
    c.drawCentredString(width / 2, y, "Larkfield partner store")
    y -= 18
    c.setFont("Helvetica", 8.5)
    c.drawString(4 * mm, y, f"INV# {r.transaction.replace('-', '')}")
    if r.show_date:
        c.drawRightString(width - 4 * mm, y, r.date_text())
    y -= 16
    c.drawString(4 * mm, y, "QTY  DESCRIPTION")
    c.drawRightString(width - 4 * mm, y, "PRICE")
    y -= 4
    c.line(4 * mm, y, width - 4 * mm, y)
    y -= 12
    for desc, q, u, t in r.items:
        c.drawString(4 * mm, y, f"{q:>2}   {desc}")
        c.drawRightString(width - 4 * mm, y, f"{t:.2f}")
        y -= 11
        c.setFont("Helvetica", 7)
        c.drawString(10 * mm, y, f"@ {u:.2f} ea")
        c.setFont("Helvetica", 8.5)
        y -= 12
    c.line(4 * mm, y + 6, width - 4 * mm, y + 6)
    y -= 6
    for label, amount in [("MERCH", r.subtotal), *r.taxes]:
        c.drawString(20 * mm, y, label)
        c.drawRightString(width - 4 * mm, y, f"{amount:.2f}")
        y -= 12
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y - 2, "AMOUNT DUE")
    c.drawRightString(width - 4 * mm, y - 2, f"{r.total:.2f}")
    y -= 18
    c.setFont("Helvetica", 8.5)
    c.drawString(4 * mm, y, f"TENDER {r.payment.upper()}")
    y -= 16
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(width / 2, y, NOTE)
    c.showPage()
    c.save()
    return buf.getvalue()


def printed_lines(pdf: bytes) -> list[str]:
    """Every line of text printed on the receipt, top to bottom (to measure how well OCR reads it)."""
    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf)) as doc:
        return [ln for p in doc.pages for ln in (p.extract_text() or "").splitlines() if ln.strip()]


def receipt_pdf(r: Receipt) -> bytes:
    return {"till": till_pdf, "online": online_pdf, "partner": partner_pdf}[r.layout](r)


# ---------------------------------------------------------------- images: render, scan, photo

def render(pdf: bytes, dpi: int = 200, page: int = 0, gray: bool = False) -> Image.Image:
    doc = pdfium.PdfDocument(pdf)
    try:
        img = doc[page].render(scale=dpi / 72, grayscale=gray).to_pil()
    finally:
        doc.close()
    return img.convert("L" if gray else "RGB")


def _noise(img: Image.Image, rng: np.random.Generator, amount: float) -> Image.Image:
    a = np.asarray(img).astype(np.float32)
    a += rng.normal(0, amount, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), img.mode)


def scan(pdf: bytes, seed: int, dpi: int = 150, angle: float = 1.0, blur: float = 0.6, fade: float = 1.0,
         noise: float = 6.0, turn: int = 0, on_page: bool = True) -> Image.Image:
    """A flatbed scan: the receipt on a letter page, a little crooked, blurred, faded and noisy."""
    rng = np.random.default_rng(seed)
    rec = render(pdf, 200, gray=True)
    if on_page and rec.width < 900:  # a small receipt lies somewhere on the scanner glass
        pagew, pageh = int(8.5 * 200), int(11 * 200)
        sheet = Image.new("L", (pagew, pageh), 246)
        x = int(rng.integers(120, max(121, pagew - rec.width - 120)))
        y = int(rng.integers(100, max(101, pageh - rec.height - 100)))
        sheet.paste(rec, (x, y))
        rec = sheet
    img = rec.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=246)
    if turn:
        img = img.rotate(turn, expand=True)
    if fade != 1.0:
        img = ImageEnhance.Contrast(img).enhance(fade)
        img = ImageEnhance.Brightness(img).enhance(1 + (1 - fade) * 0.35)
    img = img.resize((max(1, img.width * dpi // 200), max(1, img.height * dpi // 200)), Image.LANCZOS)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return _noise(img, rng, noise)


def _perspective_coeffs(src: list[tuple[float, float]], dst: list[tuple[float, float]]) -> list[float]:
    """Coefficients for Image.transform(PERSPECTIVE) that map output points dst to input points src."""
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    a = np.array(m, dtype=float)
    b = np.array(src, dtype=float).reshape(8)
    return list(np.linalg.solve(a, b))


def photo(pdf: bytes, seed: int, tilt: float = 0.06, angle: float = 4.0, shadow: float = 0.35, blur: float = 0.8,
          crop_bottom: float = 0.0, crop_top: float = 0.0, dark: float = 1.0,
          size: tuple[int, int] = (1200, 1600)) -> Image.Image:
    """A phone photo: the receipt on a table, seen at an angle, with a shadow, cropped by the frame."""
    rng = np.random.default_rng(seed)
    rec = render(pdf, 170)
    if crop_bottom or crop_top:
        rec = rec.crop((0, int(rec.height * crop_top), rec.width, int(rec.height * (1 - crop_bottom))))
    W, H = size
    bg = np.zeros((H, W, 3), np.float32)
    base = np.array([150, 120, 88], np.float32) + rng.normal(0, 6, 3)
    grain = np.sin(np.linspace(0, 60, W))[None, :, None] * 8 + rng.normal(0, 5, (H, W, 1))
    bg[:] = base + grain
    table = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    scale = min((W * 0.78) / rec.width, (H * 0.86) / rec.height)
    rec = rec.resize((int(rec.width * scale), int(rec.height * scale)), Image.LANCZOS)
    x0, y0 = (W - rec.width) // 2, (H - rec.height) // 2
    if crop_bottom:
        y0 = H - rec.height  # the receipt runs off the bottom of the frame
    if crop_top:
        y0 = int(tilt * H * 0.4) + 12  # the receipt starts at the top of the frame
    mask = Image.new("L", rec.size, 255)
    table.paste(rec, (x0, y0), mask)
    # Perspective: the top edge looks shorter than the bottom (the phone is held at an angle).
    dx, dy = tilt * W, tilt * H * 0.4
    dst = [(0, 0), (W, 0), (W, H), (0, H)]
    src = [(dx, dy), (W - dx * 0.7, dy * 0.6), (W, H), (0, H)]
    img = table.transform((W, H), Image.PERSPECTIVE, _perspective_coeffs(src, dst), Image.BICUBIC)
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=(120, 96, 70))
    # A soft shadow from the phone and the hand, across one corner.
    yy, xx = np.mgrid[0:H, 0:W]
    shade = 1 - shadow * np.clip(1 - (xx / W + yy / H) * 0.9, 0, 1)
    a = np.asarray(img).astype(np.float32) * shade[..., None] * dark
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return _noise(img, rng, 4.0)


def jpeg(img: Image.Image, quality: int = 82) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=False, progressive=False)
    return buf.getvalue()


def png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=False)
    return buf.getvalue()


def image_pdf(images: list[Image.Image], dpi: int, title: str = "Scan") -> bytes:
    """A PDF whose pages are only pictures: a scanner's PDF has no text layer."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)
    c.setTitle(title)
    for img in images:
        w, h = img.width * 72 / dpi, img.height * 72 / dpi
        c.setPageSize((w, h))
        from reportlab.lib.utils import ImageReader

        b = io.BytesIO(jpeg(img, 80))
        c.drawImage(ImageReader(b), 0, 0, w, h)
        c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------- policies (two columns, footnotes)

def _md_blocks(text: str) -> list[tuple[str, str]]:
    body = text.split("---", 2)[2] if text.startswith("---") else text
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                out.append(("title", line[2:]))
            elif line.startswith("## "):
                out.append(("h2", line[3:]))
            elif line.startswith("- "):
                out.append(("li", line[2:]))
            else:
                out.append(("p", line))
    return out


def _wrap(c: canvas.Canvas, text: str, font: str, size: float, width: float) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def policy_pdf(source: Path, footnotes: dict[str, str], header: str, rotated_table: list[list[str]] | None = None) -> tuple[bytes, dict]:
    """A policy in two columns with a running header, page numbers and footnotes.

    Returns the PDF and its truth: the sections in reading order with their paths and pages."""
    blocks = _md_blocks(source.read_text(encoding="utf-8"))
    w, h = letter
    margin, gap = 54, 24
    colw = (w - 2 * margin - gap) / 2
    top, bottom = h - 110, 110
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, invariant=1)
    c.setTitle(header)
    page, col, y = 1, 0, top
    title = ""
    sections: list[dict] = []
    path: list[str] = []
    marks = iter(["\u00b9", "\u00b2", "\u00b3"])
    pending_notes: list[tuple[str, str]] = []

    def furniture():
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawString(margin, h - 40, header)
        c.drawRightString(w - margin, h - 40, f"Page {page}")
        c.line(margin, h - 46, w - margin, h - 46)
        c.drawString(margin, 40, "Larkfield  ·  " + NOTE.replace(" Not a real receipt.", ""))
        c.setFillColorRGB(0, 0, 0)

    def notes_at_bottom():
        if not pending_notes:
            return
        yy = 70 + 11 * (len(pending_notes) - 1)
        c.line(margin, yy + 12, margin + 120, yy + 12)
        c.setFont("Helvetica", 7.5)
        for mark, note in pending_notes:
            c.drawString(margin, yy, f"{mark} {note}")
            yy -= 11
        pending_notes.clear()

    def next_column():
        nonlocal col, y, page
        if col == 0:
            col, y = 1, top
        else:
            notes_at_bottom()
            c.showPage()
            page += 1
            furniture()
            col, y = 0, top

    furniture()
    for kind, text in blocks:
        if kind == "title":
            title = text
            c.setFont("Helvetica-Bold", 20)
            c.drawString(margin, h - 85, text)
            path = [text]
            continue
        x = margin + col * (colw + gap)
        if kind == "h2":
            path = [title, text]
            font, size, lead, before = "Helvetica-Bold", 13, 17, 12
        elif kind == "li":
            font, size, lead, before = "Helvetica", 11, 15.5, 3
        else:
            font, size, lead, before = "Helvetica", 11, 15.5, 7
        mark = ""
        for key, note in footnotes.items():
            if key in text and all(key != m for m, _ in pending_notes):
                mark = next(marks, "*")
                text = text.replace(key, key + mark, 1)
                pending_notes.append((mark, note))
        indent = 12 if kind == "li" else 0
        lines = _wrap(c, text, font, size, colw - indent)
        need = before + lead * len(lines) + (lead if kind == "h2" else 0)
        if y - need < bottom:
            next_column()
            x = margin + col * (colw + gap)
        y -= before
        sections.append({"kind": kind, "path": list(path), "page": page, "column": col + 1, "text": text})
        c.setFont(font, size)
        for i, line in enumerate(lines):
            if kind == "li" and i == 0:
                c.drawString(x, y - size, "•")
            c.drawString(x + indent, y - size, line)
            y -= lead
    notes_at_bottom()
    c.showPage()
    truth = {"title": title, "sections": sections, "pages": page, "footnotes": footnotes}
    if rotated_table:
        # A wide table printed on a page that is turned a quarter turn in the file (/Rotate 90).
        page += 1
        c.setPageSize(letter)
        c.saveState()
        c.translate(w, 0)
        c.rotate(90)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(60, w - 60, rotated_table[0][0])
        y = w - 100
        widths = [60, 260, 470]
        for r_i, row in enumerate(rotated_table[1:]):
            c.setFont("Helvetica-Bold" if r_i == 0 else "Helvetica", 10)
            for x, cell in zip(widths, row):
                c.drawString(x, y, cell)
            y -= 20
        c.restoreState()
        c.showPage()
        truth["rotated_page"] = {"page": page, "rows": rotated_table[1:]}
        truth["pages"] = page
    c.save()
    pdf = buf.getvalue()
    if rotated_table:
        pdf = _rotate_last_page(pdf)
    return pdf, truth


def _rotate_last_page(pdf: bytes) -> bytes:
    """Store the last page turned (portrait in the file, /Rotate 90), as many scanners and printers do."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf))
    writer = PdfWriter()
    for i, p in enumerate(reader.pages):
        if i == len(reader.pages) - 1:
            p.rotate(90)
        writer.add_page(p)
    writer.add_metadata({"/Title": reader.metadata.get("/Title", "")})
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------------------------------------------------------------- the supplier price list (table on two pages)

PRICE_GROUPS = [
    ("Hose reels", [("HR-30", "Wall hose reel, 30 m", "each", "59.00", "318.60", "6.2"),
                    ("HR-50", "Hose reel cart, 50 m", "each", "119.00", "642.60", "11.8"),
                    ("HR-15C", "Compact reel, 15 m", "each", "34.00", "183.60", "3.1"),
                    ("HR-30P", "Wall reel, 30 m, pro", "each", "79.00", "426.60", "7.4")]),
    ("Hoses", [("HS-15", "Garden hose 15 m", "each", "21.50", "116.10", "1.9"),
               ("HS-25", "Garden hose 25 m", "each", "34.50", "186.30", "3.0"),
               ("HS-50", "Garden hose 50 m", "each", "59.90", "323.46", "5.8"),
               ("HS-25X", "Expandable hose 25 m", "each", "39.00", "210.60", "1.2"),
               ("HS-SOAK", "Soaker hose 15 m", "each", "18.75", "101.25", "1.6"),
               ("HS-CUT", "Hose by the metre", "per m", "1.45", "", "0.12")]),
    ("Nozzles and guns", [("NZ-10", "10-pattern nozzle", "each", "12.99", "70.15", "0.3"),
                          ("NZ-JET", "Jet nozzle, brass", "each", "9.50", "51.30", "0.2"),
                          ("NZ-FAN", "Fan spray nozzle", "each", "7.25", "39.15", "0.2"),
                          ("GUN-PRO", "Spray gun, metal", "each", "24.00", "129.60", "0.5"),
                          ("LANCE-90", "Watering lance 90 cm", "each", "19.95", "107.73", "0.6")]),
    ("Connectors", [("CN-12", "Hose connector 1/2 in", "pack of 3", "6.40", "34.56", "0.1"),
                    ("CN-34", "Hose connector 3/4 in", "pack of 3", "7.10", "38.34", "0.1"),
                    ("CN-STOP", "Stop connector", "pack of 2", "5.80", "31.32", "0.1"),
                    ("CN-BR", "Brass connector set", "set", "15.75", "85.05", "0.4"),
                    ("TAP-2", "Two-way tap adaptor", "each", "11.20", "60.48", "0.2"),
                    ("TAP-4", "Four-way tap adaptor", "each", "18.40", "99.36", "0.3"),
                    ("REP-KIT", "Hose repair kit", "set", "8.95", "48.33", "0.1")]),
    ("Timers and controls", [("TM-1", "Tap timer, one outlet", "each", "39.00", "210.60", "0.4"),
                             ("TM-2", "Tap timer, two outlets", "each", "54.00", "291.60", "0.5"),
                             ("RS-1", "Rain sensor", "each", "29.00", "156.60", "0.2"),
                             ("PR-1", "Pressure reducer", "each", "16.50", "89.10", "0.2")]),
    ("Sprinklers", [("SP-OSC", "Oscillating sprinkler", "each", "27.00", "145.80", "0.9"),
                    ("SP-ROT", "Rotating sprinkler", "each", "19.00", "102.60", "0.5"),
                    ("SP-PUL", "Pulse sprinkler on spike", "each", "23.50", "126.90", "0.7"),
                    ("SP-DRIP", "Drip kit, 20 plants", "kit", "44.00", "237.60", "1.1"),
                    ("SP-MIST", "Misting kit, patio", "kit", "36.00", "194.40", "0.6"),
                    ("SP-TRV", "Travelling sprinkler", "each", "89.00", "480.60", "3.9"),
                    ("SP-HOSE", "Sprinkler hose 7.5 m", "each", "16.00", "86.40", "0.8"),
                    ("SP-BASE", "Sprinkler base, heavy", "each", "12.50", "67.50", "1.0")]),
    ("Spare parts", [("SPR-WASH", "Tap washers (10)", "bag", "3.20", "17.28", "0.05"),
                     ("SPR-ORING", "O-rings for connectors (12)", "bag", "4.10", "22.14", "0.05"),
                     ("SPR-HAND", "Reel handle", "each", "6.75", "36.45", "0.2"),
                     ("SPR-GUIDE", "Hose guide roller", "each", "8.90", "48.06", "0.3"),
                     ("SPR-BRKT", "Wall bracket for HR-30", "each", "14.00", "75.60", "0.9"),
                     ("SPR-WHEEL", "Cart wheel, 20 cm", "each", "11.50", "62.10", "0.6"),
                     ("SPR-SEAL", "Nozzle seal kit", "kit", "5.60", "30.24", "0.05")]),
]


def price_list_pdf() -> tuple[bytes, dict]:
    """A supplier price list whose table continues on page 2 with its header repeated.

    The header has a merged cell ("Price (CAD)" over two columns) and the first column has a
    merged cell per group (the category is printed once per group and per page)."""
    w, h = letter
    x = [40, 150, 220, 375, 440, 505, 572]  # column edges: category, SKU, description, unit, each, case, weight
    rowh = 19
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, invariant=1)
    c.setTitle("AquaFlow trade price list")
    rows_truth, cells = [], []
    page, y = 1, 0

    def header(first: bool):
        nonlocal y
        c.setFont("Helvetica-Bold", 16 if first else 10)
        if first:
            c.drawString(40, h - 60, "AquaFlow Supply  ·  Trade price list for Larkfield")
            c.setFont("Helvetica", 9)
            c.drawString(40, h - 76, "Prices in Canadian dollars, before tax. Valid until 31 March 2027. Case = 6 units.")
            y = h - 100
        else:
            c.drawString(40, h - 50, "AquaFlow Supply  ·  Trade price list (continued)")
            y = h - 70
        c.setFillColorRGB(0.88, 0.92, 0.9)
        c.rect(x[0], y - 2 * rowh, x[-1] - x[0], 2 * rowh, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 9)
        # Two header rows: "Price (CAD)" spans the "Each" and "Case of 6" columns; the other
        # header cells span both rows.
        for i, name in [(0, "Category"), (1, "SKU"), (2, "Description"), (3, "Unit")]:
            c.drawString(x[i] + 4, y - rowh - 5, name)
        c.drawCentredString((x[4] + x[6]) / 2, y - 13, "Price (CAD)")
        c.drawRightString(x[5] - 4, y - 2 * rowh + 6, "Each")
        c.drawRightString(x[6] - 4, y - 2 * rowh + 6, "Case of 6")
        c.line(x[4], y - rowh, x[6], y - rowh)
        for xi in x:
            top = y - rowh if xi == x[5] else y  # no line between "Each" and "Case of 6" in the merged row
            c.line(xi, top, xi, y - 2 * rowh)
        c.line(x[0], y, x[-1], y)
        c.line(x[0], y - 2 * rowh, x[-1], y - 2 * rowh)
        cells.append({"page": page, "kind": "header", "text": "Price (CAD)", "spans": ["each", "case"]})
        y -= 2 * rowh

    header(True)
    c.setFont("Helvetica", 9)
    for cat, rows in PRICE_GROUPS:
        group_top = y
        printed = False
        for r_i, (sku, desc, unit, each, case, kg) in enumerate(rows):
            if y - rowh < 60:
                # close the group's box on this page and continue on the next page
                c.line(x[0], group_top, x[0], y)
                c.line(x[0], y, x[-1], y)
                c.setFont("Helvetica", 8)
                c.drawRightString(x[-1], 45, f"Page {page} of 2  ·  continued on the next page")
                c.showPage()
                page += 1
                header(False)
                c.setFont("Helvetica", 9)
                group_top, printed = y, False
            if not printed:
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x[0] + 4, y - 13, cat if r_i == 0 else f"{cat} (cont.)")
                c.setFont("Helvetica", 9)
                printed = True
            c.drawString(x[1] + 4, y - 13, sku)
            c.drawString(x[2] + 4, y - 13, desc)
            c.drawString(x[3] + 4, y - 13, unit)
            c.drawRightString(x[5] - 4, y - 13, each)
            c.drawRightString(x[6] - 4, y - 13, case or "n/a")
            for xi in x[1:]:
                c.line(xi, y, xi, y - rowh)
            c.line(x[1], y - rowh, x[-1], y - rowh)
            rows_truth.append({"page": page, "category": cat, "sku": sku, "description": desc, "unit": unit,
                               "price_each_cad": each, "price_case_cad": case or None, "weight_kg": kg})
            y -= rowh
        c.line(x[0], group_top, x[0], y)
        c.line(x[0], y, x[1], y)
    c.setFont("Helvetica", 8)
    c.drawString(40, y - 20, "n/a: sold by the metre, no case price. Weights are on the spreadsheet version of this list.")
    c.drawString(40, 45, NOTE.replace("receipt", "price list"))
    c.drawRightString(x[-1], 45, f"Page {page} of 2")
    c.showPage()
    c.save()
    return buf.getvalue(), {"columns": ["category", "sku", "description", "unit", "price_each_cad", "price_case_cad"],
                            "header_rows": 2, "merged": ["Price (CAD) over Each and Case of 6", "Category per group"],
                            "rows": [{k: v for k, v in r.items() if k != "weight_kg"} for r in rows_truth],
                            "pages": page}


def price_sheet_xlsx() -> tuple[bytes, dict]:
    """The same price list as a spreadsheet: units in the headers, a merged title, two sheets."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Prices"
    ws["A1"] = "AquaFlow Supply - trade price list for Larkfield (made up for a course)"
    ws.merge_cells("A1:G1")
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = "Prices before tax. Case = 6 units."
    heads = ["Category", "SKU", "Description", "Unit", "Price each (CAD)", "Price per case (CAD)", "Pack weight (kg)"]
    for i, hd in enumerate(heads, 1):
        ws.cell(row=4, column=i, value=hd).font = Font(bold=True)
    r = 5
    truth = []
    for cat, rows in PRICE_GROUPS:
        first = r
        for sku, desc, unit, each, case, kg in rows:
            ws.cell(row=r, column=2, value=sku)
            ws.cell(row=r, column=3, value=desc)
            ws.cell(row=r, column=4, value=unit)
            ws.cell(row=r, column=5, value=float(each)).number_format = "0.00"
            if case:
                ws.cell(row=r, column=6, value=float(case)).number_format = "0.00"
            else:
                ws.cell(row=r, column=6, value="n/a")
            ws.cell(row=r, column=7, value=float(kg))
            truth.append({"sheet": "Prices", "row": r, "category": cat, "sku": sku, "price_each_cad": each,
                          "price_case_cad": case or None, "weight_kg": kg})
            r += 1
        ws.cell(row=first, column=1, value=cat)
        ws.merge_cells(start_row=first, start_column=1, end_row=r - 1, end_column=1)
    ws.cell(row=r + 1, column=1, value="Notes: weights include packaging.")
    d = wb.create_sheet("Discounts")
    d["A1"], d["B1"] = "Order value (CAD)", "Discount (%)"
    for i, (v, p) in enumerate([("0 - 999.99", 0), ("1000 - 4999.99", 5), ("5000 and more", 8)], 2):
        d.cell(row=i, column=1, value=v)
        d.cell(row=i, column=2, value=p)
    from datetime import datetime

    wb.properties.created = wb.properties.modified = datetime(2026, 9, 1, 9, 0, 0)
    wb.properties.creator = "AquaFlow Supply (made up)"
    buf = io.BytesIO()
    wb.save(buf)
    return _fixed_zip(buf.getvalue()), {"sheets": ["Prices", "Discounts"], "header_row": 4,
                                        "units": {"Price each (CAD)": "CAD", "Price per case (CAD)": "CAD",
                                                  "Pack weight (kg)": "kg"},
                                        "merged": ["A1:G1 (title)", "column A: one category cell per group"],
                                        "rows": truth}


def _fixed_zip(data: bytes) -> bytes:
    """Rewrite a zip (xlsx) with fixed dates, so the same workbook gives the same bytes."""
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for info in src.infolist():
            body = src.read(info.filename)
            if info.filename == "docProps/core.xml":
                body = re.sub(rb"<dcterms:(created|modified)[^>]*>[^<]*</dcterms:\1>",
                              lambda m: m.group(0).split(b">")[0] + b">2026-09-01T09:00:00Z</dcterms:" + m.group(1) + b">", body)
            zi = zipfile.ZipInfo(info.filename, date_time=(2026, 9, 1, 9, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, body)
    return out.getvalue()


# ---------------------------------------------------------------- a mixed document and the bad files

def warranty_claim_pdf(r: Receipt, seed: int) -> bytes:
    """Page 1 is a digital claim form (text layer); page 2 is the customer's scanned receipt (picture only)."""
    from pypdf import PdfReader, PdfWriter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, invariant=1)
    c.setTitle("Warranty claim")
    w, h = letter
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, h - 70, "Larkfield  ·  Warranty claim form")
    c.setFont("Helvetica", 10)
    rows = [("Claim number", "WC-2026-0418"), ("Customer", "C-0022"), ("Product", r.items[0][0]),
            ("Order number", r.order_number or ""), ("Problem", "The motor stops after two minutes."),
            ("Receipt", "attached on page 2")]
    y = h - 110
    for k, v in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, k)
        c.setFont("Helvetica", 10)
        c.drawString(170, y, v)
        y -= 18
    c.setFont("Helvetica", 8)
    c.drawString(50, 48, NOTE.replace("receipt", "form"))
    c.showPage()
    c.save()
    scanned = image_pdf([scan(receipt_pdf(r), seed, dpi=150, angle=-1.2, blur=0.5)], 150)
    writer = PdfWriter()
    for part in (buf.getvalue(), scanned):
        for p in PdfReader(io.BytesIO(part)).pages:
            writer.add_page(p)
    writer.add_metadata({"/Title": "Warranty claim"})
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def encrypted(pdf: bytes, password: str) -> bytes:
    """A password-protected PDF (RC4-128, so the bytes are the same every time)."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf)))
    writer.encrypt(user_password=password, owner_password=password + "-owner", algorithm="RC4-128")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------------------------------------------------------------- the document set

@dataclass
class Doc:
    doc_id: str
    file: str
    kind: str  # receipt | policy | price_list | spreadsheet | claim | bad
    source: str  # digital_pdf | scan_pdf | scan_image | photo | xlsx | mixed_pdf | other
    language: str
    content: bytes
    truth: dict = field(default_factory=dict)
    conditions: dict = field(default_factory=dict)
    expected_intake: str = "accepted"
    pages: int = 1


def build() -> list[Doc]:
    rng = random.Random(SEED)
    docs: list[Doc] = []
    n = 0

    def did() -> str:
        nonlocal n
        n += 1
        return f"D{n:03d}"

    def add(r: Receipt | None, file: str, source: str, content: bytes, conditions: dict | None = None, **kw) -> Doc:
        d = Doc(r.doc_id if r else did(), file, kw.pop("kind", "receipt"), source, r.lang if r else kw.pop("language", "en"),
                content, r.truth() | {"layout": r.layout} if r else kw.pop("truth", {}), conditions or {}, **kw)
        docs.append(d)
        return d

    receipts: dict[str, Receipt] = {}

    def new(layout: str, lang: str = "en", **kw) -> Receipt:
        r = make_receipt(did(), rng, layout, lang, **kw)
        receipts[r.doc_id] = r
        return r

    # 1. Digital receipts: the PDF holds the text (16; 4 in French; 3 without an order number).
    for i in range(16):
        layout = ["till", "online"][i % 2]
        lang = "fr" if i in (3, 8, 11, 14) else "en"
        r = new(layout, lang, with_order=i not in (2, 6, 12))
        add(r, f"receipt-{(r.order_number or 'T' + r.transaction).lower()}.pdf", "digital_pdf", receipt_pdf(r))
    # 2. Partner-store receipts (another shop's layout): 2 digital, 2 scans, 2 photos.
    partner = [new("partner") for _ in range(6)]
    add(partner[0], f"maple-pine-{partner[0].transaction}.pdf", "digital_pdf", receipt_pdf(partner[0]))
    add(partner[1], f"maple-pine-{partner[1].transaction}.pdf", "digital_pdf", receipt_pdf(partner[1]))
    # 3. Scans (16): image-only PDFs and image files, with the conditions a scanner gives.
    scan_specs = [
        dict(dpi=200, angle=0.4, blur=0.4), dict(dpi=150, angle=-1.5, blur=0.6), dict(dpi=150, angle=2.5, blur=0.7),
        dict(dpi=100, angle=-0.8, blur=0.6), dict(dpi=100, angle=1.0, blur=0.9, fade=0.55),
        dict(dpi=75, angle=0.6, blur=0.5), dict(dpi=150, angle=0.0, blur=0.5, turn=90),
        dict(dpi=150, angle=0.3, blur=0.5, turn=180), dict(dpi=150, angle=-3.5, blur=0.6),
        dict(dpi=150, angle=1.2, blur=0.6, fade=0.45, noise=10), dict(dpi=200, angle=-0.5, blur=1.4),
        dict(dpi=150, angle=0.8, blur=0.5), dict(dpi=120, angle=-1.0, blur=0.6), dict(dpi=150, angle=1.8, blur=0.8),
    ]
    for i, spec in enumerate(scan_specs):
        layout = ["till", "online", "till"][i % 3]
        lang = "fr" if i in (2, 7, 12) else "en"
        r = new(layout, lang, with_order=i not in (4, 9))
        img = scan(receipt_pdf(r), seed=100 + i, **spec)
        cond = {k: v for k, v in spec.items()} | {"layout": layout}
        if i % 2 == 0:
            add(r, f"scan{i + 1:04d}.pdf", "scan_pdf", image_pdf([img], spec["dpi"]), cond, pages=1)
        else:
            add(r, f"scan{i + 1:04d}.jpg", "scan_image", jpeg(img, 80), cond)
    for k, p in enumerate(partner[2:4]):
        spec = dict(dpi=150, angle=[1.1, -0.7][k], blur=0.6)
        add(p, f"scan-partner-{k + 1}.jpg", "scan_image", jpeg(scan(receipt_pdf(p), 300 + k, **spec), 80), spec)
    # 4. Phone photos (12, 3 in French), and the hard ones: a cut-off total, an unreadable photo.
    photo_specs = [
        dict(tilt=0.04, angle=3.0), dict(tilt=0.07, angle=-5.0), dict(tilt=0.05, angle=8.0, shadow=0.5),
        dict(tilt=0.08, angle=-2.0, blur=1.2), dict(tilt=0.03, angle=1.0, dark=0.7), dict(tilt=0.06, angle=12.0),
        dict(tilt=0.05, angle=-6.0, shadow=0.55), dict(tilt=0.09, angle=4.0), dict(tilt=0.04, angle=-3.0, blur=1.0),
        dict(tilt=0.06, angle=5.0), dict(tilt=0.05, angle=-1.0, cut_before="TOTAL"),
        dict(tilt=0.07, angle=7.0, blur=9.0, dark=0.35, shadow=0.6),
        dict(tilt=0.04, angle=2.0, cut_top_before="Order"),
    ]
    for i, spec in enumerate(photo_specs):
        lang = "fr" if i in (1, 5, 9) else "en"
        r = new("till" if i % 3 or "cut_before" in spec or "cut_top_before" in spec else "online", lang, with_order=i != 7)
        args = dict(spec)
        if "cut_before" in args:
            # The total and the payment are outside the photo: they cannot be read from this file.
            t = r.truth()
            r_truth_absent = ["total", "payment_method"]
            args["crop_bottom"] = round(till_cut(r, args.pop("cut_before")), 4)
        if "cut_top_before" in args:
            # The shop's name and the date are outside the photo.
            t = r.truth()
            r_truth_absent = ["vendor", "date"]
            args["crop_top"] = round(till_cut(r, args.pop("cut_top_before"), top=True), 4)
        img = photo(receipt_pdf(r), 200 + i, **args)
        d = add(r, f"IMG_{4810 + i * 7}.jpg", "photo", jpeg(img, 78), args | {"layout": r.layout})
        if spec.get("cut_before") or spec.get("cut_top_before"):
            for key in r_truth_absent:
                d.truth["fields"][key] = None
            d.truth["absent"] = sorted(k for k, v in d.truth["fields"].items() if v is None)
            d.truth["printed_but_cut_off"] = r_truth_absent
            d.truth["full_receipt"] = t["fields"]
        if spec.get("blur", 0) > 4:
            d.truth["unreadable"] = True
    for k, p in enumerate(partner[4:6]):
        spec = dict(tilt=0.05, angle=[-4.0, 6.0][k])
        add(p, f"IMG_{5100 + k}.jpg", "photo", jpeg(photo(receipt_pdf(p), 400 + k, **spec), 78), spec)
    # 5. Receipts whose total does not add up (printed wrong): one digital, one scan.
    for k in range(2):
        r = new("till")
        r.total_error = Decimal("10.00") if k == 0 else Decimal("-0.90")
        if k == 0:
            add(r, f"receipt-{r.order_number.lower()}.pdf", "digital_pdf", receipt_pdf(r))
        else:
            add(r, "scan0099.jpg", "scan_image", jpeg(scan(receipt_pdf(r), 99, dpi=150, angle=0.7), 80), {"dpi": 150})
    # 6. Two receipts paid in US dollars (an order from the US store).
    for _ in range(2):
        r = new("online", currency="USD")
        r.taxes = [("Sales tax", Decimal("0.00"))]  # no sales tax on this order: printed as 0.00
        add(r, f"order-us-{r.order_number.lower()}.pdf", "digital_pdf", receipt_pdf(r))
    # 7. Policies (two columns, footnotes; the French one has a page turned a quarter turn).
    pol, ptruth = policy_pdf(SOURCES / "returns-policy.md",
                             {"45 days of delivery": "Business days and weekends both count.",
                              "12.95 dollars": "Prices in Canadian dollars, tax included."},
                             "Larkfield  ·  Returns policy  ·  version 4")
    add(None, "returns-policy-v4.pdf", "digital_pdf", pol, kind="policy", truth=ptruth, pages=ptruth["pages"])
    gar, gtruth = policy_pdf(SOURCES / "garantie-legale-quebec.md",
                             {"usage normal": "Loi sur la protection du consommateur, art. 37 et 38."},
                             "Larkfield  ·  Garantie légale au Québec",
                             rotated_table=[["Durées de garantie Larkfield (exemples)"],
                                            ["Code", "Produit", "Garantie Larkfield"],
                                            ["PW-2200", "Nettoyeur haute pression", "2 ans"],
                                            ["HT-550", "Taille-haie", "2 ans"],
                                            ["BBQ-GR310", "Barbecue au gaz", "3 ans"],
                                            ["KT-180", "Bouilloire électrique", "1 an"]])
    add(None, "garantie-legale-quebec.pdf", "digital_pdf", gar, kind="policy", language="fr", truth=gtruth,
        pages=gtruth["pages"])
    # 8. The supplier price list (PDF, table on two pages) and the same list as a spreadsheet.
    pl, pltruth = price_list_pdf()
    add(None, "aquaflow-price-list.pdf", "digital_pdf", pl, kind="price_list", truth=pltruth, pages=pltruth["pages"])
    xl, xltruth = price_sheet_xlsx()
    add(None, "aquaflow-price-list.xlsx", "xlsx", xl, kind="spreadsheet", truth=xltruth)
    # 9. A mixed document: a digital claim form with the scanned receipt as page 2.
    r = new("till")
    claim = Doc(r.doc_id, "warranty-claim-wc-2026-0418.pdf", "claim", "mixed_pdf", "en",
                warranty_claim_pdf(r, 77), r.truth() | {"layout": "till", "receipt_page": 2,
                                                        "form": {"claim_number": "WC-2026-0418", "customer": "C-0022"}},
                {"page_1": "digital", "page_2": "scan 150 dpi"}, pages=2)
    docs.append(claim)
    # 10. Bad inputs for intake: duplicate, near duplicate, corrupt, password, too big, wrong extension.
    first_pdf = docs[0]
    docs.append(Doc(did(), first_pdf.file.replace(".pdf", " (1).pdf"), "bad", "digital_pdf", first_pdf.language,
                    first_pdf.content, first_pdf.truth | {"duplicate_of": first_pdf.doc_id}, expected_intake="duplicate"))
    scanned = next(d for d in docs if d.source == "scan_image" and d.kind == "receipt")
    rr = receipts[scanned.doc_id]
    docs.append(Doc(did(), "scan-again.jpg", "bad", "scan_image", rr.lang,
                    jpeg(scan(receipt_pdf(rr), 555, dpi=150, angle=-0.9, blur=0.7), 76),
                    rr.truth() | {"layout": rr.layout, "near_duplicate_of": scanned.doc_id}, expected_intake="accepted"))
    r_good = new("online")
    good = receipt_pdf(r_good)
    docs.append(Doc(did(), "receipt-download.pdf", "bad", "other", "en", good[: int(len(good) * 0.55)],
                    r_good.truth() | {"problem": "the file ends in the middle (download stopped)"}, expected_intake="corrupt"))
    r_locked = new("till")
    docs.append(Doc(did(), "receipt-protected.pdf", "bad", "digital_pdf", "en",
                    encrypted(receipt_pdf(r_locked), "larkfield"), r_locked.truth() | {"password": "larkfield"},
                    expected_intake="password"))
    r_big = new("online")
    big_img = scan(receipt_pdf(r_big), 66, dpi=180, angle=0.2, blur=0.3).convert("RGB")
    tiff = io.BytesIO()
    big_img.save(tiff, "TIFF")  # no compression: a scanner's raw file
    docs.append(Doc(did(), "scan-raw.tif", "bad", "scan_image", "en", tiff.getvalue(),
                    r_big.truth() | {"problem": "an uncompressed scan, larger than the limit"}, expected_intake="too_large"))
    r_fake = new("till")
    fake = jpeg(scan(receipt_pdf(r_fake), 67, dpi=150), 80)
    docs.append(Doc(did(), "receipt-scan.pdf", "bad", "scan_image", "en", fake,
                    r_fake.truth() | {"layout": "till", "problem": "a JPEG photo saved with a .pdf name"},
                    expected_intake="wrong_extension"))
    docs.append(Doc(did(), "notes.txt", "bad", "other", "en", b"Customer says the receipt is in the box.\n",
                    {"problem": "not a supported format"}, expected_intake="unsupported"))
    # Number the documents in the order they arrive (D001, D002, ...).
    new_ids = {d.doc_id: f"D{i:03d}" for i, d in enumerate(docs, 1)}
    for d in docs:
        d.doc_id = new_ids[d.doc_id]
        for key in ("duplicate_of", "near_duplicate_of"):
            if key in d.truth:
                d.truth[key] = new_ids[d.truth[key]]
    return docs


def write(out: Path = DATA) -> list[Doc]:
    docs = build()
    folder = out / "documents"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    lines, sums = [], []
    for d in docs:
        (folder / d.file).write_bytes(d.content)
        sha = hashlib.sha256(d.content).hexdigest()
        sums.append(f"{sha}  documents/{d.file}")
        lines.append(json.dumps({"doc_id": d.doc_id, "file": d.file, "kind": d.kind, "source": d.source,
                                 "language": d.language, "pages": d.pages, "bytes": len(d.content), "sha256": sha,
                                 "expected_intake": d.expected_intake, "conditions": d.conditions,
                                 "truth": d.truth}, ensure_ascii=False))
    (out / "truth.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums.append(f"{hashlib.sha256((out / 'truth.jsonl').read_bytes()).hexdigest()}  truth.jsonl")
    (out / "SHA256SUMS.generated").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return docs


def check(out: Path = DATA) -> list[str]:
    """Files whose bytes differ from the course's checksums (data/SHA256SUMS)."""
    expected = (out / "SHA256SUMS").read_text(encoding="utf-8").split("\n")
    got = set((out / "SHA256SUMS.generated").read_text(encoding="utf-8").split("\n"))
    return [line.split("  ", 1)[1] for line in expected if line and line not in got]


def main() -> None:
    ap = argparse.ArgumentParser(description="Make the course's document set in data/.")
    ap.add_argument("--check", action="store_true", help="compare the files with data/SHA256SUMS")
    args = ap.parse_args()
    docs = write()
    kinds: dict[str, int] = {}
    for d in docs:
        kinds[d.kind] = kinds.get(d.kind, 0) + 1
    size = sum(len(d.content) for d in docs)
    print(f"Wrote {len(docs)} documents to data/documents ({size / 1e6:.1f} MB) and data/truth.jsonl")
    print("  " + ", ".join(f"{k} {v}" for k, v in kinds.items()))
    if args.check:
        bad = check()
        if bad:
            print(f"{len(bad)} files differ from the course's files: {', '.join(bad[:5])}")
            print("Your numbers can differ a little. To use the course's files, copy them from the labs repository.")
            raise SystemExit(1)
        print(f"All {len(docs)} files match the course's checksums.")


if __name__ == "__main__":
    main()
