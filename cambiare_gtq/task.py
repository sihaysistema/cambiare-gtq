# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def run_every_ten_mins():
	tester = frappe.new_doc("Configuration Cambiare")
	tester.data = 'minute'
	tester.save()

def all():
	tester = frappe.new_doc("Configuration Cambiare")
	tester.data = 'all'
	tester.save()

def daily():
	tester = frappe.new_doc("Configuration Cambiare")
	tester.data = 'daily'
	tester.save()

def hourly():
	tester = frappe.new_doc("Configuration Cambiare")
	tester.data = 'hourly'
	tester.save()