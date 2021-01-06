# -*- coding: utf-8 -*-
# Copyright (c) 2021, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json
from datetime import date

import frappe
from frappe.model.document import Document

class BatchCheckPrint(Document):
    pass


@frappe.whitelist()
def create_set(params, data_reg):
    """
    Creador de registros para Cambiare Cheque Print Set

    Args:
        params (dict): Filtros batch doctype
        data_reg (list): Listado de registros para tabla hija

    Returns:
        bool: True/False
    """
    try:
        today = date.today()

        params = json.loads(params)
        data_reg = json.loads(data_reg)

        # create a new document
        doc = frappe.get_doc({
            'doctype': 'Cambiare Cheque Print Set',
            'creation_date': today.strftime("%Y-%m-%d"),
            'source_bank_account': params.get('source_bank_acc'),
            'start_date': params.get('start_date'),
            'company': params.get('company'),
            'currency': params.get('currency'),
            'end_date': params.get('end_date'),
            'cheque_to_print': data_reg,
        })
        doc.save()

        return True, doc.name

    except:
        return False, frappe.get_traceback()
