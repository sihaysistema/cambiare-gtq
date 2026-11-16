# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Bulk-load the bundled Banguat and Precyos history.

The gzip is not a Frappe fixture. Rows already stored for the same date and
pair are left alone, including hand-edited ones. Currency Exchange GTQ receives
every bundled pair. ERPNext Currency Exchange receives a pair only when both
currencies already exist. This does not create Currency masters except BTC,
which is created by ensure_btc_currency.
"""

from __future__ import unicode_literals

import csv
import gzip
import os
from decimal import Decimal

import frappe
from frappe.utils import now_datetime

from cambiare_gtq.rate_logic import canonical_saved_currency
from cambiare_gtq.series_math import SOURCE_BANGUAT, decimal_string, quantize_rate

BUNDLE_VERSION = "2026-11-16"
MARKER = "cambiare_gtq_history_loaded"
_DOCTYPES = ("Currency Exchange GTQ", "Currency Exchange")


def bundle_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bundled_rates.csv.gz")


def read_bundle(path=None):
    path = path or bundle_path()
    rows = []
    with gzip.open(path, "rt") as handle:
        for record in csv.DictReader(handle):
            rows.append(record)
    return rows


def ensure_btc_currency():
    """Ship Bitcoin as a Currency master. The link value is BTC, not a per-site tweak."""
    if frappe.db.exists("Currency", "BTC"):
        _fill_btc_details()
        return "exists"
    doc = frappe.new_doc("Currency")
    doc.currency_name = "BTC"
    doc.enabled = 1
    doc.fraction = "Satoshi"
    doc.fraction_units = 100000000
    doc.smallest_currency_fraction_value = "0.00000001"
    doc.symbol = "\u20bf"
    if _has_field("Currency", "currency_textual_name"):
        doc.currency_textual_name = "Bitcoin"
    doc.insert(ignore_permissions=True)
    return "created"


def _fill_btc_details():
    """Fill symbol and fraction on a BTC row that was created empty."""
    values = {}
    current = frappe.db.get_value(
        "Currency", "BTC", ["symbol", "fraction", "fraction_units"], as_dict=True
    )
    if not current:
        return
    if not current.symbol:
        values["symbol"] = "\u20bf"
    if not current.fraction:
        values["fraction"] = "Satoshi"
    if not current.fraction_units:
        values["fraction_units"] = 100000000
    if values:
        frappe.db.set_value("Currency", "BTC", values, update_modified=False)


@frappe.whitelist()
def reload_historical_rates():
    """Insert bundled rows that are not already stored. Does not overwrite."""
    ensure_btc_currency()
    result = load_historical_rates(force=True)
    frappe.db.commit()
    return result


def load_historical_rates(force=False):
    if not force and frappe.db.get_default(MARKER) == BUNDLE_VERSION and _history_is_complete():
        stamped = stamp_owned_sources()
        banguat = stamp_matching_banguat()
        if stamped or banguat:
            return {
                "status": "sources_stamped",
                "stamped": stamped,
                "banguat_stamped": banguat,
                "version": BUNDLE_VERSION,
            }
        return {"status": "already_loaded", "version": BUNDLE_VERSION}
    if not os.path.exists(bundle_path()):
        return {"status": "missing_bundle"}
    _ensure_gtq_source_column()
    records = read_bundle()
    created = 0
    skipped = 0
    standard_created = 0
    present = _existing_pairs()
    currencies = _currency_names()
    stamp = now_datetime()
    pending = {doctype: [] for doctype in _DOCTYPES}
    for record in records:
        rate = quantize_rate(record["rate"])
        if rate <= 0:
            continue
        pair = (record["date"], record["from_currency"], record["to_currency"], rate, record["source"])
        inverse = (
            record["date"],
            record["to_currency"],
            record["from_currency"],
            quantize_rate(Decimal(1) / rate),
            record["source"],
        )
        for day, fr, to, value, source in (pair, inverse):
            made, skipped_one, std = _queue_pair(
                pending, present, currencies, stamp, day, fr, to, value, source
            )
            created += made
            skipped += skipped_one
            standard_created += std
    for doctype, rows in pending.items():
        _flush(doctype, rows)
    stamped = stamp_owned_sources(records)
    banguat = stamp_matching_banguat(records)
    if _history_is_complete():
        frappe.db.set_default(MARKER, BUNDLE_VERSION)
    return {
        "status": "loaded",
        "created": created,
        "skipped": skipped,
        "standard_created": standard_created,
        "bundled_rows": len(records),
        "stamped": stamped,
        "banguat_stamped": banguat,
    }


def stamp_owned_sources(records=None):
    """Fill rate_source on rows this loader named, once the column exists.

    The upgrade patch inserts before fixtures add the column on Currency
    Exchange, so those rows land with an empty source. Rows with any other
    name are left alone, including hand-edited and earlier backfill rows.
    """
    targets = [doctype for doctype in _DOCTYPES if _needs_stamp(doctype)]
    if not targets:
        return 0
    records = records if records is not None else read_bundle()
    by_source = {}
    for record in records:
        source = record["source"] or SOURCE_BANGUAT
        day = record["date"].replace("-", "")
        for fr, to in (
            (record["from_currency"], record["to_currency"]),
            (record["to_currency"], record["from_currency"]),
        ):
            for doctype in targets:
                prefix = "CEGTQ" if doctype == "Currency Exchange GTQ" else "CEX"
                by_source.setdefault((doctype, source), []).append(
                    "{0}-{1}-{2}-{3}".format(prefix, fr, to, day)
                )
    stamped = 0
    for (doctype, source), names in by_source.items():
        for start in range(0, len(names), 400):
            chunk = names[start:start + 400]
            frappe.db.sql(
                """UPDATE `tab{doctype}`
                SET rate_source = %s
                WHERE name IN ({names}) AND IFNULL(rate_source, '') = ''""".format(
                    doctype=doctype,
                    names=",".join(["%s"] * len(chunk)),
                ),
                tuple([source] + chunk),
            )
            stamped += len(chunk)
    return stamped


def stamp_matching_banguat(records=None):
    """Tag empty rows whose rate is the bundled Banguat figure.

    Cambiare's own pull stores that figure and its reciprocal. A hand-entered
    rate that differs stays empty. Precyos rows in the file are not used here.
    """
    records = records if records is not None else read_bundle()
    bundled = {}
    for record in records:
        if (record.get("source") or SOURCE_BANGUAT) != SOURCE_BANGUAT:
            continue
        rate = quantize_rate(record["rate"])
        if rate <= 0:
            continue
        bundled[(record["date"], record["from_currency"], record["to_currency"])] = rate
    inverses = {
        (day, to, fr): quantize_rate(Decimal(1) / rate)
        for (day, fr, to), rate in bundled.items()
    }
    stamped = 0
    for doctype in _DOCTYPES:
        if not _has_source(doctype):
            continue
        rows = frappe.db.sql(
            """SELECT name, `date`, from_currency, to_currency, exchange_rate
            FROM `tab{0}`
            WHERE IFNULL(rate_source, '') = ''""".format(doctype)
        )
        names = []
        for name, day, fr, to, rate in rows:
            key = (str(day), fr, to)
            stored = quantize_rate(rate)
            if bundled.get(key) == stored or inverses.get(key) == stored:
                names.append(name)
        _set_banguat(doctype, names)
        stamped += len(names)
    return stamped


def remap_saved_currencies():
    """Re-point Available Currencies rows onto the Banguat catalog.

    The ISO code already stored is the currency the user meant. CHF moves
    from variable 6 to variable 5. An ISO the bank does not publish keeps
    its variable number and takes that variable's real code.
    """
    if not frappe.db.table_exists("Available Currencies"):
        return 0
    _forget("Available Currencies")
    column = None
    if frappe.db.has_column("Available Currencies", "currency"):
        column = "currency"
    elif frappe.db.has_column("Available Currencies", "moneda"):
        column = "moneda"
    if not column:
        return 0
    code_column = None
    if frappe.db.has_column("Available Currencies", "code"):
        code_column = "code"
    elif frappe.db.has_column("Available Currencies", "codigo"):
        code_column = "codigo"
    selected = "name, `{0}`".format(column)
    if code_column:
        selected += ", `{0}`".format(code_column)
    rows = frappe.db.sql(
        "SELECT {selected} FROM `tabAvailable Currencies`".format(selected=selected)
    )
    updated = 0
    for row in rows:
        name = row[0]
        current = row[1]
        code = row[2] if code_column else None
        label, iso = canonical_saved_currency(current, code)
        if label == current and (not code_column or iso == (code or "")):
            continue
        if code_column:
            frappe.db.sql(
                "UPDATE `tabAvailable Currencies` SET `{column}` = %s, `{code}` = %s WHERE name = %s".format(
                    column=column, code=code_column
                ),
                (label, iso, name),
            )
        else:
            frappe.db.sql(
                "UPDATE `tabAvailable Currencies` SET `{column}` = %s WHERE name = %s".format(
                    column=column
                ),
                (label, name),
            )
        updated += 1
    return updated


def _set_banguat(doctype, names):
    for start in range(0, len(names), 400):
        chunk = names[start:start + 400]
        if not chunk:
            continue
        frappe.db.sql(
            """UPDATE `tab{doctype}`
            SET rate_source = %s
            WHERE name IN ({names}) AND IFNULL(rate_source, '') = ''""".format(
                doctype=doctype,
                names=",".join(["%s"] * len(chunk)),
            ),
            tuple([SOURCE_BANGUAT] + chunk),
        )


def _needs_stamp(doctype):
    if not _has_source(doctype):
        return False
    prefix = "CEGTQ" if doctype == "Currency Exchange GTQ" else "CEX"
    found = frappe.db.sql(
        "SELECT name FROM `tab{0}` WHERE name LIKE %s AND IFNULL(rate_source, '') = '' LIMIT 1".format(
            doctype
        ),
        (prefix + "-%",),
    )
    return bool(found)


def _queue_pair(pending, present, currencies, stamp, day, fr, to, rate, source):
    created = 0
    skipped = 0
    standard = 0
    for doctype, prefix in (("Currency Exchange GTQ", "CEGTQ"), ("Currency Exchange", "CEX")):
        if not frappe.db.table_exists(doctype):
            continue
        if doctype == "Currency Exchange" and (fr not in currencies or to not in currencies):
            continue
        key = (doctype, day, fr, to)
        if key in present:
            skipped += 1
            continue
        name = "{0}-{1}-{2}-{3}".format(prefix, fr, to, day.replace("-", ""))
        pending[doctype].append(_row(name, stamp, day, fr, to, rate, source, doctype))
        present.add(key)
        created += 1
        if doctype == "Currency Exchange":
            standard += 1
        if len(pending[doctype]) >= 400:
            _flush(doctype, pending[doctype])
            pending[doctype] = []
    return created, skipped, standard


def _row(name, stamp, day, fr, to, rate, source, doctype):
    base = [name, stamp, stamp, "Administrator", "Administrator", 0, 0, day, fr, to, decimal_string(rate), 1, 1]
    if _has_source(doctype):
        base.append(source or SOURCE_BANGUAT)
    return tuple(base)


def _flush(doctype, rows):
    if not rows:
        return
    fields = [
        "name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
        "date", "from_currency", "to_currency", "exchange_rate", "for_buying", "for_selling",
    ]
    if _has_source(doctype):
        fields.append("rate_source")
    width = len(fields)
    for start in range(0, len(rows), 400):
        chunk = rows[start:start + 400]
        placeholders = ",".join(["(" + ",".join(["%s"] * width) + ")"] * len(chunk))
        frappe.db.sql(
            "INSERT INTO `tab{doctype}` ({fields}) VALUES {values}".format(
                doctype=doctype,
                fields=",".join("`{0}`".format(field) for field in fields),
                values=placeholders,
            ),
            tuple(value for row in chunk for value in row),
        )


def _existing_pairs():
    found = set()
    for doctype in _DOCTYPES:
        if not frappe.db.table_exists(doctype):
            continue
        rows = frappe.db.sql(
            "SELECT `date`, from_currency, to_currency FROM `tab{0}`".format(doctype)
        )
        for day, fr, to in rows:
            found.add((doctype, str(day), fr, to))
    return found


def _currency_names():
    if not frappe.db.table_exists("Currency"):
        return set()
    return set(frappe.db.sql_list("SELECT name FROM `tabCurrency`"))


def _has_source(doctype):
    return frappe.db.table_exists(doctype) and frappe.db.has_column(doctype, "rate_source")


def _has_field(doctype, fieldname):
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _ensure_gtq_source_column():
    doctype = "Currency Exchange GTQ"
    if frappe.db.table_exists(doctype) and not frappe.db.has_column(doctype, "rate_source"):
        frappe.db.sql_ddl(
            "ALTER TABLE `tabCurrency Exchange GTQ` ADD COLUMN `rate_source` varchar(140)"
        )
        _forget(doctype)


def _forget(doctype):
    table = "tab" + doctype
    try:
        frappe.cache().hdel("table_columns", table)
    except Exception:
        pass
    client_cache = getattr(frappe, "client_cache", None)
    if client_cache is not None:
        try:
            client_cache.delete_value("table_columns::{0}".format(table))
        except Exception:
            pass


def _history_is_complete():
    """Wait until the standard doctype can store a source before treating the load as done."""
    if not frappe.db.table_exists("Currency Exchange"):
        return frappe.db.table_exists("Currency Exchange GTQ")
    return _has_source("Currency Exchange")
