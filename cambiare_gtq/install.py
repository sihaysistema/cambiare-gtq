# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe

from cambiare_gtq.historical import ensure_btc_currency, load_historical_rates, remap_saved_currencies


def after_install():
    """Create BTC before fixtures. History is loaded in after_sync, once currencies exist."""
    ensure_btc_currency()
    frappe.db.commit()


def after_sync():
    """Fixtures have run, so Currency Exchange can see which currencies exist."""
    ensure_btc_currency()
    load_historical_rates()
    frappe.db.commit()


def after_migrate():
    """Upgrade path: the one-time patch may have run before the source column existed."""
    ensure_btc_currency()
    remap_saved_currencies()
    load_historical_rates()
    frappe.db.commit()
