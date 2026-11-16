# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate

from cambiare_gtq.exchange_rates import backfill_exchange_rates


def daily():
    """Run when Configuration Cambiare frequency is Daily."""
    return _run_if_configured("Daily")


def hourly():
    """Run when Configuration Cambiare frequency is Hourly."""
    return _run_if_configured("Hourly")


def weekly():
    """Run when Configuration Cambiare frequency is Weekly."""
    return _run_if_configured("Weekly")


def monthly():
    """Run when Configuration Cambiare frequency is Monthly."""
    return _run_if_configured("Monthly")


def _run_if_configured(frequency):
    """Fetch today's rates when the single configuration matches ``frequency``."""
    if not frappe.db.exists("DocType", "Configuration Cambiare"):
        return None
    config = frappe.get_doc("Configuration Cambiare")
    if config.get("disable_queries"):
        return _("Queries are disabled in Configuration Cambiare")
    if str(config.get("frequency") or "") != frequency:
        return None
    today = nowdate()
    banguat = backfill_exchange_rates(today, today)
    from cambiare_gtq.btc_sync import refresh_btc_rates
    bitcoin = refresh_btc_rates()
    return {"banguat": banguat, "bitcoin": bitcoin}
