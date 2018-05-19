# -*- coding: utf8 -*-
#The line above makes the file utf-8 readable, meaning you can use spanish latin accent characters in comments and other goodies
# Source: https://www.python.org/dev/peps/pep-0263/
import datetime
#Importa el modulo requests de Python
import requests
#import xmltodict

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# es-GT: Variables comunes para los tags del XML.
var0_xml_ver = '1.0'
var1_encoding = 'utf-8'
var2_envelope = 'Envelope'
var3_xsi = 'http://www.w3.org/2001/XMLSchema-instance'
var4_xsd = 'http://www.w3.org/2001/XMLSchema'
var5_soap = 'http://schemas.xmlsoap.org/soap/envelope/'
var6_body = 'Body'
var8_xmlns = 'http://www.banguat.gob.gt/variables/ws/'
# es-GT: Listado de las operaciones ofrecidas por banguat para el Tipo de Cambio
operacion_ofrecida = ['TipoCambioDia','TipoCambioDiaString','TipoCambioFechaInicial','TipoCambioFechaInicialMoneda','TipoCambioRango','TipoCambioRangoMoneda','Variables','VariablesDisponibles']

# TipoCambioDia: Devuelve el cambio del día en dólares
# TipoCambioDiaString: Devuelve el cambio del día en dólares
# TipoCambioFechaInicial: Despliega la información del tipo de cambio, en dólares, desde una fecha dada hasta el día corriente. (Formato: fecha_ini=dd/mm/aaaa).
# TipoCambioFechaInicialMoneda: Despliega la información para la variable indicada a partir de una fecha y moneda indicada. (Formato: fecha_ini=dd/mm/aaaa moneda=02).
# TipoCambioRango: Despliega la información para dólares en el período de tiempo dado. (Formato: fecha_ini=dd/mm/aaaa fecha_fin=dd/mm/aaaa)
# TipoCambioRangoMoneda: Despliega la información para la variable indicada en el período de tiempo y la moneda dada. (Formato: fecha_ini=dd/mm/aaaa fecha_fin=dd/mm/aaaa moneda=02)
# Variables: Despliega el tipo de cambio correspondiente a una variable (moneda) dada. (Formato: moneda=2)
# VariablesDisponibles: Despliega las variables (con relació


# es-GT: Funcion que genera el XML
# es-GT: WebService Banguat: Devuelve el cambio del día en dólares
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioDia
def TipoCambioDia():
    tag7_xml_servicio = operacion_ofrecida[0]
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}" />
    </soap:{9}>
    </soap:{10}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,var6_body,var2_envelope)
    return str(banguat_xml)

# es-GT: Funcion que genera el XML
# es-GT: WebService Banguat: Devuelve el cambio del día en dólares, string
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioDiaString
def TipoCambioDiaString():
    tag7_xml_servicio = operacion_ofrecida[1]
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}" />
    </soap:{9}>
    </soap:{10}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,var6_body,var2_envelope)
    return str(banguat_xml)

# es-GT: Funcion que genera el XML
# es-GT: Despliega la información del tipo de cambio, en dólares, desde una fecha dada hasta el día corriente. (Formato: fecha_ini=dd/mm/aaaa).
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioFechaInicial
def TipoCambioFechaInicial():
    tag7_xml_servicio = operacion_ofrecida[2]
    tag9_fecha_ini = '02/05/2018'
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}">
    <fechainit>01/05/2018</fechainit>
    </{9}>
    </soap:{10}>
    </soap:{11}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,tag7_xml_servicio,var6_body,var2_envelope)
    return str(banguat_xml)

# es-GT: Funcion que genera el XML
# es-GT: Despliega la información para la variable indicada a partir de una fecha y moneda indicada. (Formato: fecha_ini=dd/mm/aaaa moneda=02).
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioFechaInicialMoneda
def TipoCambioFechaInicialMoneda(fecha_ini, moneda):
    tag7_xml_servicio = operacion_ofrecida[3]
    tag9_fecha_ini = fecha_ini
    var_moneda = moneda
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}">
    <fechainit>{9}</fechainit>
    <moneda>{10}</moneda>
    </{11}>
    </soap:{12}>
    </soap:{13}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,tag9_fecha_ini,var_moneda,tag7_xml_servicio,var6_body,var2_envelope)
    return str(banguat_xml)

# es-GT: Funcion que genera el XML
# es-GT: Despliega la información para la variable indicada a partir de una fecha y moneda indicada. (Formato: fecha_ini=dd/mm/aaaa moneda=02).
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioFechaInicialMoneda
def TipoCambioRango(fecha_ini, fecha_fin):
    tag7_xml_servicio = operacion_ofrecida[4]
    tag9_fecha_ini = fecha_ini
    tag10_fecha_fin = fecha_fin
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}">
    <fechainit>{9}</fechainit>
    <fechafin>{10}</fechafin>
    </{11}>
    </soap:{12}>
    </soap:{13}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,tag9_fecha_ini,tag10_fecha_fin,tag7_xml_servicio,var6_body,var2_envelope)
    return str(banguat_xml)
    
# es-GT: Funcion que genera el XML
# es-GT: Despliega la información para la variable indicada a partir de una fecha y moneda indicada. (Formato: fecha_ini=dd/mm/aaaa moneda=02).
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=TipoCambioFechaInicialMoneda
def TipoCambioRangoMoneda(fecha_ini, fecha_fin, moneda):
    tag7_xml_servicio = operacion_ofrecida[5]
    tag9_fecha_ini = fecha_ini
    tag10_fecha_fin = fecha_fin
    var_moneda = moneda
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}">
    <fechainit>{9}</fechainit>
    <fechafin>{10}</fechafin>
    <moneda>{11}</moneda>
    </{12}>
    </soap:{13}>
    </soap:{14}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,tag9_fecha_ini,tag10_fecha_fin,var_moneda,tag7_xml_servicio,var6_body,var2_envelope)
    return str(banguat_xml)
    
# es-GT: Funcion que genera el XML
# es-GT: WebService Banguat: Despliega el numero de variable y su correspondiente moneda disponibles para consulta.
# es-GT: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=Variables
def Variables(variable):
    tag7_xml_servicio = operacion_ofrecida[6]
    variables = variable
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}"/>
    <variable>{9}</variable>
    </soap:{10}>
    </soap:{11}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,variables,var6_body,var2_envelope)
    return str(banguat_xml)

# es-GT: Funcion que genera el XML
# es-GT: WebService Banguat: Despliega las variables (con relación a la moneda) disponibles para consulta.
# es-GT: hhttp://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=VariablesDisponibles
def VariablesDisponibles():
    tag7_xml_servicio = operacion_ofrecida[7]
    banguat_xml = """<?xml version="{0}" encoding="{1}"?>
    <soap:{2} xmlns:xsi="{3}" xmlns:xsd="{4}" xmlns:soap="{5}">
    <soap:{6}>
    <{7} xmlns="{8}" />
    </soap:{9}>
    </soap:{10}>
    """.format(var0_xml_ver,var1_encoding,var2_envelope,var3_xsi,var4_xsd,var5_soap,var6_body,tag7_xml_servicio,var8_xmlns,var6_body,var2_envelope)
    return str(banguat_xml)