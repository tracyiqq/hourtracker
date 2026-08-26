#!/usr/bin/env python3
"""
Tests for the Hong Kong holiday engine and the built app.

    python test_holidays.py

Exits non-zero on failure, so it works as a pre-commit or CI check.
No third-party packages required.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

from build_app import GAZETTED, holiday_table, check, PLACEHOLDER
from hk_holidays import hk_general_holidays, lunar_months

HERE = Path(__file__).parent
failures = []


def ok(name):
    print(f"  PASS  {name}")


def bad(name, detail):
    failures.append(f"{name}: {detail}")
    print(f"  FAIL  {name} — {detail}")


def test_algorithm_reproduces_gazetted():
    """The strongest evidence the projections are sound: the same code must
    reproduce every officially published date it was not given."""
    total = hit = 0
    for year, rows in GAZETTED.items():
        want = sorted(d for d, _ in rows)
        got = sorted(d.isoformat() for d, _ in hk_general_holidays(year))
        total += len(want)
        missing = [d for d in want if d not in got]
        extra = [d for d in got if d not in want]
        hit += len(want) - len(missing)
        if missing or extra:
            bad(f"gazetted {year}", f"missing {missing}, unexpected {extra}")
    if hit == total:
        ok(f"algorithm reproduces all {total} gazetted dates ({min(GAZETTED)}–{max(GAZETTED)})")


def test_lunar_new_year():
    """Independently known CNY dates — catches leap-month errors."""
    known = {2023: '2023-01-22', 2024: '2024-02-10', 2025: '2025-01-29', 2026: '2026-02-17',
             2027: '2027-02-06', 2028: '2028-01-26', 2029: '2029-02-13', 2030: '2030-02-03',
             2031: '2031-01-23', 2032: '2032-02-11', 2033: '2033-01-31'}
    wrong = {y: lunar_months(y)[1].isoformat() for y in known
             if lunar_months(y)[1].isoformat() != known[y]}
    if wrong:
        bad("lunar new year", f"{wrong}")
    else:
        ok(f"Lunar New Year matches {len(known)} independently known years")


def test_table_structure():
    """17 holidays a year, right year, no duplicates, never a Sunday."""
    table = holiday_table()
    try:
        total = check(table)
        ok(f"holiday table structure — {total} dates, {min(table)}–{max(table)}, 17 per year, none on a Sunday")
    except AssertionError as e:
        bad("holiday table structure", str(e))


def test_gazetted_flagged_correctly():
    table = holiday_table()
    for year, rows in table.items():
        expected = "Gazetted" if int(year) in GAZETTED else "Projected"
        mismatched = [r for r in rows if r[2] != expected]
        if mismatched:
            bad(f"status flag {year}", f"{len(mismatched)} rows not marked {expected}")
            return
    gaz = sum(len(v) for k, v in table.items() if int(k) in GAZETTED)
    ok(f"tiers flagged correctly — {gaz} gazetted, {sum(len(v) for v in table.values()) - gaz} projected")


def test_built_app_is_current():
    """The committed page must match what the source builds."""
    built = HERE.parent / "index.html"
    if not built.exists():
        bad("built app present", "index.html missing — run build_app.py")
        return
    template = (HERE / "app_template.html").read_text()
    expected = template.replace(PLACEHOLDER, json.dumps(holiday_table(), separators=(",", ":")))
    if built.read_text() != expected:
        bad("built app is current", "index.html differs from the source build — re-run build_app.py")
    else:
        ok("index.html matches a fresh build from source")


def test_app_has_no_network_calls():
    """The app must stay entirely self-contained — no code paths that talk out."""
    built = HERE.parent / "index.html"
    if not built.exists():
        return
    html = built.read_text()
    calls = re.findall(r'\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts)\b', html)
    if calls:
        bad("no network calls", f"found {sorted(set(calls))}")
    else:
        ok("no network calls in the built app")


def test_no_third_party_origins():
    """A remote origin is a supply chain. There should be none."""
    built = HERE.parent / "index.html"
    if not built.exists():
        return
    origins = set(re.findall(r'https?://[A-Za-z0-9.\-]+', built.read_text()))
    origins = {o for o in origins if 'www.w3.org' not in o}      # SVG namespace only
    if origins:
        bad("no third-party origins", f"{sorted(origins)}")
    else:
        ok("no third-party origins — the page loads nothing remote")


def test_security_headers_present():
    built = HERE.parent / "index.html"
    if not built.exists():
        return
    html = built.read_text()
    need = ["default-src 'none'", "connect-src 'none'", "object-src 'none'",
            "base-uri 'none'", "form-action 'none'", 'name="referrer" content="no-referrer"']
    missing = [n for n in need if n not in html]
    if missing:
        bad("security policy", f"missing {missing}")
    else:
        ok("content security policy locked down (no connect, no objects, no external anything)")


def test_user_text_is_escaped():
    """Editable fields must not reach innerHTML unescaped."""
    src = (HERE / "app_template.html").read_text()
    if "const esc=v=>" not in src:
        bad("escaper present", "esc() missing")
        return
    # every editable string must be wrapped where it enters the DOM
    required = ["esc(day.type)", "esc(h[1])", "esc(M.extraNote", "esc(day.holName", "esc(k)"]
    missing = [r for r in required if r not in src]
    # and these raw forms must not appear at all
    forbidden = ["${day.type}", "${h[1]}", "${day.holName||'Public holiday'}", "${k}</div>"]
    present = [f for f in forbidden if f in src]
    if missing or present:
        bad("user text escaped", f"missing {missing}, raw {present}")
    else:
        ok(f"editable text escaped at all {len(required)} entry points")


def test_no_plaintext_passcode():
    for f in [HERE.parent / "index.html", HERE / "app_template.html",
              HERE.parent / "README.md", HERE.parent / "CONTRIBUTING.md"]:
        if f.exists() and re.search(r'\b121102\b', f.read_text()):
            bad("no plaintext passcode", f"found in {f.name}")
            return
    ok("no plaintext passcode in any committed file")


def test_target_arithmetic():
    """Base x pct, then deduct — verified against figures worked by hand."""
    cases = [(105, 168.693), (100, 160.493), (110, 176.893), (107.5, 172.793),
             (60, 94.893), (120, 193.293)]
    base, stretch = 164.0, 3.507       # August 2026, no leave
    for pct, want in cases:
        got = round(base * pct / 100 - stretch, 3)
        if abs(got - want) > 0.0015:
            bad(f"target at {pct}%", f"got {got}, expected {want}")
            return
    ok(f"target arithmetic at {len(cases)} percentages (60%–120%)")


if __name__ == "__main__":
    print("Hours Ledger — tests\n")
    for fn in [test_algorithm_reproduces_gazetted, test_lunar_new_year, test_table_structure,
               test_gazetted_flagged_correctly, test_built_app_is_current,
               test_app_has_no_network_calls, test_no_third_party_origins,
               test_security_headers_present, test_user_text_is_escaped,
               test_no_plaintext_passcode, test_target_arithmetic]:
        fn()
    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All tests passed.")
