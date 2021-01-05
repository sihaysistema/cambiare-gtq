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
    """
    Recolector/procesador de datos para generar formatos de impresion para cheques,
    de Payment Entry Journal Entry, en funcion a acc bank, company, y fechas seleccionadas
    en params

    Args:
        params (dict): Parametros doctype

    Returns:
        list: Lista diccionarios con misma estrucutra para tabla hija
    """

    all_data = []
    filters = frappe._dict(json.loads(params))

    all_data.extend(get_data_of_payment_entry(filters))
    all_data.extend(get_data_of_journal_entry(filters))

    return all_data


def get_data_of_payment_entry(filters):
    """
    Obtiene datos de Payment Entry, donde sean cheques (ver condicionales de query)

    Args:
        filters (dict): parametros user

    Returns:
        list: lista diccionarios
    """

    data = frappe.db.sql(
        f"""
            SELECT name AS id, 'Payment Entry' AS transaction_id, reference_no AS cheque_no,
            paid_amount AS amount, party_type, party AS third_party
            FROM `tabPayment Entry`
            WHERE mode_of_payment='Cheque' AND company='{filters.company}'
            AND posting_date BETWEEN '{filters.start_date}' AND '{filters.end_date}'
            AND bank_account='{filters.source_bank_acc}' AND docstatus=1
        """, as_dict=True
    ) or []

    if data:
        for dd in data:
            addr = get_address(dd.get('third_party'), dd.get('party_type'))
            if addr:
                dd.update({
                    'remark': addr.get('remark', ''),
                    'po_box': addr.get('po_box', ''),
                    'city': addr.get('city', ''),
                    'pincode': addr.get('pincode', '')
                })
            else:
                dd.update({
                    'remark': '',
                    'po_box': '',
                    'city': '',
                    'pincode': ''
                })

    return data


def get_data_of_journal_entry(filters):
    """
    Obtiene datos de Journal Entry/Account, donde sean cheques (ver condicionales de query)

    Args:
        filters (dict): parametros user

    Returns:
        list: lista diccionarios
    """

    data = frappe.db.sql(
        f"""
            SELECT JE.name AS id
            FROM `tabJournal Entry` AS JE
            JOIN `tabJournal Entry Account` AS JEA
            WHERE JEA.parent=JE.name
            AND JE.mode_of_payment='Cheque'
            AND JE.company='{filters.company}'
            AND (JE.posting_date BETWEEN '{filters.start_date}' AND '{filters.end_date}')
            AND JEA.bank_account='{filters.source_bank_acc}' AND JE.docstatus=1
        """, as_dict=True
    ) or []

    # RE-Construccion datos desde Journal Entry/Accounts
    all_data = []
    for data_je in data:
        cheque_no = frappe.db.get_value('Journal Entry', {'name': data_je.get('id')}, 'cheque_no')

        amount = frappe.db.get_value('Journal Entry Account',
                                    {'parent': data_je.get('id'), 'bank_account': filters.source_bank_acc},
                                     'credit_in_account_currency')

        party_type = frappe.db.get_values('Journal Entry Account',
                                          filters={'parent': data_je.get('id'),
                                                   'party_type': ['!=', '']},
                                          fieldname=['party_type', 'party'], as_dict=1)[0]
        all_data.append({
            'id': data_je.get('id'),
            'transaction_id': 'Journal Entry',
            'cheque_no': cheque_no,
            'amount': amount,
            'party_type': party_type.get('party_type', ''),
            'third_party': party_type.get('party', '')
        })

    if all_data:
        for dd in all_data:
            addr = get_address(dd.get('third_party'), dd.get('party_type'))
            if addr:
                dd.update({
                    'remark': addr.get('remark', ''),
                    'po_box': addr.get('po_box', ''),
                    'city': addr.get('city', ''),
                    'pincode': addr.get('pincode', '')
                })
            else:
                dd.update({
                    'remark': '',
                    'po_box': '',
                    'city': '',
                    'pincode': ''
                })

    return all_data


def get_address(party_name, party_type):
    """
    Obtiene direccion de xx Proveedor/Cliente

    Args:
        party_name (str): Nombre Proveedor/cliente
        party_type (str): Supplier/Customer

    Returns:
        dict: [description]
    """

    addr = frappe.db.sql(
        f"""
        SELECT DL.link_name AS name_entity, AD.city AS city,
        AD.pincode AS pincode
        FROM `tabAddress` AS AD
        JOIN `tabDynamic Link` AS DL
        WHERE DL.parent = AD.name
        AND DL.parenttype='Address' AND DL.link_doctype='{party_type}'
        AND DL.link_name='{party_name}' AND AD.is_primary_address=1;
        """, as_dict=True
    ) or {}

    if addr:
        return addr[0]

    return addr
