# -*- coding: utf8 -*-
#The line above makes the file utf-8 readable, meaning you can use spanish latin accent characters in comments and other goodies
# Source: https://www.python.org/dev/peps/pep-0263/
from datetime import datetime
#Importa el modulo requests de Python
import requests
#import xmltodict
# Importa las funciones que estructuran el xml de banguat
import data_banguat
from data_banguat import TipoCambioDia, TipoCambioDiaString, TipoCambioFechaInicial, TipoCambioFechaInicialMoneda, TipoCambioRango, TipoCambioRangoMoneda, Variables, VariablesDisponibles
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
nl = '\n'
space = ' '

#Compras
# Una factura de compra en USD, implica una COMPRA de USD. Porque tendré que comprar los dolares para comprar los articulos en la factura.
# Una factura de venta en USD, implica una VENTA de USD.  Porque tendré que vender los dolares para obtener quetzales a los ingresos de la empresa.

# es-GT: Variables temporales
# es-GT: Fecha debe ser un string de dd/mm/aaaa
fecha_ini = '01/05/2018'
fecha_fin = '10/05/2018'
fecha_test = datetime.date
# es-GT: Hay varios tipos de moneda que convierten a Quetzal, es necesario correlacionar el numero de variable de la moneda con el nombre oficial de la moneda.
# es-GT: Esto se logra con enviar la opcion: http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?op=Variables

moneda = 2
variable = 2
# es-GT: Tiempo máximo para esperar respuesta si el servicio está activo. Segundos
# es-GT: Esto busca minimizar el tiempo de espera.  Si el servicio no responde adecuadamente en este tiempo, genera un timeout.
timeout_verificacion_status = 1
if timeout_verificacion_status > 1:
    secs = 'segundos'
else:
    secs = 'segundo'

# Paso 1: Obtener datos del servidor: Estatus, Headers

try:
    # es-GT: Agregamos la dirección del web service del BANGUAT a una variable
    url = str('http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx')
    # es-GT: Hacemos el request básico y asignamos la respuesta a una variable tambien
    r = requests.get(url, timeout=timeout_verificacion_status)
    # es-GT: Verificamos el estatus del web service usando status_code
    r.status_code
    # es-GT: Imprimimos en pantalla el resultado del status code
    #print ('El estatus del web service es: ' + str(r.status_code))
    # es-GT: Convertimos un estatus de 200 o OK a un boolean de verdadero o falso.
    status_bool = r.status_code == requests.codes.ok
    # es-GT: Imprimimos en pantalla el resultado del status code según su resultado
    if status_bool == True:
        print('El estatus del web service indica que esta funcionando correctamente')
        # es-GT: Por lo tanto corremos la solicitud de datos.
        print('Intentando obtener datos del Banco de Guatemala... espere un momento porfavor')
        try:
            # es-GT: Indicamos los headers o cabeceras, respecto al tipo de datos que enviaremos
            headers = {"content-type": "text/xml"}
            # es-GT: Hacemos el request con POST, indicando el url, los datos, los headers y un timeout
            response = requests.post(url, data=VariablesDisponibles(), headers=headers, timeout=5)
            # es-GT: Asignamos la respuesta a una variable para poder trabajarla
            respuesta = response.content
            # es-GT: Imprimimos la respuesta en consola
            print ('Respuesta del web service:' + nl + respuesta)
        except:
        #frappe.msgprint(_('Error en la Comunicacion al servidor de INFILE. Verifique al PBX: +502 2208-2208'))
            print('Algo se fregó en el pedido de datos')
        #print('La funcion retorna: ' + nl + TipoCambioDia())
        #print VariablesDisponibles()

    else:
        print('El servicio no responde despues de ' + str(timeout_verificacion_status) + space + str(secs) +'. Intente de nuevo más tarde.')
        # es-GT: Estatus codes de distintas opciones

#    requests.codes['temporary_redirect']
#    requests.codes.teapot
#    requests.codes['o/']

except:
    #frappe.msgprint(_('Error en la Comunicacion'))
    print 'a'