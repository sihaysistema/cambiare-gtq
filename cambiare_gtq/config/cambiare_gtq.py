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
                    "description": _("Configuracion"),
                    "onboard": 1,
                }
            ]
        },
        {
            "label": _("Registro Consultas Tipo Cambio"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Currency Exchange GTQ",
                    "description": _("Encuentre todas las consultas registradas al banco de GT"),
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
                    "description": _("Impresora para cheques"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Batch Check Print",
                    "description": _("Generador lotes para cheques"),
                    "onboard": 1,
                }
            ]
        }
    ]
