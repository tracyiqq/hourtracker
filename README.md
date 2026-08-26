# Hours Ledger

A single-file web app that works out how many hours you are required to deliver in a given month
— after Hong Kong public holidays, leave and stretch time — and tracks completed task rounds
against that target.

No build step to run it, no dependencies, no backend. Open `index.html` in a browser.

---

## The calculation

```
Base hours          Mondays × 8.000  +  Tue–Fri × 7.750
                    (weekends and public holidays are 0)
× 105%              the target percentage — applies to BASE HOURS ONLY
− leave             full day, or the half-day rate for that leave type
− custom            ad-hoc hours logged against a specific date
− stretch           0.167 h for every day actually attended
= TARGET HOURS REQUIRED
```

Every deduction comes off **after** the percentage is applied, so no deduction is scaled by it.
An hour of leave reduces the target by exactly one hour.

Settings has a switch to flip this to `Before`, giving `(base − deductions) × 105%`. In that mode
each deduction line is shown scaled, which is arithmetically the same thing.

### The target percentage

105% is only a default. It is adjustable in two places:

- **Settings → Default target percentage** — applies to every month that has no figure of its own.
- **Target tab → Target percentage** — sets one month only, leaving every other month alone.
  A slider covering 60%–120% in half-point steps, with a field beside it for typing an exact
  figure. The two stay in sync; decimals work (107.5), and a value outside the slider range is
  accepted from the field with a note saying so. Clearing the field restores the default.

A month with its own percentage says so on the Target tab and in the ledger, which also names the
default it is departing from. "Use the default" clears the override.

Changing the default does **not** rewrite months already saved to history — each record keeps the
percentage it was saved with, so a mid-year change to your target does not falsify past months.

**Progress** is `completed − target`. Short shows red, met shows dark green.

### Leave rates

Leave is two-dimensional: a **type** and a **session**. Each combination has its own rate,
editable in Settings.

| Type | Full day | Mon AM | Mon PM | Tue–Fri AM | Tue–Fri PM |
|---|---|---|---|---|---|
| AL | *base* | 4.750 | 3.750 | 4.250 | 3.500 |
| SL | *base* | 4.750 | 3.750 | 4.250 | 3.500 |
| MA | *base* | 4.750 | 3.500 | 4.250 | **3.250** |
| Other | *base* | 4.750 | 3.750 | 4.250 | 3.500 |

*base* means the day's own base hours, so full-day leave self-adjusts between Monday (8.000) and
Tue–Fri (7.750). New types can be added and appear in the leave picker automatically.

### Stretch time

0.167 h (10 minutes) per **attended** day. A full day of leave is not attended, so no stretch is
deducted. Half-days count as attended by default; a setting turns that off.

### Task rounds

One line per completed round: hours and a name. There is no quantity field — a line counts once.
Use Duplicate for repeated identical rounds.

---

## Using it

Five tabs along the bottom:

- **Target** — the headline figures and the save-to-history button
- **Days** — tap any date to set leave type, session, or custom hours
- **Tasks** — one line per completed round
- **Ledger** — the calculation line by line, with a copy-as-text button
- **History** — months you have chosen to record, with CSV export

Month navigation and Settings sit in the top bar.

**History is manual.** Each month keeps a *draft* that saves continuously as you type, and a
*history record* written only when you press save. Editing a month you already saved does not
change the record until you save again; the status line on the Target tab tells you which state
you are in.

---

## Assumptions that need confirming

Carried from the original specification. Each is one field in Settings.

1. **Monday AM half-day is 4.750 h.** By the clock, 8:45–13:00 is 4.250 h. The other three
   half-day figures reconcile with the clock exactly, so this one is worth a second look.
2. **Tue–Fri AM half-day is 4.250 h** — never specified, derived from 8:45–13:00.
3. **MA morning rates are copies of AL.** Only MA Tue–Fri PM (3.250 h, 14:15–17:30) was given.
   MA Monday PM is set to 3.500 h assuming the same 15-minute shift against a 17:45 finish. The
   MA morning figures are placeholders.

---

## Public holidays

408 dates covering 2023–2046, in two tiers. The distinction matters.

**Gazetted — 2023 to 2027 — 85 dates.** The official general holidays published by the HKSAR
Government on gov.hk.

**Projected — 2028 to 2046 — 323 dates.** Not official. Hong Kong gazettes each year's holidays
roughly 18 months ahead; per the government's 1823 service, 2028 becomes available around
May 2027. These dates were calculated from:

- new moon and solar term times (Meeus, *Astronomical Algorithms* 2nd ed., ch. 25 and 49)
- Chinese calendar month numbering via the winter-solstice and no-principal-term leap rules
- Gregorian Easter (Butcher's algorithm)
- the substitution rules in the General Holidays Ordinance (Cap. 149)

The lunar arithmetic is dependable. What cannot be predicted is a government *decision* — a
one-off holiday, an amended ordinance, a substitution resolved differently. A date can also move
by a day if a new moon falls within minutes of midnight Hong Kong time.

Each holiday's tier is shown when you tap the date, so you always know whether a figure rests on
an official date or a computed one.

### Annual maintenance

When Hong Kong publishes a new year's list, correct that year in `build_app.py` — move its rows
from `PROJECTED` into `GAZETTED` with any fixes — then rebuild. The app's Settings screen can
delete a wrong holiday for a quick fix, but it cannot add or rename one; the source is the
authoritative copy.

> One known discrepancy to check first: a public-holiday aggregator lists Tuen Ng 2028 as
> 27 June, where this project computes 28 May (substituted to 29 May, a Sunday). The difference
> is in how 2028's leap fifth month is handled. The computed date is consistent with Mid-Autumn
> 2028 falling on 3 October.

---

## Repository layout

```
├── .gitignore
├── README.md
├── CONTRIBUTING.md             how to build, test and change the rules safely
├── index.html                  the app — 73 KB, single file, no dependencies
└── src/
    ├── app_template.html       app source; holiday data injected at build time
    ├── build_app.py            injects the holidays, validates, writes index.html
    ├── hk_holidays.py          astronomical engine: derives HK holidays for any year
    ├── holidays_projected.py   generated output of the above, 2028–2046
    └── test_holidays.py        seven checks, no dependencies
```

`index.html` is generated but committed deliberately: it is what a user opens, it has no runtime
dependency, and being at the repository root means any static host serves it without
configuration. Never edit it by hand — the tests fail if it has drifted from the source.

---

## Building from source

Python 3.11+. No third-party packages.

```bash
cd src && python build_app.py
# ../index.html  73 KB
# 408 holidays, 2023-2046  (85 gazetted, 323 projected)
```

`build_app.py` refuses to write a file whose calendar is wrong: it asserts 17 holidays per year,
no date filed under the wrong year, no duplicates, and nothing falling on a Sunday (Sundays are
already general holidays and never appear as named entries).

**Extending past 2046** or changing the substitution rules means regenerating the projections:

```bash
cd src
python -c "
from hk_holidays import hk_general_holidays
with open('holidays_projected.py','w') as f:
    f.write('PROJECTED = {\n')
    for y in range(2028, 2051):
        f.write(f'{y}: {[(d.isoformat(), n) for d, n in hk_general_holidays(y)]!r},\n')
    f.write('}\n')
"
python build_app.py
```

`hk_holidays.py` has no dependencies either — the astronomy is implemented directly.

---

## Tests

```bash
cd src && python test_holidays.py
```

```
PASS  algorithm reproduces all 85 gazetted dates (2023–2027)
PASS  Lunar New Year matches 11 independently known years
PASS  holiday table structure — 408 dates, 2023–2046, 17 per year, none on a Sunday
PASS  tiers flagged correctly — 85 gazetted, 323 projected
PASS  index.html matches a fresh build from source
PASS  no network calls in the built app
PASS  target arithmetic at 6 percentages (60%–120%)
```

Exits non-zero on failure, so it drops straight into a pre-commit hook or a CI job. The first
check is the one that matters: if the algorithm stops reproducing the officially published dates,
the 323 projected dates cannot be trusted either.

---

## Verification

Claims worth trusting only because they were tested:

| Check | Result |
|---|---|
| Gazetted holidays reproduced by the algorithm | 85 / 85 exact, including the 2023 Sunday-LNY substitution and the 2026 Ching Ming / Easter Monday collision |
| Lunar New Year vs independently known dates | 11 / 11 (2023–2033) |
| Projected years structural check | 19 years × 17 holidays, none on a Sunday, no duplicates |
| Monthly targets vs an independent implementation | 12 / 12 months of 2026 to the cent |
| Leave rate combinations | 8 / 8, incl. MA PM 3.250 vs SL PM 3.500 on identical Tuesdays |
| Legacy record migration | totals preserved exactly when rounds-with-quantity expand to one line each |
| Target percentage override | 10 / 10 values from 60% to 130%, incl. decimals and blank fallback, match hand calculations |
| Build reproducibility | `build_app.py` output byte-identical to the shipped file |

Worked example — August 2026, no leave: base 164.000 → ×105% = 172.200 → −3.507 stretch =
**168.693**. The same month at 110% gives **176.893**, at 100% gives **160.493**. March 2026 with
mixed leave types: **139.498**.

---

## Data and privacy

Nothing leaves the device. No network calls, no analytics, no backend.

Everything is stored in local browser storage under the `hoursledger:` prefix. Two consequences:

- **Clearing browser data erases your history.** Export the CSV from the History tab periodically.
- **Nothing syncs between devices.** Each browser keeps its own copy.

---

## Hosting

The repository is deployment-ready: `index.html` sits at the root with no build step, no
dependencies and no server-side anything, so any static host serves it as-is. Once it has a URL,
Safari → Share → Add to Home Screen gives a full-screen icon — the meta tags for that are already
in place.

**Turning hosting on has to go through a company-managed environment.** Do not publish this to a
personal GitHub Pages, Netlify or Vercel account, and do not register one with a work email
address. The approved routes are the company Cloudflare or Render enterprise setup, Apps Script
on the company Workspace, or another environment already approved for the team.

Raise it in `#cell_ai_native_working` or `#cell_security`, stating the service, purpose, data
involved, permissions needed and target environment. It is a light request — one static file, no
backend, no secrets, no data leaving the device — but it goes through the same gate as anything
else.

Until it has a URL: open `index.html` from the Files app on iOS, or from wherever you keep it.

---

## Changelog

| Change | Effect |
|---|---|
| Percentage applies to base hours only | every deduction now off after the percentage; leave is worth face value |
| Target percentage adjustable per month | slider 60–120% plus a typed field; a default in Settings, overridable per month; saved history keeps its own figure |
| Leave split into type × session | MA, SL and AL can differ on the same weekday |
| Rounds quantity removed | one task line = one round |
| Three decimal places | stretch time no longer hides in rounding |
| Red / dark green status | short vs met, on the target ring, ledger and history |
| Holidays extended to 2046 | 85 gazetted + 323 projected |
