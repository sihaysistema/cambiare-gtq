# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from api_cambiare import preparar_peticion_banguat


def test():
	'''Funcion para prueba, se ejecuta cada minuto '''
	estado = verificar_configuracion('Cada Hora')
	return estado
	# frappe.publish_realtime(event='eval_js', message='alert("{0}")'.format(estado), user=frappe.session.user)


def run_every_ten_mins():
	'''Se ejecuta cada 10 minutos'''
	pass


def all():
	'''Se ejecuta cada 4 minutos'''
	pass


def daily():
	'''Se ejecuta cada 24 horas'''
	estado = verificar_configuracion('Cada dia')
	return


def hourly():
	'''Se ejecuta cada 60 minutos'''
	estado = verificar_configuracion('Cada Hora')
	return


def weekly():
	'''Se ejecuta cada semana'''
	pass


def monthly():
	'''Se ejecuta cada mes'''
	pass


def verificar_configuracion(opt):
	'''Funcion para verificar la configuracion de cambiare'''

	configuracion = frappe.get_doc('Configuration Cambiare')

	# Si el servicio esta activo
	if configuracion.desactivar_consultas == 0:
		if str(configuracion.frecuencia) == opt:
			estado = preparar_peticion_banguat('1')
			return estado
		else:
			return
	else:
		return 'Servicio desactivado por usuario'
