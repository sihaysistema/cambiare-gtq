# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from cambiare_gtq.rate_logic import fill_currency_codes

class ConfigurationCambiare(Document):
	def validate(self):
		# Child validate is skipped on the first parent save on Frappe v15.
		fill_currency_codes(self.get("currencies"))
