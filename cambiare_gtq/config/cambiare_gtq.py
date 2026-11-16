# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
    return [
        {
            "label": _("Configuration Cambiare"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Configuration Cambiare",
                    "description": _("Exchange rate settings"),
                    "onboard": 1,
                }
            ]
        },
        {
            "label": _("Exchange Rate Records"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Currency Exchange GTQ",
                    "description": _("Rates fetched from Banco de Guatemala"),
                    "onboard": 1,
                }
            ]
        },
        {
            "label": _("Printer"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Cambiare Cheque Print Set",
                    "description": _("Cheque print settings"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Batch Check Print",
                    "description": _("Print cheques in a batch"),
                    "onboard": 1,
                }
            ]
        }
    ]
