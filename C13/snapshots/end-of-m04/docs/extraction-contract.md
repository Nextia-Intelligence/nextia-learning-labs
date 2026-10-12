# Extraction contract: receipts (receipt-v1)

The pipeline returns one record per receipt. Every field has a **status**: `found` (printed on the
document), `inferred` (not printed, but follows from something printed) or `absent` (not on the
document, with a reason). A value is never guessed: `absent` is a correct answer when the document
does not show the value.

**Evidence.** Every `found` or `inferred` value keeps where it came from: the file, the page and the
box `[x0, top, x1, bottom]` with its unit (`pt` = 1/72 inch on a PDF page, `px` = pixels of an image
file). For a spreadsheet: the sheet and the cell (`Prices!E12`).

| Field | Kind | Required | May be absent because | Format |
|---|---|---|---|---|
| `vendor` | text | yes | unreadable | the shop's registered name: Larkfield, Maple & Pine Hardware |
| `order_number` | code | no | not_printed, cut_off, unreadable | `LK-` and 6 digits. In-store receipts have a transaction number instead: never put it here |
| `date` | date | yes | cut_off, unreadable | `YYYY-MM-DD`. Receipts from Quebec print the day first: 09/08/2026 is 2026-08-09 |
| `currency` | code | yes | unreadable | `CAD` or `USD`. A shop in Canada that prints only `$` or no symbol: `CAD`, status `inferred` |
| `subtotal` | money | yes | cut_off, unreadable | 2 decimals, a point, no thousands separator: `1011.78` |
| `shipping` | money | no | not_printed, cut_off, unreadable | till receipts have no shipping line: absent, counts as 0.00 |
| `tax` | money | yes | cut_off, unreadable | the sum of all tax lines (GST, HST, PST, QST, TPS, TVQ) |
| `total` | money | yes | cut_off, unreadable | the amount paid |
| `payment_method` | enum | no | not_printed, cut_off, unreadable | Visa, Mastercard, Amex, Debit or Cash; never the card number |

**Items** (a list, one entry per printed item line): `description` (as printed), `quantity` (a whole
number), `unit_price` and `line_total` (2 decimals).

**Checks** (validate.py): every required field is present; the date is a real date, not after today;
`subtotal + shipping + tax = total` (to the cent); the tax rate is a Canadian sales tax rate (a
warning); the currency is CAD or USD (USD is a warning: convert before a refund); the order number has
the right format; the item lines add up to the subtotal (a warning).
