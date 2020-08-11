# -*- coding: utf-8 -*-
#  Si Hay Sistema and Contributors 2020
from __future__ import unicode_literals
from . import __version__ as app_version


def fill_fixtures():
    # We declare fixtures as an empty list.
    fixtures_fillup = []

    # Add the corresponding fields to the fixture objects
    # if the object does not exist, simply create it and copy accordingly.

    custom_field = {
        "dt": "Custom Field", "filters": [
            [
                "name", "in", [
                    "Currency Exchange-validity_date_ranges",
                    "Currency Exchange-valid_to",
                    "Currency Exchange-col_break",
                    "Currency Exchange-valid_from",
                    "Currency-currency_textual_name"
                ]
            ]
        ]
    }
    
    translations = {
        "dt": "Translation", "filters": [
            [
                "source_name", "in", [
                    "Could not create USD to GTQ exchange rate, please try generating GTQ manually",
                    "Currency Textual Name"
                ]
            ]
        ]
    }
    
    currencies = {
        "dt": "Currency", "filters": [
            [
                "name", "in", [
                    "GTQ",
                ]
            ]
        ]
    }
    

    # NEW FUNCTIONALITY FOR EXPORTING
    fixtures_fillup.append(custom_field)
    fixtures_fillup.append(translations)
    fixtures_fillup.append(currencies)

    return fixtures_fillup
