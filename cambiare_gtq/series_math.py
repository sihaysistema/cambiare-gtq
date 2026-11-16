# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Pure helpers for bundled rates, Precyos, Bisq, and conversion.

No Frappe import. A rate is quetzales (or the other currency) per 1 unit of
the from currency: amount_to = amount_from * rate.
"""

from __future__ import unicode_literals

import datetime
from decimal import Decimal, ROUND_HALF_UP

PRECYOS_ITEM = "64.15.15.05.001"
PRECYOS_URL = (
    "https://precyos.com/api/method/precyos.api.series?item_code=" + PRECYOS_ITEM
)
BISQ_URL = "https://markets.bisq.network/api/trades"
IGNORED_PRECYOS_DATES = frozenset(["2009-10-05", "2010-05-22"])
BTC_HISTORY_START = "2010-08-18"
SOURCE_BANGUAT = "Banguat"
SOURCE_PRECYOS = "Precyos"
SOURCE_BISQ = "Bisq median"
OWNED_SOURCES = frozenset([SOURCE_PRECYOS, SOURCE_BISQ])
RATE_QUANT = Decimal("0.000000001")


def median(values):
    """Median of a non-empty sequence. Even counts use the mean of the two middle values."""
    ordered = sorted(Decimal(str(value)) for value in values)
    count = len(ordered)
    if not count:
        return None
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal(2)


def quantize_rate(value):
    return Decimal(str(value)).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)


def decimal_string(value):
    """Plain decimal string, no scientific notation."""
    text = format(quantize_rate(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text


def utc_day(epoch_ms):
    """UTC calendar date of a Bisq trade_date in milliseconds."""
    stamp = datetime.datetime.fromtimestamp(float(epoch_ms) / 1000.0, datetime.timezone.utc)
    return stamp.date()


def precyos_usd_points(points):
    """BTC/USD prints from Precyos, dropping the two isolated pre-history dates."""
    kept = []
    for point in points or []:
        day = point.get("date")
        if not day or day in IGNORED_PRECYOS_DATES or day < BTC_HISTORY_START:
            continue
        usd = Decimal(str(point.get("usd")))
        if usd <= 0:
            continue
        kept.append((day, usd))
    kept.sort()
    return kept


def asof_rate(dated_rates, day):
    """Latest rate on or before ``day``. ``dated_rates`` maps dates to Decimals."""
    chosen = None
    chosen_day = None
    for rate_day, rate in dated_rates.items():
        if rate_day <= day and (chosen_day is None or rate_day > chosen_day):
            chosen = rate
            chosen_day = rate_day
    return chosen


def btc_gtq(btc_usd, usd_gtq):
    """1 BTC in quetzales = BTC/USD times the as-of Banguat venta."""
    return Decimal(str(btc_usd)) * Decimal(str(usd_gtq))


def bridge_rate(from_to_gtq, to_to_gtq):
    """Cross rate through GTQ. 1 FROM = (GTQ per FROM) / (GTQ per TO) of TO."""
    return Decimal(str(from_to_gtq)) / Decimal(str(to_to_gtq))


def trades_by_utc_day(trades):
    """Group Bisq trades by the UTC day they printed. Price is BTC in USD."""
    grouped = {}
    for trade in trades or []:
        day = utc_day(trade["trade_date"])
        grouped.setdefault(day, []).append(Decimal(str(trade["price"])))
    return {day: median(prices) for day, prices in grouped.items() if prices}


def page_bisq(fetch_page, start_date, end_date, pause):
    """Walk Bisq pages of at most 2000 trades. ``pause`` is called between pages.

    ``fetch_page(timestamp_from_seconds, timestamp_to_seconds)`` returns trades
    sorted ascending. The next page starts one second after the last trade_date.
    """
    start_ts = _utc_midnight(start_date)
    end_ts = _utc_midnight(end_date + datetime.timedelta(days=1))
    cursor = start_ts
    collected = []
    while cursor < end_ts:
        page = list(fetch_page(cursor, end_ts) or [])
        if not page:
            break
        collected.extend(page)
        last_ms = max(int(trade["trade_date"]) for trade in page)
        next_cursor = (last_ms // 1000) + 1
        if next_cursor <= cursor or len(page) < 2000:
            break
        cursor = next_cursor
        pause()
    return collected


def _utc_midnight(day):
    stamp = datetime.datetime(day.year, day.month, day.day, tzinfo=datetime.timezone.utc)
    return int(stamp.timestamp())
