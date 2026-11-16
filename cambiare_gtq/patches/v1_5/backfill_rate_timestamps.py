# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Stamp existing Currency Exchange GTQ rows with a UTC datetime.

Bitcoin rows are 00:00:00 UTC on the rate date. Other rows are 06:00:00 UTC,
which is 00:00 in America/Guatemala. Rows that already have a stamp are left
alone.
"""

from __future__ import unicode_literals

from cambiare_gtq.historical import backfill_rate_timestamps


def execute():
    backfill_rate_timestamps()
