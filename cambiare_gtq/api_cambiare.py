# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import requests
import json
import xml.dom.minidom as beauty_xml
import xmltodict

@frappe.whitelist()
def preparar_peticion_banguat(opt, fecha_ini=0, fecha_fin=0, moneda=2):

    if opt == '1':
        cambio_del_dia = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioDia xmlns="http://www.banguat.gob.gt/variables/ws/" />
        </soap12:Body>
        </soap12:Envelope>'''

        # return consultar_a_banguat(cambio_del_dia)
        cambio_dia = xmltodict.parse(consultar_a_banguat(cambio_del_dia))
        cambio = cambio_dia['soap:Envelope']['soap:Body']['TipoCambioDiaResponse'] \
                           ['TipoCambioDiaResult']['CambioDolar'] \
                           ['VarDolar']

        # frappe.msgprint(_(str(cambio['fecha']), str(cambio['referencia'])))
        return cambio['referencia'], cambio['fecha']

    elif opt == '2':
        tipo_cambio_fecha_inicial = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
        <TipoCambioFechaInicial xmlns="http://www.banguat.gob.gt/variables/ws/">
            <fechainit>{}</fechainit>
        </TipoCambioFechaInicial>
        </soap12:Body>
        </soap12:Envelope>'''.format(fecha_ini)

    elif opt == '3':
        tipo_cambio_fecha_inicial_moneda ='''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioFechaInicialMoneda xmlns="http://www.banguat.gob.gt/variables/ws/">
            <fechainit>{0}</fechainit>
            <moneda>{1}</moneda>
            </TipoCambioFechaInicialMoneda>
        </soap12:Body>
        </soap12:Envelope>'''.format(fecha_ini, moneda)

    elif opt == '4':
        tipo_cambio_rango = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioRango xmlns="http://www.banguat.gob.gt/variables/ws/">
            <fechainit>{0}</fechainit>
            <fechafin>{1}</fechafin>
            </TipoCambioRango>
        </soap12:Body>
        </soap12:Envelope>'''.format(fecha_ini, fecha_fin)

    elif opt == '5':
        tipo_cambio_rango_moneda = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioRangoMoneda xmlns="http://www.banguat.gob.gt/variables/ws/">
            <fechainit>{0}</fechainit>
            <fechafin>{1}</fechafin>
            <moneda>{2}</moneda>
            </TipoCambioRangoMoneda>
        </soap12:Body>
        </soap12:Envelope>'''.format(fecha_ini, fecha_fin, moneda)

    elif opt == '6':
        variables = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <Variables xmlns="http://www.banguat.gob.gt/variables/ws/">
            <variable>{}</variable>
            </Variables>
        </soap12:Body>
        </soap12:Envelope>'''.format(moneda)

    elif opt == '7':
        variables_disponibles = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <VariablesDisponibles xmlns="http://www.banguat.gob.gt/variables/ws/" />
        </soap12:Body>
        </soap12:Envelope>'''

        v_response = consultar_a_banguat(variables_disponibles)
        # res = xmltodict.parse(v_response)
        # monedas_disp = res['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable']

        # listado_m = []
        # for moneda in monedas_disp:
        #     listado_m.append((moneda['descripcion']))

        # return listado_m
        frappe.msgprint(_(str(v_response)))
    else:
        pass


def consultar_a_banguat(peticion):
    # WSDL SOAP BANCO GUATEMALA
    url = "http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?WSDL"
    cabeceras = {"content-type": "text/xml"}

    try:
        response = requests.post(url, data=peticion, headers=cabeceras)
        respuesta = response.content
    except:
        frappe.msgprint(_('error consulta'))
    else:
        # frappe.msgprint(_(response.content))
        return response.content

    # prueba = consultar()
    # print(prueba.status_code)

    # contenido = beauty_xml.parseString(prueba.content)

    # with open('respuesta2.xml', 'w') as f:
    #     f.write(contenido.toprettyxml())