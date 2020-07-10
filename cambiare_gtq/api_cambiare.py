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
import datetime
import re

def crear_tipo_cambio_gtq(cambio, fecha, factor_1usd_xgtq, moneda_cod_letras='USD'):
    '''Funcion para crear registros en custom doctype (Currency Exchange GTQ)

    Args:
        cambio: monto conversion
        fecha: fecha del tipo cambio
        moneda_cod_letras: Codigo de moneda ISO

    Returns:
        Retorna mensajes con la descripcion status de lo procesado
    '''

    try:

        if moneda_cod_letras != 'USD':
            result = float(factor_1usd_xgtq) / float(cambio)
            any_to_gtq = frappe.new_doc("Currency Exchange GTQ")  # Crea un nuevo registro para el doctype
            any_to_gtq.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()  # frappe.utils.nowdate()
            any_to_gtq.from_currency = moneda_cod_letras
            any_to_gtq.to_currency = 'GTQ'
            any_to_gtq.exchange_rate = float(result)
            any_to_gtq.for_buying = True
            any_to_gtq.for_selling = True
            any_to_gtq.save()

        else:
            usd_to_gtq = frappe.new_doc("Currency Exchange GTQ")  # Crea un nuevo registro para el doctype
            usd_to_gtq.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()  # frappe.utils.nowdate()
            usd_to_gtq.from_currency = moneda_cod_letras
            usd_to_gtq.to_currency = 'GTQ'
            usd_to_gtq.exchange_rate = float(cambio)
            usd_to_gtq.for_buying = True
            usd_to_gtq.for_selling = True
            usd_to_gtq.save()

    except:
        return _('Could not create USD to GTQ exchange rate, please try generating GTQ manually')

    else:
        try:

            if moneda_cod_letras != 'USD':
                result = float(factor_1usd_xgtq) / float(cambio)
                any_to_usd = frappe.new_doc("Currency Exchange GTQ")
                any_to_usd.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()   # frappe.utils.nowdate()
                any_to_usd.from_currency = 'GTQ'
                any_to_usd.to_currency = moneda_cod_letras
                any_to_usd.exchange_rate = 1/float(result)
                any_to_usd.for_buying = True
                any_to_usd.for_selling = True
                any_to_usd.save()

            else:
                gtq_to_usd = frappe.new_doc("Currency Exchange GTQ")
                gtq_to_usd.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()   # frappe.utils.nowdate()
                gtq_to_usd.from_currency = 'GTQ'
                gtq_to_usd.to_currency = moneda_cod_letras
                gtq_to_usd.exchange_rate = 1/float(cambio)
                gtq_to_usd.for_buying = True
                gtq_to_usd.for_selling = True
                gtq_to_usd.save()

        except:
            return 'No se pudo crear tipo cambio GTQ to USD, intentar manualmente GTQ'
        else:
            return 'Currency Exchange GTQ OK'

def crear_cambio_moneda(cambio, fecha, factor_1usd_xgtq, moneda_cod_letras='USD'):
    '''Funcion para crear registros en doctype (Currency Exchange)

    Args:
        cambio: monto conversion
        fecha: fecha del tipo cambio
        moneda_cod_letras: Codigo de moneda ISO

    Returns:
        Retorna mensajes con la descripcion status de lo procesado
    '''

    try:
        if moneda_cod_letras != 'USD':
            result = float(factor_1usd_xgtq) / float(cambio)
            any_to_gtq = frappe.new_doc("Currency Exchange")  # Crea un nuevo registro para el doctype
            any_to_gtq.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()  # frappe.utils.nowdate()
            any_to_gtq.from_currency = moneda_cod_letras
            any_to_gtq.to_currency = 'GTQ'
            any_to_gtq.exchange_rate = float(result)
            any_to_gtq.for_buying = True
            any_to_gtq.for_selling = True
            any_to_gtq.save()

        else:
            usd_to_gtq = frappe.new_doc("Currency Exchange")
            usd_to_gtq.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()  # frappe.utils.nowdate()
            usd_to_gtq.from_currency = moneda_cod_letras
            usd_to_gtq.to_currency = 'GTQ'
            usd_to_gtq.exchange_rate = float(cambio)
            usd_to_gtq.for_buying = True
            usd_to_gtq.for_selling = True
            usd_to_gtq.save()
    except:
        return 'No se pudo crear tipo cambio USD to GTQ, intentar manualmente'
    else:
        try:
            if moneda_cod_letras != 'USD':
                result = float(factor_1usd_xgtq) / float(cambio)
                any_to_usd = frappe.new_doc("Currency Exchange")
                any_to_usd.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()   # frappe.utils.nowdate()
                any_to_usd.from_currency = 'GTQ'
                any_to_usd.to_currency = moneda_cod_letras
                any_to_usd.exchange_rate = 1/float(result)
                any_to_usd.for_buying = True
                any_to_usd.for_selling = True
                any_to_usd.save()
            else:
                gtq_to_usd = frappe.new_doc("Currency Exchange")
                gtq_to_usd.date = datetime.datetime.strptime(fecha, '%d/%m/%Y').date()   # frappe.utils.nowdate()
                gtq_to_usd.from_currency = 'GTQ'
                gtq_to_usd.to_currency = moneda_cod_letras
                gtq_to_usd.exchange_rate = 1/float(cambio)
                gtq_to_usd.for_buying = True
                gtq_to_usd.for_selling = True
                gtq_to_usd.save()
        except:
            return 'No se pudo crear tipo cambio GTQ to USD, intentar manualmente'
        else:
            return 'Currency Exchange OK'

@frappe.whitelist()
def preparar_peticion_banguat(opt, fecha_ini=0, fecha_fin=0, moneda=2):
    '''Funcion encargada de preparar y enviar la peticion hacia el banco de guatemala, para mas
    info puede ver las opciones aqui: https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx

    Args:
        opt: numero de peticion a preparar
        fecha_ini: fecha inicial
        fecha_fin: fecha final
        moneda: codigo de monedas del banco de guatemala, (ver variables disponibles en
        https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=Variables)

    Returns:
        Retorna el status segun la opcion escogida a consumir del webservice
    '''

    # Cambio del dia en dolares
    if opt == '1':
        cambio_del_dia = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioDia xmlns="http://www.banguat.gob.gt/variables/ws/" />
        </soap12:Body>
        </soap12:Envelope>'''

        # Usamos la libreria xmltodict, para parsearlo a diccionario
        cambio_dia = xmltodict.parse(consultar_a_banguat(cambio_del_dia))
        # accesamos al contenido de varDolar con la ayuda de xmltodict
        cambio = cambio_dia['soap:Envelope']['soap:Body']['TipoCambioDiaResponse'] \
                           ['TipoCambioDiaResult']['CambioDolar'] \
                           ['VarDolar']

        # Funciones para registrar el tipo de cambio consumido del webservice en el ERPNEXT
        status = crear_cambio_moneda(cambio['referencia'], cambio['fecha'], '7.80')
        status_custom = crear_tipo_cambio_gtq(cambio['referencia'], cambio['fecha'], '7.80')

        return status

    # WIP:
    # Despliega la informacion del tipo de cambio, en dolares, desde una fecha dada hasta el dia corriente
    # (Formato: fecha_ini=dd/mm/aaaa).
    elif opt == '2':
        tipo_cambio_fecha_inicial = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
        <TipoCambioFechaInicial xmlns="http://www.banguat.gob.gt/variables/ws/">
            <fechainit>{}</fechainit>
        </TipoCambioFechaInicial>
        </soap12:Body>
        </soap12:Envelope>'''.format(fecha_ini)

    # WIP
    # Despliega la informacion para la variable indicada a partir de una fecha y moneda indicada.
    # (Formato: fecha_ini=dd/mm/aaaa moneda=02).
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

    # WIP
    # Despliega la informacion para dolares en el periodo de tiempo dado.
    # (Formato: fecha_ini=dd/mm/aaaa fecha_fin=dd/mm/aaaa)
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

    # WIP:
    # Despliega la informacion para la variable indicada en el periodo de tiempo y la moneda dada.
    # (Formato: fecha_ini=dd/mm/aaaa fecha_fin=dd/mm/aaaa moneda=02)
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

    # Despliega el tipo de cambio correspondiente a una variable (moneda) dada. (Formato: moneda=2)
    elif opt == '6':
        # Monedas hardcode
        # monedas = [
        #     {'cod': 'MXN', 'mon': 18},
        #     {'cod': 'HNL', 'mon': 19},
        #     {'cod': 'SVC', 'mon': 17},
        #     {'cod': 'NIO', 'mon': 21},
        #     {'cod': 'CRC', 'mon': 16},
        #     {'cod': 'CAD', 'mon': 7},
        #     {'cod': 'EUR', 'mon': 24}
        # ]

        # en_US:  We prepare a default USD to GTQ query because we need it to convert other currencies to GTQ. Banguat webservice has USD as currency reference
        cambio_usd = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <TipoCambioDia xmlns="http://www.banguat.gob.gt/variables/ws/" />
        </soap12:Body>
        </soap12:Envelope>'''
        # en_US: We consult the webservice to generate a response
        exchange = xmltodict.parse(consultar_a_banguat(cambio_usd))
        # en_US: We access the var value (X) from the response, this is 1 USD to X GTQ
        factor_1usd_xgtq = exchange['soap:Envelope']['soap:Body']['TipoCambioDiaResponse']['TipoCambioDiaResult']['CambioDolar']['VarDolar']

        monedas = obtener_listado_monedas()
        if monedas != False:  # en_US: We find out if currencies exist to generate exchange records es: Averiguamos si existen monedas para generar registros de cambio.
            for moneda in monedas:
                variables = '''<?xml version="1.0" encoding="utf-8"?>
                <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Body>
                    <Variables xmlns="http://www.banguat.gob.gt/variables/ws/">
                    <variable>{}</variable>
                    </Variables>
                </soap12:Body>
                </soap12:Envelope>'''.format(moneda['mon'])

                # Obtiene el cambio del dia y Convierte de la respuesta XML a diccionario
                cambio_dia = xmltodict.parse(consultar_a_banguat(variables))
                # Accedemos al valor Var
                cambio = cambio_dia['soap:Envelope']['soap:Body']['VariablesResponse'] \
                                ['VariablesResult']['CambioDia']['Var']

                # Crea registro en Currency Exchange
                status = crear_cambio_moneda(cambio['venta'], cambio['fecha'], factor_1usd_xgtq['referencia'], moneda_cod_letras=moneda['cod'])
                # Crea registro en Currency Exchange GTQ
                status_custom_dt = crear_tipo_cambio_gtq(cambio['venta'], cambio['fecha'], factor_1usd_xgtq['referencia'], moneda_cod_letras=moneda['cod'])

            return status
        else:
            return False

    # Despliega las variables (con relacion a la moneda) disponibles para consulta.
    # Todas las monedas disponibles del webservice
    elif opt == '7':
        variables_disponibles = '''<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
            <VariablesDisponibles xmlns="http://www.banguat.gob.gt/variables/ws/" />
        </soap12:Body>
        </soap12:Envelope>'''

        v_response = consultar_a_banguat(variables_disponibles)
        res = xmltodict.parse(v_response)
        monedas_disp = res['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse'] \
                          ['VariablesDisponiblesResult']['Variables']['Variable']

        listado_m = []
        for moneda in monedas_disp:
            # listado_m.append((moneda['descripcion']))
            detalle = '{0} - {1}'.format(moneda['moneda'], str(moneda['descripcion']))
            listado_m.append(detalle)

        return listado_m

    else:
        pass


def consultar_a_banguat(peticion):
    '''Funcion encargada de consumir el webservice del banco de Guatemala, segun el
    tipo de peticion que se le pase por argumento

    Args:
        peticion: peticion XML a consumir

    Returns:
        Retorna XML con data de x peticion
    '''
    # WSDL SOAP BANCO GUATEMALA
    url = "http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?WSDL"
    cabeceras = {"content-type": "text/xml"}

    try:
        response = requests.post(url, data=peticion, headers=cabeceras)
        respuesta = response.content
    except:
        frappe.msgprint(_('Inconveniente al tratar de obtener informacion del Banco de Guatemala: '+str(frappe.get_traceback())))
    else:
        return response.content


def obtener_listado_monedas():
    '''Funcion encargada de obtener las monedas configuradas de la tabla hija
       Currency Available del doctype padre Configuracion Cambiare GTQ y las retorna
       en un formato especial para ser procesadas.  Averigua cuales monedas desea el usuario
       para generar conversiones.

    Args:
        Ninguno

    Returns:
        Retorna un listado de monedas con el siguiente formato:
        monedas = [
            {'cod': 'USD', 'mon': 2}
            {'cod': 'MXN', 'mon': 18},
            {'cod': 'HNL', 'mon': 19},
            {'cod': 'SVC', 'mon': 17},
            {'cod': 'NIO', 'mon': 21},
            {'cod': 'CRC', 'mon': 16},
            {'cod': 'CAD', 'mon': 7},
            {'cod': 'EUR', 'mon': 24}
        ]
    '''
    # Selecciona las monedas disponibles que han sido seleccionadas en configuracion cambiare
    # omitiendo los duplicados, como lista de diccionarios.
    monedas_db = frappe.db.sql('''SELECT DISTINCT moneda 
                                FROM `tabAvailable Currencies`''', as_dict=True)
    # Contendra las monedas
    mone_ok = []

    if len(monedas_db) > 0:  # Si existe por lo menos un elemento
        for mone in monedas_db:
            # Con expresion regular, separamos el string donde se encuentre un guión
            x = re.split('-', mone['moneda'])  # -> ['1 ', ' Quetzales ', ' GTQ']

            mone_ok.append({
                'cod': x[2].strip(),  # -> 'GTQ'
                'mon': int(x[0].strip())  # -> '1'
            })

        return mone_ok
    else:
        return False  # Si no hay data return False