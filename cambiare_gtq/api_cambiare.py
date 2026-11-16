# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Backward-compatible entry points for the desk button and older callers.

New code should call ``cambiare_gtq.exchange_rates``.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate

from cambiare_gtq.exchange_rates import backfill_exchange_rates
from cambiare_gtq.rate_logic import VARIABLE_TO_ISO, ZeepBanguatClient


@frappe.whitelist()
def preparar_peticion_banguat(opt, fecha_ini=None, fecha_fin=None, moneda=None):
    """Dispatch the historical Banguat operations.

    Options 2 to 5 used to build a request and discard it. They now store
    the range. Options 1 and 6 still refresh today's rates for the scheduler
    button and are idempotent.
    """
    opt = str(opt)
    if opt == "1":
        return backfill_exchange_rates(nowdate(), nowdate(), currency="USD")
    if opt == "6":
        return backfill_exchange_rates(nowdate(), nowdate(), currency=None)
    if opt == "2":
        return backfill_exchange_rates(fecha_ini, nowdate(), currency="USD")
    if opt == "3":
        return backfill_exchange_rates(fecha_ini, nowdate(), currency=_iso_for_variable(moneda))
    if opt == "4":
        return backfill_exchange_rates(fecha_ini, fecha_fin, currency="USD")
    if opt == "5":
        return backfill_exchange_rates(fecha_ini, fecha_fin, currency=_iso_for_variable(moneda))
    if opt == "7":
        return _available_variables()
    frappe.throw(_("Unknown Banco de Guatemala request option {0}.").format(opt))


def _iso_for_variable(moneda):
    try:
        variable = int(moneda)
    except (TypeError, ValueError):
        frappe.throw(_("Currency variable {0} is not a Banco de Guatemala code.").format(moneda))
    if variable == 2:
        return "USD"
    iso = VARIABLE_TO_ISO.get(variable)
    if not iso:
        frappe.throw(_("Currency variable {0} is not a Banco de Guatemala code.").format(moneda))
    return iso


def _available_variables():
    try:
        payload = ZeepBanguatClient().service.VariablesDisponibles()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cambiare GTQ Banguat")
        frappe.throw(_("Could not fetch exchange rates from Banco de Guatemala: {0}").format(
            _("the variable list is unavailable")
        ))
    variables = []
    container = getattr(payload, "Variables", None)
    items = getattr(container, "Variable", None) if container is not None else None
    if items is None:
        return variables
    if not isinstance(items, list):
        items = [items]
    for item in items:
        variables.append("{0} - {1}".format(item.moneda, item.descripcion))
    return variables
