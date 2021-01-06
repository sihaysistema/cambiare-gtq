# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import locale
import math

import frappe
from frappe import _
from numinwords import numinwords

__version__ = '1.3.0'


@frappe.whitelist()
def test1(num):
    hello = "hello world" + str(num)
    return hello


@frappe.whitelist()
def currency_in_words(amount, currency, cent_in_numb=0):
    '''
    Function that calls the numinwords pip package by Si Hay Sistema
    and then capitalizes the result, returning a properly capitalized sentence.
    https://pypi.org/project/numinwords/
    https://www.geeksforgeeks.org/string-capitalize-python/
    Arguments:
    Amount: Float number
    Currency: ISO4217 Currency code, eg. 'GTQ', 'USD'
    Cent in Number = 1  enables cent in numbers
    '''
    # mapa traducciones es
    mapa_es = {
        'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
        'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9'
    }

    if cent_in_numb:
        # Convierte el monto a palabras moneda
        words = numinwords(float(amount), lang='es')
        # Convierte el string en una lista, separando por la palabra 'punto'
        x2 = str(words).split('punto')

        # Validaciones
        if len(x2) == 1:  # si es numero entero
            return str(x2[0]).capitalize()

        elif len(x2) > 1:  # Si tiene centavos
            # Extrae los centavos del monto y lo convierte a numeros sobre 100
            # Extraccion texto de centavos y conversion a lista donde exstan espacio en blanco
            x3 = x2[1].strip().split(' ')

            if len(x3) > 1:  # Si los centavos son de mas de dos cifras
                return str(x2[0].strip() + ' con ' + str(mapa_es[x3[0]]) + str(mapa_es[x3[1]]) + '/100').capitalize()
            else:  # Si los centavos tiene una sola cifra
                return str(x2[0].strip() + ' con ' + str(mapa_es[x3[0]]) + '0' + '/100').capitalize()

    else:
        words = numinwords(float(amount), to='currency', lang='es', currency=currency)
        text = words.capitalize()
        return text


@frappe.whitelist()
def currency_in_words_hundred_fractions(amount, currency):
    '''
    Improved version of currency in words. This function obtains the amount, the currency,
    and a switch to include or exlcude the currency in the sentence.
    DEPENDENCIES:  The ttf font /apps/milconnect/milconnect/www/fonts/100fractions.ttf family: "HundredFractions"
    must be installed in the application. Otherwise, it will not work!
    '''
    # This function maps the amounts split at the decimal point
    amount_str = str(float(amount))
    left_of_decimal, right_of_decimal = map(int, str(amount_str).split(".", 1))
    words = numinwords(float(amount), to='currency', lang='es', currency=currency)
    units, cents = map(str,words.split("con", 1))
    units_in_words = units.capitalize()
    html_string = '<p class="">' + units_in_words + ' con ' + '<strong class="hundredfraction">' + hundred_fraction_selector(right_of_decimal) + '</strong>' + '</p>'
    return html_string


@frappe.whitelist()
def hundred_fraction_selector(cents):
    '''
    This functions takes a value from 1 to 99, and selects the proper
    character from the keyboard to return, such that when the hundred fraciton font is selected,
    the correct cents amount is displayed in the print format.
    '''
    switcher = {
        1:'1',
        2:'2',
        3:'3',
        4:'4',
        5:'5',
        6:'6',
        7:'7',
        8:'8',
        9:'9',
        10:'0',
        11:'a',
        12:'b',
        13:'c',
        14:'d',
        15:'e',
        16:'f',
        17:'g',
        18:'h',
        19:'i',
        20:'j',
        21:'k',
        22:'l',
        23:'m',
        24:'n',
        25:'o',
        26:'p',
        27:'q',
        28:'r',
        29:'s',
        30:'t',
        31:'u',
        32:'v',
        33:'w',
        34:'x',
        35:'y',
        36:'z',
        37:'A',
        38:'B',
        39:'C',
        40:'D',
        41:'E',
        42:'F',
        43:'G',
        44:'H',
        45:'I',
        46:'J',
        47:'K',
        48:'L',
        49:'M',
        50:'N',
        51:'O',
        52:'P',
        53:'Q',
        54:'R',
        55:'S',
        56:'T',
        57:'U',
        58:'V',
        59:'W',
        60:'X',
        61:'Y',
        62:'Z',
        63:'\u003A', # : COLON
        64:'\u003B', # ; SEMICOLON
        65:'\u003C', # < LESS-THAN SIGN
        66:'\u003D', # = EQUALS SIGN
        67:'\u003E', # > GREATER-THAN SIGN
        68:'\u003C', # ? QUESTION MARK
        69:'@', # '\u0040' # @ COMMERCIAL AT
        70:'[', # '\u005B' # [ LEFT SQUARE BRACKET
        71:'\u005C', # \ REVERSE SOLIDUS backslash "\"
        72:']', # '\u005D' # ] RIGHT SQUARE BRACKET
        73:'^', # '\u005B' # ^ CIRCUMFLEX ACCENT
        74:'_', # '\u005F' # _ LOW LINE
        75:'`', # '\u0060' # ` GRAVE ACCENT
        76:'{', # '\u007B' # { LEFT CURLY BRACKET
        77:'}', # '\u007D' # } RIGHT CURLY BRACKET
        78:'|', # '\u007C' # | VERTICAL LINE "bar"
        79:'!', # '\u0021' # ! EXCLAMATION MARK "exclam"
        80:'"', # '\u0022' # " QUOTATION MARK "quotedbl"
        81:'#', # '\u0023' # # NUMBER SIGN "numbersign"
        82:'$', # '\u0024' # $ DOLLAR SIGN "dollar"
        83:'\u0025', # '\u0025' # % PERCENT SIGN "quotedbl"
        84:'&', # '\u0026' # & AMPERSAND "ampersand"
        85:'\u0027', # '\u0027' # ' APOSTROPHE "quotesingle"
        86:'(', # '\u0028' # LEFT PARENTHESIS "parenleft"
        87:')', # '\u0029' # RIGHT PARENTHESIS "parenleft"
        88:'*', # '\u002A' # ASTERISK "asterisk"
        89:'+', # '\u002B' # PLUS SIGN "plus"
        90:',', # '\u002C' # COMMA "comma"
        91:'-', # '\u002D' # HYPHEN-MINUS "hyphen"
        92:'.', # '\u002E' # FULL STOP "period"
        93:'/', # '\u002F' # SOLIDUS "slash"  "forwardslash"
        94:'¡', # '\u00A1' # INVERTED EXCLAMATION MARK "exclamdown"
        95:'´', # '\u00B4' # ACUTE ACCENT "acute"
        96:'·', # '\u00B7' # MIDDLE DOT "periodcentered"
        97:'Ç', # '\u00C7' # LATIN CAPITAL LETTER C WITH CEDILLA "Ccedilla"
        98:'ª', # '\u00AA' # FEMININE ORDINAL INDICATOR "ordfeminine"
        99:'º' # '\u00BA' # MASCULINE ORDINAL INDICATOR "ordmasculine"
    }
    char = switcher.get(cents, "")
    text = '<h2 class="hundredfraction">' + char + '</h2>'
    return char
