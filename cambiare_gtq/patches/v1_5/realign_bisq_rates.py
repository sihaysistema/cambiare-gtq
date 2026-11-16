# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Put Bisq rows on the Precyos date convention.

Where Precyos publishes the date, the row takes that BTC/USD price. Otherwise
the row moves forward one day, because it was the median of trades on the
date it was stored under.
"""

from __future__ import unicode_literals

import frappe

from cambiare_gtq.btc_sync import realign_bisq_rates


def execute():
    result = realign_bisq_rates()
    frappe.db.commit()
    return result
