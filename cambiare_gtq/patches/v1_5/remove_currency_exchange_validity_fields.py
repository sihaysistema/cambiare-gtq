# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Remove the unused validity range from ERPNext Currency Exchange.

``date`` is the rate date. ``valid_from`` and ``valid_to`` were custom
fields nothing in this app read. The section break and column break existed
only to place those two fields, so they go with them. Dropping the fixture
entries does not delete Custom Field rows already installed.
"""

from __future__ import unicode_literals

import frappe

# Records created by the previous Custom Field fixture.
VALIDITY_FIELDS = (
    "Currency Exchange-valid_from",
    "Currency Exchange-valid_to",
    "Currency Exchange-col_break",
    "Currency Exchange-validity_date_ranges",
)

# Only the datetime fields created real columns.
VALUE_COLUMNS = ("valid_from", "valid_to")


def execute():
    """Delete the validity Custom Fields and their columns."""
    for name in VALIDITY_FIELDS:
        if frappe.db.exists("Custom Field", name):
            frappe.delete_doc(
                "Custom Field",
                name,
                force=True,
                ignore_permissions=True,
                ignore_missing=True,
            )
    _drop_leftover_columns()
    frappe.clear_cache(doctype="Currency Exchange")


def _drop_leftover_columns():
    """delete_doc drops the column. Repeat the drop if a row was removed another way."""
    if not frappe.db.table_exists("Currency Exchange"):
        return
    for column in VALUE_COLUMNS:
        if frappe.db.has_column("Currency Exchange", column):
            frappe.db.sql_ddl(
                "ALTER TABLE `tabCurrency Exchange` DROP COLUMN `{0}`".format(column)
            )
