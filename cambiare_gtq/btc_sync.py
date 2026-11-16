# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Refresh BTC/USD and BTC/GTQ.

Precyos (https://precyos.com) is the default source. Its public series is
BTC in USD. BTC/GTQ is that price times the Banguat as-of venta (Precyos has
no public GTQ endpoint). Days Precyos does not publish fall back to the median
of Bisq BTC/USD trades in the 24 hours before 00:00 UTC on that date, which is
how Precyos dates the series. Selecting Bisq in Configuration Cambiare uses
that median for every day in the window. Rows tagged Banguat, or with no
source, are left alone.
"""

from __future__ import unicode_literals

import datetime
import json
import os
from decimal import Decimal

import frappe
import requests
from frappe.utils import getdate, nowdate

from cambiare_gtq.historical import _currency_names, _has_source, ensure_btc_currency
from cambiare_gtq.series_math import (
    BISQ_URL,
    BUNDLE_BTC_LAST,
    PRECYOS_URL,
    SOURCE_BISQ,
    SOURCE_PRECYOS,
    btc_gtq,
    collect_bisq_days,
    days_without_precyos,
    decimal_string,
    default_refresh_start,
    rate_timestamp_utc,
    timestamp_for_column,
    iter_days,
    mapped_rate,
    precyos_usd_points,
    quantize_rate,
    trades_by_utc_day,
)

def selected_btc_source():
    if not frappe.db.exists("DocType", "Configuration Cambiare"):
        return SOURCE_PRECYOS
    try:
        doc = frappe.get_doc("Configuration Cambiare")
    except Exception:
        return SOURCE_PRECYOS
    value = doc.get("btc_rate_source") or SOURCE_PRECYOS
    if value == "Bisq":
        return SOURCE_BISQ
    return SOURCE_PRECYOS


@frappe.whitelist()
def refresh_btc_rates(from_date=None, to_date=None):
    """Recompute BTC pairs for a window.

    With no from-date, the window is the last 14 days. If BTC/USD is still
    missing somewhere after the bundled Precyos series (2026-10-23), the
    window starts at the first missing day so that gap is filled once.
    """
    end = getdate(to_date or nowdate())
    if from_date:
        start = getdate(from_date)
    else:
        start = default_refresh_start(end, _btc_usd_dates(), _bundle_btc_last())
    if start > end:
        frappe.throw(frappe._("From Date must be on or before To Date."))
    ensure_btc_currency()
    result = sync_btc_window(start, end, source=selected_btc_source())
    frappe.db.commit()
    return result


def sync_btc_window(start, end, source=SOURCE_PRECYOS, precyos_points=None, bisq_trades=None):
    """Store BTC/USD and BTC/GTQ. ``source`` is Precyos or Bisq median."""
    if precyos_points is None and source == SOURCE_PRECYOS:
        precyos_points = fetch_precyos_points()
    precyos = {day: rate for day, rate in precyos_usd_points(precyos_points or [])}
    if bisq_trades is None:
        if source == SOURCE_BISQ:
            needed = list(iter_days(start, end))
        else:
            needed = days_without_precyos(start, end, precyos)
        bisq_trades = fetch_bisq_days(needed) if needed else []
    bisq = trades_by_utc_day(bisq_trades or [])
    usd_gtq = _usd_gtq_rates()
    created = updated = kept = empty = 0
    day = start
    while day <= end:
        btc_usd, used = _price_for_day(day, source, precyos, bisq)
        if btc_usd is None:
            empty += 1
            day += datetime.timedelta(days=1)
            continue
        base = _asof(usd_gtq, day)
        if base is None:
            empty += 1
            day += datetime.timedelta(days=1)
            continue
        gtq = btc_gtq(btc_usd, base)
        for fr, to, rate in (
            ("BTC", "USD", btc_usd),
            ("USD", "BTC", quantize_rate(1 / btc_usd)),
            ("BTC", "GTQ", gtq),
            ("GTQ", "BTC", quantize_rate(1 / gtq)),
        ):
            outcome = _store_rate(day, fr, to, rate, used)
            if outcome == "created":
                created += 1
            elif outcome == "updated":
                updated += 1
            else:
                kept += 1
        day += datetime.timedelta(days=1)
    return {
        "from_date": str(start),
        "to_date": str(end),
        "source": source,
        "created": created,
        "updated": updated,
        "kept": kept,
        "empty_days": empty,
    }


def _price_for_day(day, source, precyos, bisq):
    if source == SOURCE_BISQ:
        price = mapped_rate(bisq, day)
        return (price, SOURCE_BISQ) if price is not None else (None, None)
    precyos_price = mapped_rate(precyos, day)
    if precyos_price is not None:
        return precyos_price, SOURCE_PRECYOS
    price = mapped_rate(bisq, day)
    if price is None:
        return None, None
    return price, SOURCE_BISQ


def fetch_precyos_points():
    response = requests.get(PRECYOS_URL, timeout=60)
    response.raise_for_status()
    payload = response.json()
    message = payload.get("message") or payload
    sources = message.get("sources") or {}
    price = sources.get("Precio") or {}
    return price.get("points") or []


def realign_bisq_rates(precyos_points=None):
    """Replace Bisq rows with Precyos where Precyos has that date.

    A Bisq row dated D was the median of trades on UTC day D. Precyos stores
    that median as D+1. Where Precyos publishes D, the row becomes the Precyos
    price. Otherwise the row moves to D+1. An existing row on the destination
    date is kept and the mis-dated row is removed.
    """
    if precyos_points is None:
        precyos_points = fetch_precyos_points()
    precyos = {day: rate for day, rate in precyos_usd_points(precyos_points or [])}
    usd_gtq = _usd_gtq_rates()
    replaced = shifted = removed = 0
    for doctype in ("Currency Exchange GTQ", "Currency Exchange"):
        if not frappe.db.table_exists(doctype):
            continue
        dates = frappe.db.sql(
            """SELECT DISTINCT `date` FROM `tab{0}`
            WHERE rate_source = %s
            ORDER BY `date` DESC""".format(doctype),
            (SOURCE_BISQ,),
        )
        for (day,) in dates:
            day = getdate(day)
            text = day.isoformat()
            if text in precyos:
                replaced += _replace_bisq_with_precyos(doctype, day, precyos[text], usd_gtq)
            else:
                moved, dropped = _shift_bisq_date(doctype, day, day + datetime.timedelta(days=1))
                shifted += moved
                removed += dropped
    return {"replaced": replaced, "shifted": shifted, "removed": removed}


def _replace_bisq_with_precyos(doctype, day, btc_usd, usd_gtq):
    btc_usd = quantize_rate(btc_usd)
    pairs = {
        ("BTC", "USD"): btc_usd,
        ("USD", "BTC"): quantize_rate(Decimal(1) / btc_usd),
    }
    base = _asof(usd_gtq, day)
    if base:
        gtq = quantize_rate(btc_gtq(btc_usd, base))
        pairs[("BTC", "GTQ")] = gtq
        pairs[("GTQ", "BTC")] = quantize_rate(Decimal(1) / gtq)
    updated = 0
    for (fr, to), rate in pairs.items():
        assignments = "exchange_rate = %s, rate_source = %s"
        values = [decimal_string(rate), SOURCE_PRECYOS]
        if doctype == "Currency Exchange GTQ" and frappe.db.has_column(doctype, "rate_timestamp_utc"):
            assignments += ", rate_timestamp_utc = %s"
            values.append(timestamp_for_column(rate_timestamp_utc(day, fr, to)))
        values.extend([day.isoformat(), fr, to, SOURCE_BISQ])
        frappe.db.sql(
            """UPDATE `tab{doctype}`
            SET {assignments}
            WHERE `date` = %s AND from_currency = %s AND to_currency = %s
            AND rate_source = %s""".format(doctype=doctype, assignments=assignments),
            tuple(values),
        )
        updated += 1
    return updated


def _shift_bisq_date(doctype, day, new_day):
    rows = frappe.db.sql(
        """SELECT name, from_currency, to_currency FROM `tab{0}`
        WHERE `date` = %s AND rate_source = %s""".format(doctype),
        (day.isoformat(), SOURCE_BISQ),
    )
    moved = removed = 0
    for name, fr, to in rows:
        taken = frappe.db.sql(
            """SELECT name FROM `tab{0}`
            WHERE `date` = %s AND from_currency = %s AND to_currency = %s
            LIMIT 1""".format(doctype),
            (new_day.isoformat(), fr, to),
        )
        if taken:
            frappe.db.sql("DELETE FROM `tab{0}` WHERE name = %s".format(doctype), (name,))
            removed += 1
            continue
        if doctype == "Currency Exchange GTQ" and frappe.db.has_column(doctype, "rate_timestamp_utc"):
            frappe.db.sql(
                """UPDATE `tab{0}`
                SET `date` = %s, rate_timestamp_utc = %s
                WHERE name = %s""".format(doctype),
                (
                    new_day.isoformat(),
                    timestamp_for_column(rate_timestamp_utc(new_day, fr, to)),
                    name,
                ),
            )
        else:
            frappe.db.sql(
                "UPDATE `tab{0}` SET `date` = %s WHERE name = %s".format(doctype),
                (new_day.isoformat(), name),
            )
        moved += 1
    return moved, removed


def fetch_bisq_days(days):
    """Median input for each UTC day Precyos did not publish.

    One request covers one day. A day Bisq did not trade is absent from the
    result and stays empty. A day with 2000 trades is paged until it ends.
    """
    def fetch_page(timestamp_from, timestamp_to):
        response = requests.get(
            BISQ_URL,
            params={
                "market": "btc_usd",
                "format": "json",
                "sort": "asc",
                "limit": 2000,
                "timestamp_from": timestamp_from,
                "timestamp_to": timestamp_to,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            payload = payload.get("trades") or payload.get("data") or []
        return payload

    def pause():
        time_sleep(1)

    return collect_bisq_days(fetch_page, days, pause)


def _bundle_btc_last():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bundled_rates_manifest.json")
    try:
        with open(path) as handle:
            last = json.load(handle)["btc"]["last"]
        return datetime.date.fromisoformat(last)
    except (OSError, KeyError, ValueError):
        return datetime.date.fromisoformat(BUNDLE_BTC_LAST)


def _btc_usd_dates():
    found = set()
    for doctype in ("Currency Exchange GTQ", "Currency Exchange"):
        if not frappe.db.table_exists(doctype):
            continue
        rows = frappe.db.sql(
            """SELECT DISTINCT `date` FROM `tab{0}`
            WHERE from_currency = 'BTC' AND to_currency = 'USD'""".format(doctype)
        )
        for row in rows:
            found.add(getdate(row[0]))
    return found


def time_sleep(seconds):
    import time
    time.sleep(seconds)


def _usd_gtq_rates():
    """USD to GTQ venta. Currency Exchange GTQ wins; standard Currency Exchange fills gaps."""
    rates = {}
    for doctype in ("Currency Exchange", "Currency Exchange GTQ"):
        if not frappe.db.table_exists(doctype):
            continue
        rows = frappe.db.sql(
            """SELECT `date` AS rate_date, exchange_rate
            FROM `tab{0}`
            WHERE from_currency = 'USD' AND to_currency = 'GTQ'
            ORDER BY `date` ASC""".format(doctype)
        )
        for day, rate in rows:
            rates[frappe.utils.getdate(day)] = rate
    return rates


def _asof(rates, day):
    chosen = None
    chosen_day = None
    for rate_day, rate in rates.items():
        if rate_day <= day and (chosen_day is None or rate_day > chosen_day):
            chosen = rate
            chosen_day = rate_day
    return chosen


def _store_rate(day, fr, to, rate, source):
    outcome = "kept"
    currencies = _currency_names()
    text_day = day.isoformat()
    for doctype in ("Currency Exchange GTQ", "Currency Exchange"):
        if not frappe.db.table_exists(doctype):
            continue
        if doctype == "Currency Exchange" and (fr not in currencies or to not in currencies):
            continue
        columns = "name, rate_source" if _has_source(doctype) else "name, ''"
        existing = frappe.db.sql(
            """SELECT {columns}
            FROM `tab{doctype}`
            WHERE `date` = %s AND from_currency = %s AND to_currency = %s
            LIMIT 1""".format(columns=columns, doctype=doctype),
            (text_day, fr, to),
        )
        if existing:
            current = existing[0][1] or ""
            if current not in (SOURCE_PRECYOS, SOURCE_BISQ):
                continue
            if _has_source(doctype):
                frappe.db.sql(
                    """UPDATE `tab{doctype}`
                    SET exchange_rate = %s, rate_source = %s
                    WHERE name = %s""".format(doctype=doctype),
                    (decimal_string(rate), source, existing[0][0]),
                )
            else:
                frappe.db.sql(
                    "UPDATE `tab{0}` SET exchange_rate = %s WHERE name = %s".format(doctype),
                    (decimal_string(rate), existing[0][0]),
                )
            if outcome != "created":
                outcome = "updated"
            continue
        doc = frappe.new_doc(doctype)
        doc.date = text_day
        doc.from_currency = fr
        doc.to_currency = to
        doc.exchange_rate = decimal_string(rate)
        doc.for_buying = 1
        doc.for_selling = 1
        if _has_source(doctype):
            doc.rate_source = source
        if doctype == "Currency Exchange GTQ" and frappe.db.has_column(doctype, "rate_timestamp_utc"):
            doc.rate_timestamp_utc = timestamp_for_column(rate_timestamp_utc(day, fr, to))
        doc.insert(ignore_permissions=True, ignore_links=doctype == "Currency Exchange GTQ")
        outcome = "created"
    return outcome
