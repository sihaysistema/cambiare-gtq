# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Fill Currency Exchange GTQ when install-app loaded only the standard table.

Rows already stored for a date and pair are skipped, including Bisq rows
written after the bundled file.
"""

from __future__ import unicode_literals

from cambiare_gtq.historical import load_historical_rates


def execute():
    load_historical_rates()
