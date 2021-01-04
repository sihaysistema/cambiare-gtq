# -*- coding: utf-8 -*-
# Copyright (c) 2021, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _, _dict
from frappe.model.document import Document
import json


class CambiareChequePrintSet(Document):
    pass


@frappe.whitelist()
def get_data(params):

    filters = frappe._dict(json.loads(params))

