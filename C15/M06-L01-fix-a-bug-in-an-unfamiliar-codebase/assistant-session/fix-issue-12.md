# Recorded session: fix issue 12 in delivery-slots

| | |
|---|---|
| Case study | Fix a bug in an unfamiliar codebase |
| Assistant | Aider 0.86.2 (open source, Apache-2.0), in a terminal |
| Model | `chat-strong`, the larger model (gpt-6.1-sol-2026-09-29), on Azure |
| Settings | Aider edit format `diff`; default temperature; repository map on; edits applied to the files, no commits; shell commands not allowed; the test command `python -m pytest -q` only in turn 3; every question from Aider answered yes |
| Project | `delivery-slots`, the starter, with its Git history |
| Checks run after each turn | `python -m pytest`, ruff, and the area table (12 postal codes; the case study's step "Compare the fixes") |
| Model calls, tokens, cost | 7 calls; 36,069 tokens in, 2,701 out; US$0.0992 at the deployment's price per token (you pay nothing to read this transcript) |

A different run, another model or another assistant can give a different answer. The folder path is shown as `~/projects/delivery-slots`. Aider prints the lines "Analytics have been permanently disabled" and "Detected dumb terminal" because of the recording settings.

Before the session: tests: 35 passed in 0.18s · ruff check: pass · ruff format --check: pass · area table: 6 failed, 6 passed in 0.35s

## Turn 1 (ask mode: the assistant may not change files)

Files added to the chat by Amira: none (the assistant sees Aider's map of the repository).

### Prompt

````text
I have never seen this project. The help desk filed this issue:

# Issue 12: no evening slots for H3Z, although the delivery page promises them

Status: open
Reported by: Grace, help-desk lead

A customer wrote to us on Monday morning. Her email, as she sent it:

> Hello,
>
> Your delivery page says that the west zone gets evening deliveries on Tuesdays
> and Thursdays, 6 to 8 pm. I live in Westmount, H3Z 2Y7, and I work during the
> day. This morning (Monday, about 10 o'clock) I ordered a garden bench, order
> L-40213. For Tuesday the checkout offered me only 8-10, 10-12 and 12-2. No
> evening slot at all. My sister in Notre-Dame-de-Grâce, H4A, has an evening
> delivery booked for tomorrow, so the evening slots do exist.
>
> Can you deliver my bench on Tuesday evening, please?
>
> Solange

What I checked: on the checkout page, `H3Z 2Y7` and Tuesday 20 October show the
same three daytime slots. Monday 10:00 is long before the 20:00 cut-off. The
order L-40213 is paid, and it has no delivery slot yet. I told Solange that we
will come back to her today.

Delphine and Luis are at the trade fair until Friday. Amira (help-desk tools)
said that she can look at it.

Before anyone changes code, I need a map of the project. Please answer from the
repository map:

1. In two or three lines: what does this project do?
2. Each file in delivery_slots/, with one line on what it does.
3. The functions that this command goes through, in order, from cli.py to the
   lines it prints:

       python -m delivery_slots --now 2026-10-19T10:00 slots "H3Z 2Y7" --day 2026-10-20

Do not change any file, and do not guess the cause yet.
````

### What the assistant printed

````text
Analytics have been permanently disabled.
Detected dumb terminal, disabling fancy input and pretty output.

Aider v0.86.2
Model: openai/chat-strong with ask edit format
Git repo: .git with 27 files
Repo-map: using 4096 tokens, auto refresh


delivery_slots/cli.py
## 1. What this project does

This project is a command-line tool for looking up delivery slots by postcode and date, booking an 
order into a slot, and printing a driver’s delivery manifest.  
It reads zone mappings, slot plans, and bookings from CSV files; slot availability accounts for 
bookings and an ordering cutoff.

## 2. Files in `delivery_slots/`

The repository map shows these files, plus the `cli.py` you added:

| File | Purpose |
|---|---|
| `__init__.py` | Package initialization file; its contents have not been supplied. |
| `__main__.py` | Entry point for `python -m delivery_slots`; its exact implementation has not been 
supplied. |
| `cli.py` | Parses command-line arguments, loads the data, runs the requested command, and prints 
results or refusal errors. |
| `bookings.py` | Defines `Booking` and provides functions to load bookings and save a booking. |
| `checkout.py` | Provides the `book()` operation and the `BookingError` exception for refused 
bookings. |
| `manifest.py` | Selects bookings for a day and zone and formats the driver’s manifest. |
| `postcodes.py` | Provides postcode normalization through `normalise()`. |
| `slots.py` | Defines plan rows and slots, loads the slot plan, calculates cutoffs, and finds slots
and their availability. |
| `zones.py` | Loads postcode-to-zone mappings, looks up a postcode’s zone, and defines 
`UnknownPostcode`. |

## 3. Function flow for the command

```sh
python -m delivery_slots --now 2026-10-19T10:00 slots "H3Z 2Y7" --day 2026-10-20
```

Python starts `delivery_slots/__main__.py`. **The handoff from that file to `cli.main()` cannot be 
verified without its contents.** From `cli.main()` onward, the supplied code shows this sequence:

1. **`main()` → `build_parser()` → `parse_args(argv)`**
   - Selects the `slots` command and sets its handler to `cmd_slots`.
   - Parses `--now` using `datetime.fromisoformat`.
   - Parses `--day` using `date.fromisoformat`.
   - Uses the default data folder, `data/`.

2. **`main()` → `load(args.data)`**, which calls, in order:
   - `zones.load_zones(data/zones.csv)`
   - `slots.load_plan(data/slot-plan.csv)`
   - `bookings.load_bookings(data/bookings.csv)`

3. **`main()` → `args.run(...)`**, which is **`cmd_slots(args, data, now)`**:
   - Calls `zones.zone_for("H3Z 2Y7", data.zones)`.
   - Calls `slots.slots_for(zone, day, data.plan, data.bookings, now)`.
   - Calls `normalise(args.postcode)` and prints:
     ```text
     <normalized postcode> is in zone <zone>.
     ```

4. **If no slots are returned:**
   - Calls `day_text(args.day)` and prints:
     ```text
     Zone <zone> has no delivery slots on Tuesday 20 October 2026.
     ```
   - Returns exit code `0`.

5. **Otherwise:**
   - Calls `slots.cutoff_for(args.day)`.
   - Calls `day_text(args.day)` and prints:
     ```text
     Slots on Tuesday 20 October 2026 (orders close <weekday> at <HH:MM>):
     ```
   - For each returned slot, calls `describe(slot)` and prints:
     ```text
       <start>-<end>  <availability>
     ```
   - `describe()` checks `slot.closed`, then `slot.places_left`, to produce `closed`, `full`, `1 
place left`, or `<N> places left`.
   - Returns exit code `0`.

If `UnknownPostcode` or `BookingError` reaches `main()` from the command handler, it prints `Error: 
<message>` to standard error and returns `1`.

The actual zone, slot times, and availability cannot be established from the supplied file contents.
Internal calls within the lookup and slot functions are also not visible in the repository map. No 
files have been changed, and this does not diagnose the issue’s cause.

Tokens: 3.1k sent, 996 received. Cost: $0.02 message, $0.02 session.

delivery_slots/__main__.py

delivery_slots/bookings.py

delivery_slots/checkout.py

delivery_slots/manifest.py

delivery_slots/postcodes.py

delivery_slots/slots.py

delivery_slots/zones.py
You’re right—those files were already supplied in full. My previous answer incorrectly said their 
contents were unavailable.

For the project map and command flow you requested, **no additional files are needed**. We can trace
the command through `__main__.py`, `cli.main()`, data loading, postcode normalization, zone lookup, 
slot calculation, and output formatting.

To establish the command’s **exact printed results**, we would also need:
- `data/zones.csv`
- `data/slot-plan.csv`
- `data/bookings.csv`

`delivery_slots/__init__.py` is the only package file whose contents have not been supplied; add it 
if you want its role confirmed beyond identifying it as the package initialization file.

No changes or diagnosis are needed at this stage.

Tokens: 5.8k sent, 160 received. Cost: $0.01 message, $0.03 session.

data/bookings.csv

data/slot-plan.csv

data/zones.csv

delivery_slots/__init__.py
No additional files are needed for your requested project map and command trace. All package files 
and the three data CSVs are available in the chat.

My earlier statements that some contents were missing were incorrect—sorry for the confusion. I can 
now give the complete function flow and exact printed output without changing files or diagnosing 
the cause.

Tokens: 6.6k sent, 68 received. Cost: $0.01 message, $0.04 session.
````

**After turn 1:** 3 model calls, 15,459 tokens in, 1,224 out (US$0.0432). Changes since the start: 0 files, +0 −0 lines (no file).

Checks: tests: 35 passed in 0.06s · ruff check: pass · ruff format --check: pass · area table: 6 failed, 6 passed in 0.11s

## Turn 2 (ask mode: the assistant may not change files)

Files added to the chat by Amira: `delivery_slots/zones.py`, `delivery_slots/postcodes.py`, `data/zones.csv`.

### Prompt

````text
Targeted questions. For H3Z 2Y7 on Tuesday, the customer was offered 08:00-10:00,
10:00-12:00 and 12:00-14:00. In data/slot-plan.csv, those are the city zone's
slots, not the west zone's.

1. Where in the code is the zone of a postcode decided? Name the function and
   the lines.
2. Walk through that function for "H3Z 2Y7", with the rows of data/zones.csv
   in their order. Which zone does it return, and at which step?
3. Which other areas in data/zones.csv get a wrong zone in the same way?

Answer from the code only. Do not change any file.
````

### What the assistant printed

````text
Analytics have been permanently disabled.
Detected dumb terminal, disabling fancy input and pretty output.

Aider v0.86.2
Model: openai/chat-strong with ask edit format
Git repo: .git with 27 files
Repo-map: using 4096 tokens, auto refresh
Added data/zones.csv to the chat.
Added delivery_slots/postcodes.py to the chat.
Added delivery_slots/zones.py to the chat.
Restored previous conversation history.


data/slot-plan.csv
### 1. Where the zone is decided

In **`delivery_slots/zones.py`, `zone_for()`**, defined at line **28**. The deciding lines are 
**34–37**:

```python
code = normalise(postcode).replace(" ", "")
for area, zone in zones.items():
    if code.startswith(area):
        return zone
```

It returns the zone of the **first matching prefix**, not necessarily the most specific prefix. 
`load_zones()` preserves the CSV row order.

### 2. Walkthrough for `"H3Z 2Y7"`

Line 34 normalizes the postcode and removes spaces, producing `"H3Z2Y7"`.

The first row in `data/zones.csv` is:

```csv
H3,city
```

At line 36, `"H3Z2Y7".startswith("H3")` is `True`. **Line 37 immediately returns `"city"` on the 
first iteration.**

No subsequent rows are checked: `H2Y`, `H2Z`, `H2`, `H3N`, `H4`, `H3T`, `H3Y`, or `H3Z`. In 
particular, the final `H3Z,west` row is never reached.

### 3. Other areas affected

These other explicit mappings are also shadowed by the first `H3,city` row:

| Area | Zone in its CSV row | Zone actually returned |
|---|---|---|
| `H3N` | `north` | `city` |
| `H3T` | `west` | `city` |
| `H3Y` | `west` | `city` |

`H2Y` and `H2Z` are not affected: their specific rows appear before the broader `H2,north` row.

Tokens: 4.0k sent, 532 received. Cost: $0.01 message, $0.01 session.
````

**After turn 2:** 1 model call, 4,047 tokens in, 532 out (US$0.0134). Changes since the start: 0 files, +0 −0 lines (no file).

Checks: tests: 35 passed in 0.08s · ruff check: pass · ruff format --check: pass · area table: 6 failed, 6 passed in 0.05s

## Between turns 2 and 3: Amira's own step (no assistant)

Amira ran the command of the issue (it printed `H3Z 2Y7 is in zone city.`), shrank the input to two rows and one postal code, and wrote the failing test `test_fsa_rows_win` in `tests/test_zones.py`. She committed it: "Add a failing test for issue 12: H3Z 2Y7 is in zone west".

Checks: tests: 4 failed, 35 passed in 0.20s · ruff check: pass · ruff format --check: pass · area table: 6 failed, 6 passed in 0.09s

## Turn 3 (Aider runs the tests after each edit)

Files added to the chat by Amira: `delivery_slots/zones.py`, `tests/test_zones.py`.

### Prompt

````text
I committed a failing test: test_fsa_rows_win in tests/test_zones.py.
It fails four times. For example, zone_for("H3Z 2Y7", zones) returns "city";
expected "west". `python -m pytest -q` prints "4 failed, 35 passed".

Fix zone_for so that these tests pass.
- Change only delivery_slots/zones.py. Do not change the tests or the data.
- Postal codes typed without a space must still work (issue 3,
  test_postcode_without_a_space).
- Keep the change small. In two lines, say why it fixes the cause.
````

### What the assistant printed

````text
Analytics have been permanently disabled.
Detected dumb terminal, disabling fancy input and pretty output.

Aider v0.86.2
Model: openai/chat-strong with diff edit format
Git repo: .git with 27 files
Repo-map: using 4096 tokens, auto refresh
Added delivery_slots/zones.py to the chat.
Added tests/test_zones.py to the chat.
Restored previous conversation history.

Matching longer prefixes first prevents the broad H3 entry from hiding specific FSA mappings.
Postcode normalization stays unchanged, so postcodes without spaces still work.

delivery_slots/zones.py
```python
<<<<<<< SEARCH
    for area, zone in zones.items():
        if code.startswith(area):
            return zone
=======
    for area in sorted(zones, key=len, reverse=True):
        if code.startswith(area):
            return zones[area]
>>>>>>> REPLACE
```

Tokens: 6.4k sent, 183 received. Cost: $0.01 message, $0.01 session.
Applied edit to delivery_slots/zones.py
.......................................                                                      [100%]
39 passed in 0.06s
````

**After turn 3:** 1 model call, 6,376 tokens in, 183 out (US$0.0146). Changes since Amira's commit: 1 files, +2 −2 lines (delivery_slots/zones.py).

Checks: tests: 39 passed in 0.06s · ruff check: pass · ruff format --check: pass · area table: 12 passed in 0.03s

## Turn 4 (ask mode: the assistant may not change files)

Files added to the chat by Amira: `delivery_slots/zones.py`, `tests/test_zones.py`, `data/zones.csv`.

### Prompt

````text
Review your change to zone_for. Give the inputs for which the new zone_for could
still return a wrong zone, or fail in an unexpected way. For each one, say what
it returns now. Do not change any file.
````

### What the assistant printed

````text
Analytics have been permanently disabled.
Detected dumb terminal, disabling fancy input and pretty output.

Aider v0.86.2
Model: openai/chat-strong with ask edit format
Git repo: .git with 27 files
Repo-map: using 4096 tokens, auto refresh
Added data/zones.csv to the chat.
Added delivery_slots/zones.py to the chat.
Added tests/test_zones.py to the chat.
Restored previous conversation history.

With the supplied CSV, **I see no remaining precedence error for valid postcodes**: three-character 
FSA entries now win over two-character entries, regardless of row order.

The remaining edge cases concern invalid postcodes or malformed mappings. `zone_for()` accepts a 
dictionary directly, so callers are not restricted to `load_zones()`.

| Postcode input | Mapping | Result now | Concern |
|---|---|---|---|
| `"H3"` | Supplied CSV | `"city"` | An incomplete postcode is accepted because it matches a prefix.
|
| `"H3Z"` | Supplied CSV | `"west"` | An FSA alone is accepted; the rest of the postcode is not 
required. |
| `"H3ZXYZ"` | Supplied CSV | `"west"` | Invalid trailing characters are not validated. |
| `"H3Z 2Y7"` | `{"H3": "city", "h3z": "west"}` | `"city"` | Directly supplied keys are not 
uppercased, so the lowercase specific entry misses. |
| `"H3Z 2Y7"` | `{"H3": "city", "H3Z ": "west"}` | `"city"` | Directly supplied keys are not 
stripped; the trailing space prevents the specific match. |
| `"K1A 0B1"` | `{"": "west"}` | `"west"` | An empty prefix matches every postcode, including 
otherwise unsupported ones. |
| `"H3Z 2Y7"` | `{3: "city"}` | Raises `TypeError` during sorting | `len()` cannot be applied to an 
integer key. This violates the declared key type. |

The supplied CSV contains none of those malformed keys. `load_zones()` also strips and uppercases 
keys, preventing the lowercase and trailing-space examples when loading through it.

**None of these is a new regression caused by sorting**, though sorting can expose an invalid key 
before any matching entry is returned. The change fixes prefix precedence; it does not add postcode 
or mapping validation. I would need the full `postcodes.py` to assess additional 
normalization-related failures precisely.

Tokens: 4.8k sent, 688 received. Cost: $0.02 message, $0.02 session.

delivery_slots/postcodes.py
No additional files are needed for this review. `postcodes.py`, `zones.py`, `data/zones.csv`, and 
`tests/test_zones.py` are already available.

My previous request for `postcodes.py` was mistaken—sorry. Its `normalise()` function uppercases 
text and collapses whitespace; it does not validate postcode structure.

Tokens: 5.4k sent, 74 received. Cost: $0.01 message, $0.03 session.
````

**After turn 4:** 2 model calls, 10,187 tokens in, 762 out (US$0.0280). Changes since Amira's commit: 1 files, +2 −2 lines (delivery_slots/zones.py).

Checks: tests: 39 passed in 0.05s · ruff check: pass · ruff format --check: pass · area table: 12 passed in 0.02s

## The assistant's change

This is `fix-issue-12.patch`. It applies to the starter after Amira's test commit (`git apply fix-issue-12.patch`).

```diff
diff --git a/delivery_slots/zones.py b/delivery_slots/zones.py
index baea720..5f38063 100644
--- a/delivery_slots/zones.py
+++ b/delivery_slots/zones.py
@@ -32,7 +32,7 @@ def zone_for(postcode: str, zones: dict[str, str]) -> str:
     so the area is matched at the start of the postal code.
     """
     code = normalise(postcode).replace(" ", "")
-    for area, zone in zones.items():
+    for area in sorted(zones, key=len, reverse=True):
         if code.startswith(area):
-            return zone
+            return zones[area]
     raise UnknownPostcode(f"We do not deliver to {normalise(postcode)}.")
```
