# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Whitelisted exchange-rate API for other apps (Revelare Direct Cash Flow).

Reads ``Currency Exchange GTQ`` first and falls back to ERPNext
``Currency Exchange`` for the same pair. Writes go to both doctypes.

The rate is the ERPNext multiplier: amount in ``to_currency`` equals
amount in ``from_currency`` times ``rate``. ``USD -> GTQ`` is quetzales
per 1 US dollar. ``GTQ -> USD`` is US dollars per 1 quetzal.
"""

from __future__ import unicode_literals

import frappe
from frappe import _

from cambiare_gtq.rate_logic import (
    ExchangeService,
    RateError,
    ZeepBanguatClient,
    currencies_from_config_rows,
    parse_date,
)


_MESSAGES = {
    "not_found": "No exchange rate is registered for {0} to {1} on or before {2}.",
    "bad_range": "From Date must be on or before To Date.",
    "bad_date": "Date {0} is not a valid date. Use YYYY-MM-DD.",
    "unknown_currency": "Currency {0} is not a Banco de Guatemala variable known to Cambiare.",
    "banguat": "Could not fetch exchange rates from Banco de Guatemala: {0}",
    "bad_quote": "Banco de Guatemala returned a rate that cannot be stored.",
}

_DOCTYPES = ("Currency Exchange GTQ", "Currency Exchange")


def _throw(exc):
    template = _MESSAGES.get(exc.code, "Could not resolve the exchange rate.")
    frappe.throw(_(template).format(*exc.args), title=_("Exchange Rate"))


def _service():
    return ExchangeService(FrappeRateBook(), ZeepBanguatClient())


def _configured_currencies():
    if not frappe.db.exists("DocType", "Configuration Cambiare"):
        return []
    try:
        config = frappe.get_doc("Configuration Cambiare")
    except Exception:
        return []
    rows = []
    for row in config.get("currencies") or config.get("monedas") or []:
        rows.append(row)
    return currencies_from_config_rows(rows)


class FrappeRateBook(object):
    """Persists both directions' rates without creating duplicate rows."""

    def doctypes(self):
        found = []
        for doctype in _DOCTYPES:
            if frappe.db.exists("DocType", doctype):
                found.append(doctype)
        return found

    def add(self, rate_date, from_currency, to_currency, rate):
        created = 0
        skipped = 0
        rate_date = parse_date(rate_date)
        for doctype in self.doctypes():
            if _exists(doctype, rate_date, from_currency, to_currency):
                skipped += 1
                continue
            doc = frappe.new_doc(doctype)
            doc.date = rate_date
            doc.from_currency = from_currency
            doc.to_currency = to_currency
            doc.exchange_rate = float(rate)
            doc.for_buying = 1
            doc.for_selling = 1
            doc.insert(ignore_permissions=True)
            created += 1
        if not self.doctypes():
            raise RateError("not_found", (from_currency, to_currency, str(rate_date)))
        return created, skipped

    def find(self, from_currency, to_currency):
        """Prefer Currency Exchange GTQ when both doctypes have the same date."""
        by_date = {}
        for doctype in self.doctypes():
            rows = frappe.db.sql(
                """SELECT `date` AS rate_date, exchange_rate
                FROM `tab{doctype}`
                WHERE from_currency = %s AND to_currency = %s
                ORDER BY `date` ASC, modified DESC""".format(doctype=doctype),
                (from_currency, to_currency),
                as_dict=True,
            )
            for row in rows:
                key = parse_date(row.rate_date)
                if key not in by_date:
                    by_date[key] = {"date": key, "rate": float(row.exchange_rate)}
        return list(by_date.values())


def _exists(doctype, rate_date, from_currency, to_currency):
    return frappe.db.exists(
        doctype,
        {
            "date": rate_date,
            "from_currency": from_currency,
            "to_currency": to_currency,
        },
    )


@frappe.whitelist()
def backfill_exchange_rates(from_date, to_date, currency=None):
    """Fetch a Banguat date range and store it. Idempotent per date and pair.

    ``currency`` is an ISO code. Leave it empty to fetch USD and every
    currency selected on Configuration Cambiare. ``USD`` or ``GTQ`` fetches
    only the dollar/quetzal pair. Any other known ISO code also stores USD
    for the same dates, because Banguat quotes that currency per US dollar.

    Existing rows for the same date, from currency and to currency are left
    as they are. A second run reports them as skipped.
    """
    try:
        result = _service().backfill(
            from_date,
            to_date,
            currency=currency,
            configured=_configured_currencies(),
        )
    except RateError as exc:
        _throw(exc)
    frappe.db.commit()
    return result


@frappe.whitelist()
def get_closing_rate(from_currency, to_currency, date, fetch_if_missing=1):
    """Rate registered on ``date`` for ``from_currency`` to ``to_currency``.

    When that date has no row and ``fetch_if_missing`` is true, the date is
    requested from Banguat and stored. When it is still missing, the latest
    row on or before ``date`` is used. The response ``rate_date`` is the date
    of the row actually used and ``source`` is ``exact``, ``banguat``,
    ``inverse``, ``fallback`` or ``identity``.

    ``meaning`` is ``1 {from} = {rate} {to}``. ``USD -> GTQ`` is quetzales
    per 1 US dollar. ``GTQ -> USD`` is the reciprocal.
    """
    try:
        return _service().get_closing_rate(
            from_currency, to_currency, date, fetch_if_missing=fetch_if_missing
        )
    except RateError as exc:
        _throw(exc)


@frappe.whitelist()
def get_average_rate(from_currency, to_currency, from_date, to_date, fetch_if_missing=1):
    """Unweighted arithmetic average of the daily rate for each covered day.

    Each calendar day in the inclusive range contributes one rate, resolved
    the same way as :func:`get_closing_rate` (that day's row, otherwise the
    latest row on or before that day). Days that still have no rate are
    omitted. ``days`` is the number of rates that were averaged. This is the
    simple average used for a partial month, not a volume-weighted average.
    """
    try:
        return _service().get_average_rate(
            from_currency,
            to_currency,
            from_date,
            to_date,
            fetch_if_missing=fetch_if_missing,
        )
    except RateError as exc:
        _throw(exc)
