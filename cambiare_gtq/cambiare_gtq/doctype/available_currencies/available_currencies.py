# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document

from cambiare_gtq.rate_logic import iso_from_option


class AvailableCurrencies(Document):
    def validate(self):
        iso = iso_from_option(self.currency)
        if iso:
            self.code = iso
