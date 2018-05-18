# -*- coding: utf8 -*-
#The line above makes the file utf-8 readable, meaning you can use spanish latin accent characters in comments and other goodies
# Source: https://www.python.org/dev/peps/pep-0263/
from datetime import datetime
#Importa el modulo requests de Python
import requests
#import xmltodict

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#Paso 3: Escupir la data en pantalla.

try:
    # es-GT: Agregamos la dirección del web service del BANGUAT a una variable
    url = str('http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx')
    # es-GT: Hacemos el request básico y asignamos la respuesta a una variable tambien
    r = requests.get(url)
    # es-GT: Verificamos el estatus del web service usando status_code
    r.status_code
    # es-GT: Imprimimos en pantalla el resultado del status code
    print r.status_code
    # es-GT: Convertimos un estatus de 200 o OK a un boolean de verdadero
    r.status_code == requests.codes.ok
    # es-GT: Estatus codes de distintas opciones
    requests.codes['temporary_redirect']
    requests.codes.teapot
    requests.codes['o/']

# CABECERAS: Indican el tipo de datos FUNCIONA OK!!!
#headers = {"content-type": "text/xml"}
# FUNCIONA OK!!!
#response = requests.post(url, data=envio_datos, headers=headers, timeout=15)
#respuesta = response.content
except:
#frappe.msgprint(_('Error en la Comunicacion al servidor de INFILE. Verifique al PBX: +502 2208-2208'))
    print('se jodio la cosa')


