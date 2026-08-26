"""
Derive Hong Kong general holidays for years beyond the gazetted range.

Astronomy from Meeus, 'Astronomical Algorithms' 2nd ed:
  ch.49  phases of the moon (new moon, incl. planetary corrections)
  ch.25  solar coordinates (apparent longitude)
Chinese calendar rules: month begins on the day of the new moon in China
Standard Time (UTC+8); month 11 is the month containing the winter solstice;
a 13-month cycle inserts a leap month at the first month with no principal
term (zhongqi).
Substitution rules: General Holidays Ordinance (Cap. 149).
"""
import math
from datetime import date, timedelta

RAD = math.pi / 180.0
CST = 8.0 / 24.0                      # China Standard Time offset in days


def _dt_seconds(year):
    """Delta T (TD - UT) in seconds; Espenak/Meeus polynomial, 2005-2150."""
    if year < 2050:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    t = year - 1820
    return -20 + 32 * (t / 100.0) ** 2 - 0.5628 * (2150 - year)


def new_moon_jde(k):
    """JDE (TD) of new moon number k. Meeus 49.1 with all corrections."""
    T = k / 1236.85
    T2, T3, T4 = T * T, T ** 3, T ** 4
    jde = (2451550.09766 + 29.530588861 * k
           + 0.00015437 * T2 - 0.000000150 * T3 + 0.00000000073 * T4)
    E = 1 - 0.002516 * T - 0.0000074 * T2
    M = (2.5534 + 29.10535670 * k - 0.0000014 * T2 - 0.00000011 * T3) * RAD
    Mp = (201.5643 + 385.81693528 * k + 0.0107582 * T2
          + 0.00001238 * T3 - 0.000000058 * T4) * RAD
    F = (160.7108 + 390.67050284 * k - 0.0016118 * T2
         - 0.00000227 * T3 + 0.000000011 * T4) * RAD
    Om = (124.7746 - 1.56375588 * k + 0.0020672 * T2 + 0.00000215 * T3) * RAD
    s = math.sin
    jde += (-0.40720 * s(Mp)
            + 0.17241 * E * s(M)
            + 0.01608 * s(2 * Mp)
            + 0.01039 * s(2 * F)
            + 0.00739 * E * s(Mp - M)
            - 0.00514 * E * s(Mp + M)
            + 0.00208 * E * E * s(2 * M)
            - 0.00111 * s(Mp - 2 * F)
            - 0.00057 * s(Mp + 2 * F)
            + 0.00056 * E * s(2 * Mp + M)
            - 0.00042 * s(3 * Mp)
            + 0.00042 * E * s(M + 2 * F)
            + 0.00038 * E * s(M - 2 * F)
            - 0.00024 * E * s(2 * Mp - M)
            - 0.00017 * s(Om)
            - 0.00007 * s(Mp + 2 * M)
            + 0.00004 * s(2 * Mp - 2 * F)
            + 0.00004 * s(3 * M)
            + 0.00003 * s(Mp + M - 2 * F)
            + 0.00003 * s(2 * Mp + 2 * F)
            - 0.00003 * s(Mp + M + 2 * F)
            + 0.00003 * s(Mp - M + 2 * F)
            - 0.00002 * s(Mp - M - 2 * F)
            - 0.00002 * s(3 * Mp + M)
            + 0.00002 * s(4 * Mp))
    A = [(299.77 + 0.107408 * k - 0.009173 * T2, 0.000325),
         (251.88 + 0.016321 * k, 0.000165),
         (251.83 + 26.651886 * k, 0.000164),
         (349.42 + 36.412478 * k, 0.000126),
         (84.66 + 18.206239 * k, 0.000110),
         (141.74 + 53.303771 * k, 0.000062),
         (207.14 + 2.453732 * k, 0.000060),
         (154.84 + 7.306860 * k, 0.000056),
         (34.52 + 27.261239 * k, 0.000047),
         (207.19 + 0.121824 * k, 0.000042),
         (291.34 + 1.844379 * k, 0.000040),
         (161.72 + 24.198154 * k, 0.000037),
         (239.56 + 25.513099 * k, 0.000035),
         (331.55 + 3.592518 * k, 0.000023)]
    for ang, coef in A:
        jde += coef * math.sin(ang * RAD)
    return jde


def jd_to_date(jd):
    """Julian Day (UT) -> Gregorian date, taking the civil day it falls in."""
    jd = jd + 0.5
    z = math.floor(jd)
    f = jd - z
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return date(int(year), int(month), int(day))


def date_to_jd(dt):
    y, m, d = dt.year, dt.month, dt.day
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def sun_apparent_longitude(jde):
    """Apparent geometric longitude of the sun in degrees, Meeus ch.25."""
    T = (jde - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    Mr = M * RAD
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
         + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
         + 0.000289 * math.sin(3 * Mr))
    true_long = L0 + C
    Om = 125.04 - 1934.136 * T
    app = true_long - 0.00569 - 0.00478 * math.sin(Om * RAD)
    return app % 360.0


def solar_term_jde(year, target_deg):
    """JDE (TD) at which apparent solar longitude equals target_deg."""
    # seed: rough day-of-year for the target longitude
    approx = date(year, 3, 20) + timedelta(days=target_deg * 365.2422 / 360.0)
    lo = date_to_jd(approx) - 20
    hi = lo + 40

    def diff(j):
        d = (sun_apparent_longitude(j) - target_deg + 180) % 360 - 180
        return d

    for _ in range(80):
        mid = (lo + hi) / 2
        if diff(lo) * diff(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _local_date(jde, year):
    """TD-based JDE -> civil date in China Standard Time."""
    jd_ut = jde - _dt_seconds(year) / 86400.0
    return jd_to_date(jd_ut + CST)


def winter_solstice_date(year):
    return _local_date(solar_term_jde(year, 270.0), year)


def new_moon_dates(from_date, to_date):
    """All new moon civil dates (CST) in a range, as a sorted list."""
    k0 = math.floor((from_date.year + (from_date.month - 1) / 12.0 - 2000) * 12.3685) - 3
    out = []
    k = k0
    while True:
        jde = new_moon_jde(k)
        d = _local_date(jde, from_date.year)
        if d > to_date:
            break
        if d >= from_date:
            out.append(d)
        k += 1
        if k > k0 + 500:
            break
    return out


def lunar_months(year):
    """
    Map lunar month number -> start date, for the months of the given
    Gregorian year's lunar year (month 1 through month 12).
    Implements the winter-solstice / no-zhongqi leap rule.
    """
    ws_prev = winter_solstice_date(year - 1)
    ws_this = winter_solstice_date(year)
    nms = new_moon_dates(ws_prev - timedelta(days=40), ws_this + timedelta(days=40))
    # month 11 of the previous lunar year starts at the last new moon <= ws_prev
    starts = [d for d in nms if d <= ws_prev]
    m11_prev = starts[-1]
    starts_after = [d for d in nms if d > ws_prev]
    # index of the new moon that starts month 11 of THIS year
    cand = [d for d in nms if d <= ws_this]
    m11_this = cand[-1]

    seq = [d for d in nms if m11_prev <= d <= m11_this]
    n_months = len(seq) - 1                       # months from m11_prev to m11_this
    leap_ok = (n_months == 13)

    def has_zhongqi(start, end):
        """True if a principal term (long. multiple of 30) falls in [start, end)."""
        for deg in range(0, 360, 30):
            # a given longitude occurs once per Gregorian year, but the crossing
            # for a winter longitude sits in the following January/February, so
            # the neighbouring years must both be tried
            for y in (start.year - 1, start.year, start.year + 1):
                d = _local_date(solar_term_jde(y, float(deg)), y)
                if start <= d < end:
                    return True
        return False

    months = {}
    num = 11
    leap_used = False
    for i in range(len(seq) - 1):
        start, nxt = seq[i], seq[i + 1]
        is_leap = False
        if leap_ok and not leap_used and i > 0 and not has_zhongqi(start, nxt):
            is_leap = True
            leap_used = True
        if not is_leap:
            months.setdefault(num, start)
            num = 1 if num == 12 else num + 1
        # a leap month takes the previous month's number and is skipped here
    return months


def lunar_day(year, month, day):
    """Gregorian date of the day-th day of the given lunar month."""
    m = lunar_months(year)
    return m[month] + timedelta(days=day - 1)


def easter(year):
    """Gregorian Easter Sunday (Meeus/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def hk_general_holidays(year):
    """
    The 17 general holidays for a year, with Cap.149 substitution applied.
    Returns a list of (date, name) sorted by date.
    """
    e = easter(year)
    cny1 = lunar_months(year)[1]
    items = []                                    # (date, name, kind)

    items.append((date(year, 1, 1), "The first day of January", "shift"))

    lny = [cny1, cny1 + timedelta(days=1), cny1 + timedelta(days=2)]
    lny4 = cny1 + timedelta(days=3)
    names = ["Lunar New Year's Day", "Lunar New Year 2nd day", "Lunar New Year 3rd day"]
    if any(d.weekday() == 6 for d in lny):        # a LNY day on Sunday -> use day 4
        kept = [(d, n) for d, n in zip(lny, names) if d.weekday() != 6]
        kept.append((lny4, "Lunar New Year 4th day"))
        for d, n in kept:
            items.append((d, n, "fixed"))
    else:
        for d, n in zip(lny, names):
            items.append((d, n, "fixed"))

    ching_ming = _local_date(solar_term_jde(year, 15.0), year)
    items.append((ching_ming, "Ching Ming Festival", "shift"))

    items.append((e - timedelta(days=2), "Good Friday", "fixed"))
    items.append((e - timedelta(days=1), "Day following Good Friday", "fixed"))
    items.append((e + timedelta(days=1), "Easter Monday", "shift"))

    items.append((date(year, 5, 1), "Labour Day", "shift"))
    items.append((lunar_day(year, 4, 8), "Birthday of the Buddha", "shift"))
    items.append((lunar_day(year, 5, 5), "Tuen Ng Festival", "shift"))
    items.append((date(year, 7, 1), "HKSAR Establishment Day", "shift"))

    mid_autumn = lunar_day(year, 8, 15)
    day_after = mid_autumn + timedelta(days=1)
    if day_after.weekday() == 6:                  # day after falls on Sunday
        items.append((mid_autumn, "Chinese Mid-Autumn Festival", "fixed"))
    else:
        items.append((day_after, "Day following Mid-Autumn Festival", "fixed"))

    items.append((date(year, 10, 1), "National Day", "shift"))
    items.append((lunar_day(year, 9, 9), "Chung Yeung Festival", "shift"))
    items.append((date(year, 12, 25), "Christmas Day", "shift"))

    # first weekday after Christmas Day (Sunday is not a weekday)
    d = date(year, 12, 26)
    while d.weekday() == 6:
        d += timedelta(days=1)
    items.append((d, "First weekday after Christmas Day", "boxing"))

    # apply Sunday substitution, cascading onto the next free non-Sunday day
    # (Sunday is itself a general holiday, so it can never serve as a substitute)
    items.sort(key=lambda x: x[0])
    taken = set()
    out = []
    for d, name, kind in items:
        if kind == "shift" and d.weekday() == 6:
            nd = d + timedelta(days=1)
            while nd in taken or nd.weekday() == 6:
                nd += timedelta(days=1)
            out.append((nd, "Day following " + name))
            taken.add(nd)
        else:
            nd = d
            while nd in taken or (nd != d and nd.weekday() == 6):
                nd += timedelta(days=1)
            out.append((nd, name))
            taken.add(nd)
    out.sort()
    return out
