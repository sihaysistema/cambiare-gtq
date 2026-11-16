# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Refresh BTC/USD and BTC/GTQ.

Precyos (https://precyos.com) is the default source. Its public series is
BTC in USD. BTC/GTQ is that price times the Banguat as-of venta (Precyos has
no public GTQ endpoint). Days Precyos does not publish fall back to the median
of Bisq BTC/USD trades in that UTC day. Selecting Bisq in Configuration
Cambiare uses Bisq for every day in the window. Rows tagged Banguat, or with
no source, are left alone.
"""

from __future__ import unicode_literals

import datetime

import frappe
import requests
from frappe.utils import getdate, nowdate

from cambiare_gtq.historical import _currency_names, _has_source, ensure_btc_currency
from cambiare_gtq.series_math import (
    BISQ_URL,
    PRECYOS_URL,
    SOURCE_BISQ,
    SOURCE_PRECYOS,
    btc_gtq,
    decimal_string,
    page_bisq,
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
    """Recompute BTC pairs for a window. Defaults to the last 14 UTC days."""
    end = getdate(to_date or nowdate())
    start = getdate(from_date) if from_date else end - datetime.timedelta(days=13)
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
    if bisq_trades is None and (source == SOURCE_BISQ or source == SOURCE_PRECYOS):
        bisq_trades = fetch_bisq_trades(start, end)
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
    text = day.isoformat() if hasattr(day, "isoformat") else str(day)
    if source == SOURCE_BISQ:
        price = bisq.get(day)
        return (price, SOURCE_BISQ) if price is not None else (None, None)
    if text in precyos:
        return precyos[text], SOURCE_PRECYOS
    # Precyos map is keyed by iso strings from the feed.
    if day in precyos:
        return precyos[day], SOURCE_PRECYOS
    price = bisq.get(day)
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


def fetch_bisq_trades(start, end):
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
        return response.json()

    def pause():
        time_sleep(1)

    return page_bisq(fetch_page, start, end, pause)


def time_sleep(seconds):
    import time
    time.sleep(seconds)


def _usd_gtq_rates():
    if not frappe.db.table_exists("Currency Exchange GTQ"):
        return {}
    rows = frappe.db.sql(
        """SELECT `date` AS rate_date, exchange_rate
        FROM `tabCurrency Exchange GTQ`
        WHERE from_currency = 'USD' AND to_currency = 'GTQ'
        ORDER BY `date` ASC"""
    )
    return {frappe.utils.getdate(day): rate for day, rate in rows}


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
        doc.flags.name_set = True
        doc.insert(ignore_permissions=True, ignore_links=doctype == "Currency Exchange GTQ")
        outcome = "created"
    return outcome
