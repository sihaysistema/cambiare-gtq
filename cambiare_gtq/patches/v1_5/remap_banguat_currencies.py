# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Point saved currencies at the Banguat variable for their ISO code.

Also stamp Rate Source ``Banguat`` on rows this app's pull stored with an
empty source, when the rate matches the bundled bank figure.
"""

from __future__ import unicode_literals

from cambiare_gtq.historical import remap_saved_currencies, stamp_matching_banguat


def execute():
    remap_saved_currencies()
    stamp_matching_banguat()
