# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from cambiare_gtq.api_cambiare import preparar_peticion_banguat


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
    estado = verificar_configuracion('Cada Dia')
    return estado


def hourly():
    '''Se ejecuta cada 60 minutos'''
    estado = verificar_configuracion('Cada Hora')
    return estado


def weekly():
    '''Se ejecuta cada semana'''
    estado = verificar_configuracion('Cada Semana')
    return estado


def monthly():
    '''Se ejecuta cada mes'''
    estado = verificar_configuracion('Cada Mes')
    return estado


def verificar_configuracion(opt):
    '''Funcion para verificar la configuracion de cambiare

    Args:
        opt: puede ser "Cada Hora", "Cada Dia", "Cada Semana", "Cada Mes",
        para configurarlo a la medida ver el archivo hooks.py y utilizar CRON

    Returns:
        Retorna mensajes con la descripcion status de lo procesado
    '''

    configuracion = frappe.get_doc('Configuration Cambiare')  # Obtiene data del dt

    # Si el servicio esta activo osea igual a cero
    if configuracion.desactivar_consultas == 0:
        # SI la frecuencia configurada es decir, cada dia, hora, etc ...
        # son iguales a la que se le esta pasando por parametro, procede
        if str(configuracion.frecuencia) == opt:
            # Obtiene el cambio del dia USD
            estado_cambio_dia = preparar_peticion_banguat('1')

            # Obtiene el tipo cambio del dia en base a codigos de moneda
            tipo_cambio_monedas = preparar_peticion_banguat('6')

            return estado_cambio_dia, tipo_cambio_monedas
        else:
            # No hara nada
            pass
    else:
        return 'Servicio desactivado por usuario'
