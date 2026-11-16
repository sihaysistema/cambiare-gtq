# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Move Spanish fieldnames and option values onto the English DocType.

Runs before model sync on every supported Frappe major, while the old
columns still exist. A site that already migrated is left unchanged.
"""

from __future__ import unicode_literals

import frappe

from cambiare_gtq.rate_logic import (
    LEGACY_CURRENCY_OPTIONS,
    LEGACY_FREQUENCY,
    iso_from_option,
)


def execute():
    """Rename Configuration Cambiare and Available Currencies fields."""
    _rename_column("Available Currencies", "moneda", "currency")
    _rename_column("Available Currencies", "codigo", "code")
    _rewrite_currency_options()
    _fill_currency_codes()
    _retarget_parentfield("Available Currencies", "monedas", "currencies")
    _rename_single_field("Configuration Cambiare", "frecuencia", "frequency", LEGACY_FREQUENCY)
    _rename_single_field("Configuration Cambiare", "desactivar_consultas", "disable_queries", None)
    _rename_single_field("Configuration Cambiare", "monedas", "currencies", None)
    _rename_single_field(
        "Configuration Cambiare",
        "monedas_disponibles_section",
        "available_currencies_section",
        None,
    )
    for doctype, old, new in (
        ("Configuration Cambiare", "frecuencia", "frequency"),
        ("Configuration Cambiare", "desactivar_consultas", "disable_queries"),
        ("Configuration Cambiare", "monedas", "currencies"),
        ("Configuration Cambiare", "monedas_disponibles_section", "available_currencies_section"),
        ("Available Currencies", "moneda", "currency"),
        ("Available Currencies", "codigo", "code"),
    ):
        _rename_property_setter_field(doctype, old, new)


def _table_exists(doctype):
    return frappe.db.table_exists(doctype)


def _forget_columns(doctype):
    """Drop cached column lists. DDL commits immediately and the cache would lie."""
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
    local_cols = getattr(frappe.local, "table_columns", None)
    if isinstance(local_cols, dict):
        local_cols.pop(doctype, None)
        local_cols.pop(table, None)


def _rename_column(doctype, old, new):
    if not _table_exists(doctype):
        return
    _forget_columns(doctype)
    has_old = frappe.db.has_column(doctype, old)
    has_new = frappe.db.has_column(doctype, new)
    table = "`tab{0}`".format(doctype)
    if has_old and not has_new:
        column_type, null_sql = _column_spec(doctype, old)
        frappe.db.sql_ddl(
            "ALTER TABLE {table} CHANGE `{old}` `{new}` {column_type} {null_sql}".format(
                table=table, old=old, new=new, column_type=column_type, null_sql=null_sql
            )
        )
        _forget_columns(doctype)
    elif has_old and has_new:
        frappe.db.sql(
            """UPDATE {table}
            SET `{new}` = `{old}`
            WHERE (`{new}` IS NULL OR `{new}` = '')
            AND `{old}` IS NOT NULL AND `{old}` != ''""".format(table=table, new=new, old=old)
        )


def _column_spec(doctype, column):
    rows = frappe.db.sql("SHOW COLUMNS FROM `tab{0}` LIKE %s".format(doctype), (column,))
    if not rows:
        return "varchar(140)", "NULL"
    column_type = rows[0][1]
    null_sql = "NULL" if rows[0][2] == "YES" else "NOT NULL"
    return column_type, null_sql


def _rewrite_currency_options():
    if not _table_exists("Available Currencies"):
        return
    _forget_columns("Available Currencies")
    column = "currency" if frappe.db.has_column("Available Currencies", "currency") else None
    if not column and frappe.db.has_column("Available Currencies", "moneda"):
        column = "moneda"
    if not column:
        return
    for old, new in LEGACY_CURRENCY_OPTIONS.items():
        if old == new:
            continue
        frappe.db.sql(
            "UPDATE `tabAvailable Currencies` SET `{column}` = %s WHERE `{column}` = %s".format(
                column=column
            ),
            (new, old),
        )


def _fill_currency_codes():
    if not _table_exists("Available Currencies"):
        return
    _forget_columns("Available Currencies")
    if not frappe.db.has_column("Available Currencies", "currency"):
        return
    if not frappe.db.has_column("Available Currencies", "code"):
        return
    # Raw SQL: this patch runs before DocType sync, so meta still has the old fieldname.
    rows = frappe.db.sql(
        """SELECT name, currency FROM `tabAvailable Currencies`
        WHERE IFNULL(currency, '') != '' AND IFNULL(code, '') = ''"""
    )
    for name, currency in rows:
        iso = iso_from_option(currency)
        if iso:
            frappe.db.sql(
                "UPDATE `tabAvailable Currencies` SET code = %s WHERE name = %s",
                (iso, name),
            )


def _retarget_parentfield(child_doctype, old, new):
    if not _table_exists(child_doctype):
        return
    frappe.db.sql(
        "UPDATE `tab{0}` SET parentfield = %s WHERE parentfield = %s".format(child_doctype),
        (new, old),
    )


def _rename_single_field(doctype, old, new, value_map):
    current = frappe.db.sql(
        "SELECT value FROM `tabSingles` WHERE doctype = %s AND field = %s",
        (doctype, old),
    )
    if not current:
        if value_map:
            _remap_single_value(doctype, new, value_map)
        return
    value = current[0][0]
    if value_map and value in value_map:
        value = value_map[value]
    existing = frappe.db.sql(
        "SELECT value FROM `tabSingles` WHERE doctype = %s AND field = %s",
        (doctype, new),
    )
    if existing:
        if (existing[0][0] in (None, "")) and value not in (None, ""):
            frappe.db.sql(
                "UPDATE `tabSingles` SET value = %s WHERE doctype = %s AND field = %s",
                (value, doctype, new),
            )
        frappe.db.sql(
            "DELETE FROM `tabSingles` WHERE doctype = %s AND field = %s",
            (doctype, old),
        )
    else:
        frappe.db.sql(
            "UPDATE `tabSingles` SET field = %s, value = %s WHERE doctype = %s AND field = %s",
            (new, value, doctype, old),
        )


def _remap_single_value(doctype, field, value_map):
    rows = frappe.db.sql(
        "SELECT value FROM `tabSingles` WHERE doctype = %s AND field = %s",
        (doctype, field),
    )
    if not rows:
        return
    value = rows[0][0]
    if value in value_map:
        frappe.db.sql(
            "UPDATE `tabSingles` SET value = %s WHERE doctype = %s AND field = %s",
            (value_map[value], doctype, field),
        )


def _rename_property_setter_field(doctype, old, new):
    if not frappe.db.table_exists("Property Setter"):
        return
    frappe.db.sql(
        """UPDATE `tabProperty Setter` SET field_name = %s
        WHERE doc_type = %s AND field_name = %s""",
        (new, doctype, old),
    )
