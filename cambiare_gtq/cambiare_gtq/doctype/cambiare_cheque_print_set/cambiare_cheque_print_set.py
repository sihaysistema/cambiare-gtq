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
    """[summary]

    Args:
        params ([type]): [description]

    Returns:
        [type]: [description]
    """

    all_data = []
    filters = frappe._dict(json.loads(params))

    all_data.extend(get_data_of_payment_entry(filters))

    return all_data


def get_data_of_payment_entry(filters):
    """[summary]

    Args:
        filters ([type]): [description]

    Returns:
        [type]: [description]
    """

    data = frappe.db.sql(
        f"""
            SELECT 'Payment Entry' AS transaction_id, reference_no AS cheque_no,
            paid_amount AS amount, party_type, party AS third_party
            FROM `tabPayment Entry`
            WHERE mode_of_payment='Cheque' AND company='{filters.company}'
            AND posting_date BETWEEN '{filters.start_date}' AND '{filters.end_date}'
            AND bank_account='{filters.source_bank_acc}'
        """, as_dict=True
    ) or []

    return data
