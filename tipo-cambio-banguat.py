# -*- coding: utf8 -*-
#The line above makes the file utf-8 readable, meaning you can use spanish latin accent characters in comments and other goodies
# Source: https://www.python.org/dev/peps/pep-0263/
from datetime import datetime
#Importa el modulo requests de Python
import requests
import xmltodict
# Importa las funciones que estructuran el xml de banguat
import data_banguat
from data_banguat import TipoCambioDia, TipoCambioDiaString, TipoCambioFechaInicial, TipoCambioFechaInicialMoneda, TipoCambioRango, TipoCambioRangoMoneda, Variables, VariablesDisponibles
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
nl = '\n'
space = ' '
datos_en_file_xml = open('variables.xml', 'r').read()

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
    secs_verify = 'segundos'
else:
    secs_verify = 'segundo'
# es-GT: Tiempo máximo para esperar respuesta de datos. Segundos
# es-GT: Esto busca minimizar el tiempo de espera.  Si el servicio no envía datos adecuadamente en este tiempo, genera un timeout.
timeout_recepcion_status = 1
if timeout_recepcion_status > 1:
    secs_rec = 'segundos'
else:
    secs_rec = 'segundo'

# Paso 1: Obtener datos del servidor: Estatus, Headers
####  TODO    ESTO ES SOLO PRUEBA
respuesta = datos_en_file_xml
# es-GT: Imprimimos la respuesta en consola
#print ('Respuesta del web service:' + nl + respuesta)
respuesta_dict = xmltodict.parse(respuesta)
#print ('Respuesta del web service como diccionario:' + nl + str(respuesta_dict))
#print respuesta_dict
# accesing the keys of first dict element: respuesta_dict['soap:Envelope'].keys()
# accesing the keys of the second dict element: respuesta_dict['soap:Envelope']['soap:Body'].keys()
# El completo nos lleva a poder parsear por cada uno de los items internos. Alli hay que ir imprimiendo uno por uno. La respuesta es un diccionario donde la llave es un numero, y el valor de la lalve es la moneda

# Este es un listado respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable']
# El listado contiene elementos de diccionario:  moneda y descripcion.  Llaves: Moneda, Descripcion.  Valores:  LOs que quiero de cada uno.
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][0]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][0]['descripcion']

print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][1]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][1]['descripcion']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][2]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][2]['descripcion']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][3]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][3]['descripcion']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][4]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][4]['descripcion']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][5]['moneda']
print respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][5]['descripcion']
# Asignamos la respuesta del XML parseada a diccionario/lista a una variable
lista_respuesta = respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable']
largo_lista_respuesta = len(lista_respuesta)
# Imprimimos el largo de la lista
print len(lista_respuesta)
# Creamos una lista
lista_test1 = []

# es-GT: Compresníon de lista para los elementos del diccionario. Los quiero en lista para
for x in range(largo_lista_respuesta):
    moneda1 = respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][x]['moneda']
    desc1 = respuesta_dict['soap:Envelope']['soap:Body']['VariablesDisponiblesResponse']['VariablesDisponiblesResult']['Variables']['Variable'][x]['descripcion']
    lista_inside = []
    lista_inside.append(moneda1)
    lista_inside.append(desc1)
    lista_test1.append(lista_inside)

largo_lista_test1 = len(lista_test1)
for x in range(largo_lista_test1):
    print(*lista_test1[x], sep='\n')
#Obtenga la moneda
#Obtenga la descripcion
# Lista que va adentro
#Agregue a la lista nueva.
#lista_test1.append()

#test1 = dict((el,0) for el in dict1)


'''
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
            #headers = {"content-type": "text/xml"}
            # es-GT: Hacemos el request con POST, indicando el url, los datos, los headers y un timeout
            #response = requests.post(url, data=VariablesDisponibles(), headers=headers, timeout=5)
            # es-GT: Asignamos la respuesta a una variable para poder trabajarla
            #respuesta = response.content
            ####  TODO    ESTO ES SOLO PRUEBA
            respuesta = datos_en_file_xml
            # es-GT: Imprimimos la respuesta en consola
            print ('Respuesta del web service:' + nl + respuesta)
            respuesta_dict = xmltodict.parse(respuesta)
            #print ('Respuesta del web service como diccionario:' + nl + str(respuesta_dict))
            print respuesta_dict.keys()
            #descripciones = (documento_descripcion['S:Envelope']['S:Body']['ns2:registrarDteResponse']['return']['descripcion'])
        except:
        #frappe.msgprint(_('Error en la Comunicacion al servidor de INFILE. Verifique al PBX: +502 2208-2208'))
            print('Algo se fregó en el pedido de datos.')
    else:
        print(' El servicio no responde despues de ' + str(timeout_verificacion_status) + space + str(secs_verify) +'. Intente de nuevo más tarde.')
        # es-GT: Estatus codes de distintas opciones
        # requests.codes['temporary_redirect']
        # requests.codes.teapot
        # requests.codes['o/']
except:
    #frappe.msgprint(_('Error en la Comunicacion'))
    print('El servicio no envía datos despues de ' + str(timeout_recepcion_status) + space + str(secs_rec) +'. Intente de nuevo más tarde.')
'''