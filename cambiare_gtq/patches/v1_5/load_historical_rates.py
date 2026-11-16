# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Load the bundled Banguat and Precyos history once.

Fresh installs mark patches complete before they run, so after_sync loads the
file there. This patch covers a site that already had Cambiare installed.
"""

from __future__ import unicode_literals

from cambiare_gtq.historical import ensure_btc_currency, load_historical_rates


def execute():
    ensure_btc_currency()
    load_historical_rates()
