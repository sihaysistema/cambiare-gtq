# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Convert an amount between currencies.

Direct pairs are used when that date has a stored rate. Otherwise the rate is
crossed through GTQ, so EUR to BTC is (EUR to GTQ) / (BTC to GTQ). ``method``
is ``daily`` (one date, default today) or ``average`` (unweighted mean of the
daily rates in an inclusive range).
"""

from __future__ import unicode_literals

import datetime
from decimal import Decimal

import frappe
from frappe.utils import getdate, nowdate

from cambiare_gtq.btc_sync import refresh_btc_rates
from cambiare_gtq.exchange_rates import get_average_rate, get_closing_rate
from cambiare_gtq.rate_logic import RateError
from cambiare_gtq.series_math import bridge_rate, decimal_string, quantize_rate


@frappe.whitelist()
def convert(amount, from_currency, to_currency, date=None, from_date=None, to_date=None,
            method="daily", fetch_if_missing=1):
    from_currency = (from_currency or "").strip().upper()
    to_currency = (to_currency or "").strip().upper()
    method = (method or "daily").strip().lower()
    if method not in ("daily", "average"):
        frappe.throw(frappe._("Method must be daily or average."))
    quantity = Decimal(str(amount))
    if method == "average":
        start = getdate(from_date or date or nowdate())
        end = getdate(to_date or date or nowdate())
        if start > end:
            frappe.throw(frappe._("From Date must be on or before To Date."))
        resolved = _average(from_currency, to_currency, start, end, fetch_if_missing)
    else:
        day = getdate(date or from_date or nowdate())
        resolved = _daily(from_currency, to_currency, day, fetch_if_missing)
    converted = quantize_rate(quantity * Decimal(str(resolved["rate"])))
    resolved["amount"] = decimal_string(converted)
    resolved["rate"] = decimal_string(resolved["rate"])
    resolved["method"] = method
    resolved["from_currency"] = from_currency
    resolved["to_currency"] = to_currency
    return resolved


def _daily(from_currency, to_currency, day, fetch_if_missing):
    _maybe_refresh_btc(from_currency, to_currency, day, day, fetch_if_missing)
    direct = _safe_closing(from_currency, to_currency, day, fetch_if_missing)
    if direct and direct.get("source") == "exact":
        return _pack_daily(direct, "direct")
    if from_currency != "GTQ" and to_currency != "GTQ":
        left = _safe_closing(from_currency, "GTQ", day, fetch_if_missing)
        right = _safe_closing(to_currency, "GTQ", day, fetch_if_missing)
        if left and right:
            rate = bridge_rate(left["rate"], right["rate"])
            return {
                "rate": rate,
                "rate_date": day.isoformat(),
                "source": "cross",
                "rate_source": _join_sources(left, right),
                "via": "GTQ",
                "legs": [_public_leg(left), _public_leg(right)],
            }
    if direct:
        return _pack_daily(direct, "direct")
    frappe.throw(
        frappe._("No exchange rate is registered for {0} to {1} on or before {2}.").format(
            from_currency, to_currency, day.isoformat()
        ),
        title=frappe._("Exchange Rate"),
    )


def _average(from_currency, to_currency, start, end, fetch_if_missing):
    _maybe_refresh_btc(from_currency, to_currency, start, end, fetch_if_missing)
    if from_currency == to_currency:
        days = (end - start).days + 1
        return {
            "rate": Decimal(1),
            "rate_date": start.isoformat(),
            "covered_from": start.isoformat(),
            "covered_to": end.isoformat(),
            "days": days,
            "source": "identity",
        }
    if from_currency != "GTQ" and to_currency != "GTQ":
        rates = []
        sources = []
        day = start
        while day <= end:
            try:
                one = _daily(from_currency, to_currency, day, 0)
            except Exception:
                one = None
            if one:
                rates.append(Decimal(str(one["rate"])))
                sources.append(one.get("source"))
            day += datetime.timedelta(days=1)
        if not rates:
            frappe.throw(
                frappe._("No exchange rate is registered for {0} to {1} on or before {2}.").format(
                    from_currency, to_currency, start.isoformat() + " - " + end.isoformat()
                )
            )
        average = sum(rates) / Decimal(len(rates))
        return {
            "rate": average,
            "rate_date": start.isoformat(),
            "covered_from": start.isoformat(),
            "covered_to": end.isoformat(),
            "days": len(rates),
            "source": "cross" if "cross" in sources else sources[0],
        }
    result = get_average_rate(from_currency, to_currency, start, end, fetch_if_missing)
    return {
        "rate": Decimal(str(result["average"])),
        "rate_date": result.get("covered_from") or result["from_date"],
        "covered_from": result["from_date"],
        "covered_to": result["to_date"],
        "days": result["days"],
        "source": "direct",
    }


def _safe_closing(from_currency, to_currency, day, fetch_if_missing):
    try:
        return get_closing_rate(from_currency, to_currency, day.isoformat(), fetch_if_missing)
    except Exception as exc:
        if isinstance(exc, RateError) or "Exchange Rate" in str(getattr(exc, "args", exc)):
            return None
        # frappe.throw raises ValidationError. Treat a missing rate as no row.
        if exc.__class__.__name__ in ("ValidationError", "RateError"):
            return None
        raise


def _pack_daily(direct, source):
    packed = {
        "rate": Decimal(str(direct["rate"])),
        "rate_date": direct["rate_date"],
        "source": source,
    }
    if direct.get("rate_source"):
        packed["rate_source"] = direct["rate_source"]
    return packed


def _public_leg(leg):
    return {
        "from_currency": leg["from_currency"],
        "to_currency": leg["to_currency"],
        "rate": decimal_string(leg["rate"]),
        "rate_date": leg["rate_date"],
        "rate_source": leg.get("rate_source"),
    }


def _join_sources(left, right):
    parts = [value for value in (left.get("rate_source"), right.get("rate_source")) if value]
    if not parts:
        return None
    if parts[0] == parts[-1]:
        return parts[0]
    return " + ".join(parts)


def _maybe_refresh_btc(from_currency, to_currency, start, end, fetch_if_missing):
    if not _truthy(fetch_if_missing):
        return
    if "BTC" not in (from_currency, to_currency):
        return
    refresh_btc_rates(start.isoformat(), end.isoformat())


def _truthy(value):
    if value is None:
        return True
    return str(value).strip().lower() not in ("0", "false", "no", "")
