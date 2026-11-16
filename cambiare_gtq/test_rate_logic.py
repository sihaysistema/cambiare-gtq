# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Unit tests for rate lookup. They do not need a Frappe site.

Run from the repository root:

    python3 cambiare_gtq/test_rate_logic.py
"""

from __future__ import unicode_literals

import datetime
import importlib.util
import json
import os
import unittest


def _load_rate_logic():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rate_logic.py")
    spec = importlib.util.spec_from_file_location("cambiare_rate_logic_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rate_logic = _load_rate_logic()


class _Var(object):
    def __init__(self, moneda, fecha, venta, compra=None):
        self.moneda = moneda
        self.fecha = fecha
        self.venta = venta
        self.compra = compra if compra is not None else venta


class _Vars(object):
    def __init__(self, items):
        self.Var = items


class _Payload(object):
    def __init__(self, items):
        self.Vars = _Vars(items) if items is not None else None
        if items is None:
            self.TotalItems = 0
        elif isinstance(items, list):
            self.TotalItems = len(items)
        else:
            self.TotalItems = 1


class FakeBanguat(object):
    """Returns a USD quote and an EUR quote (units of EUR per 1 USD)."""

    def __init__(self):
        self.usd_calls = 0
        self.currency_calls = 0

    def usd_range(self, from_date, to_date):
        self.usd_calls += 1
        start = rate_logic.parse_date(from_date)
        end = rate_logic.parse_date(to_date)
        rows = []
        day = start
        while day <= end:
            # 7.50 on the 1st, 7.80 afterwards. Weekends included, like Banguat.
            rate = 7.5 if day.day == 1 else 7.8
            rows.append({"variable": 2, "date": day, "rate": rate})
            day += datetime.timedelta(days=1)
        return rows

    def currency_range(self, variable, from_date, to_date):
        self.currency_calls += 1
        start = rate_logic.parse_date(from_date)
        end = rate_logic.parse_date(to_date)
        rows = []
        day = start
        while day <= end:
            rows.append({"variable": int(variable), "date": day, "rate": 1.25})
            day += datetime.timedelta(days=1)
        return rows


class TestQuotes(unittest.TestCase):
    def test_usd_quote_is_quetzales_per_dollar(self):
        self.assertAlmostEqual(rate_logic.quetzales_per_unit(7.5, 1), 7.5)

    def test_non_usd_quote_converts_through_the_dollar(self):
        # 1 USD = 7.5 GTQ and 1 USD = 1.25 EUR => 1 EUR = 6 GTQ.
        self.assertAlmostEqual(rate_logic.quetzales_per_unit(7.5, 1.25), 6.0)

    def test_reciprocal_direction(self):
        self.assertAlmostEqual(rate_logic.reciprocal(7.5), 1.0 / 7.5)

    def test_parse_var_rows_accepts_a_single_object(self):
        payload = _Payload(_Var(2, "15/11/2026", 7.64312))
        rows = rate_logic.parse_var_rows(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], datetime.date(2026, 11, 15))
        self.assertAlmostEqual(rows[0]["rate"], 7.64312)

    def test_parse_var_rows_accepts_a_dict_list(self):
        payload = {
            "Vars": {
                "Var": [
                    {"moneda": 24, "fecha": "03/11/2026", "venta": "1.1187", "compra": "1.1187"},
                ]
            }
        }
        rows = rate_logic.parse_var_rows(payload)
        self.assertEqual(rows[0]["date"], datetime.date(2026, 11, 3))
        self.assertAlmostEqual(rows[0]["rate"], 1.1187)

    def test_empty_payload(self):
        self.assertEqual(rate_logic.parse_var_rows(_Payload(None)), [])


class TestClosingAndAverage(unittest.TestCase):
    def setUp(self):
        self.client = FakeBanguat()
        self.service = rate_logic.ExchangeService(rate_logic.MemoryBook(), self.client)

    def test_backfill_is_idempotent_and_stores_both_directions(self):
        first = self.service.backfill("2026-11-01", "2026-11-03", currency="USD")
        self.assertEqual(first["created"], 6)  # 3 days x 2 directions
        self.assertEqual(first["skipped"], 0)
        second = self.service.backfill("2026-11-01", "2026-11-03", currency="USD")
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["skipped"], 6)
        usd = self.service.get_closing_rate("USD", "GTQ", "2026-11-01", fetch_if_missing=0)
        self.assertAlmostEqual(usd["rate"], 7.5)
        self.assertEqual(usd["source"], "exact")
        self.assertEqual(usd["rate_date"], "2026-11-01")
        gtq = self.service.get_closing_rate("GTQ", "USD", "2026-11-01", fetch_if_missing=0)
        self.assertAlmostEqual(gtq["rate"], 1.0 / 7.5)
        self.assertIn("1 GTQ =", gtq["meaning"])
        self.assertIn("USD", gtq["meaning"])

    def test_eur_is_quetzales_per_euro(self):
        self.service.backfill("2026-11-01", "2026-11-01", currency="EUR")
        eur = self.service.get_closing_rate("EUR", "GTQ", "2026-11-01", fetch_if_missing=0)
        self.assertAlmostEqual(eur["rate"], 6.0)
        back = self.service.get_closing_rate("GTQ", "EUR", "2026-11-01", fetch_if_missing=0)
        self.assertAlmostEqual(back["rate"], 1.0 / 6.0)

    def test_fetch_if_missing_stores_the_requested_date(self):
        result = self.service.get_closing_rate("USD", "GTQ", "2026-11-02", fetch_if_missing=1)
        self.assertEqual(result["source"], "banguat")
        self.assertEqual(result["rate_date"], "2026-11-02")
        self.assertAlmostEqual(result["rate"], 7.8)
        self.assertEqual(self.client.usd_calls, 1)

    def test_fallback_uses_the_latest_rate_on_or_before(self):
        self.service.book.add("2026-11-01", "USD", "GTQ", 7.1)
        result = self.service.get_closing_rate("USD", "GTQ", "2026-11-04", fetch_if_missing=0)
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["rate_date"], "2026-11-01")
        self.assertAlmostEqual(result["rate"], 7.1)

    def test_inverse_when_only_the_other_direction_exists(self):
        self.service.book.add("2026-11-02", "USD", "GTQ", 8)
        result = self.service.get_closing_rate("GTQ", "USD", "2026-11-02", fetch_if_missing=0)
        self.assertEqual(result["source"], "inverse")
        self.assertAlmostEqual(result["rate"], 0.125)

    def test_missing_rate_raises(self):
        with self.assertRaises(rate_logic.RateError) as raised:
            self.service.get_closing_rate("USD", "GTQ", "2026-11-01", fetch_if_missing=0)
        self.assertEqual(raised.exception.code, "not_found")

    def test_identity_rate(self):
        result = self.service.get_closing_rate("GTQ", "GTQ", "2026-11-01", fetch_if_missing=0)
        self.assertEqual(result["rate"], 1.0)
        self.assertEqual(result["source"], "identity")

    def test_average_is_unweighted_per_calendar_day(self):
        # Nov 1 is 7.5, Nov 2 and Nov 3 are 7.8. Mean of the three days.
        result = self.service.get_average_rate(
            "USD", "GTQ", "2026-11-01", "2026-11-03", fetch_if_missing=1
        )
        self.assertEqual(result["days"], 3)
        self.assertAlmostEqual(result["average"], (7.5 + 7.8 + 7.8) / 3.0)
        self.assertEqual(result["from_date"], "2026-11-01")
        self.assertEqual(result["to_date"], "2026-11-03")

    def test_average_carries_the_previous_rate_when_a_day_was_not_stored(self):
        self.service.book.add("2026-11-01", "USD", "GTQ", 7.0)
        self.service.book.add("2026-11-03", "USD", "GTQ", 8.0)
        result = self.service.get_average_rate(
            "USD", "GTQ", "2026-11-01", "2026-11-03", fetch_if_missing=0
        )
        self.assertEqual(result["days"], 3)
        self.assertAlmostEqual(result["average"], (7.0 + 7.0 + 8.0) / 3.0)

    def test_average_of_a_partial_month_uses_only_that_span(self):
        self.service.backfill("2026-11-01", "2026-11-10", currency="USD")
        result = self.service.get_average_rate(
            "GTQ", "USD", "2026-11-01", "2026-11-02", fetch_if_missing=0
        )
        expected = ((1.0 / 7.5) + (1.0 / 7.8)) / 2.0
        self.assertEqual(result["days"], 2)
        self.assertAlmostEqual(result["average"], expected)

    def test_reversed_date_range_is_rejected(self):
        with self.assertRaises(rate_logic.RateError) as raised:
            self.service.get_average_rate("USD", "GTQ", "2026-11-05", "2026-11-01")
        self.assertEqual(raised.exception.code, "bad_range")

    def test_unknown_currency_is_rejected(self):
        with self.assertRaises(rate_logic.RateError) as raised:
            self.service.backfill("2026-11-01", "2026-11-01", currency="XXX")
        self.assertEqual(raised.exception.code, "unknown_currency")


class TestCatalogAndLegacyValues(unittest.TestCase):
    def test_doctype_options_match_the_catalog(self):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cambiare_gtq",
            "doctype",
            "available_currencies",
            "available_currencies.json",
        )
        with open(path, "r") as handle:
            doc = json.load(handle)
        field = [item for item in doc["fields"] if item["fieldname"] == "currency"][0]
        self.assertEqual(field["label"], "Currency")
        self.assertEqual(field["options"], rate_logic.currency_options_text())
        code = [item for item in doc["fields"] if item["fieldname"] == "code"][0]
        self.assertEqual(code["label"], "Code")

    def test_legacy_frequency_and_currency_maps(self):
        self.assertEqual(rate_logic.LEGACY_FREQUENCY["Cada Hora"], "Hourly")
        self.assertEqual(rate_logic.LEGACY_FREQUENCY["Cada Dia"], "Daily")
        self.assertEqual(
            rate_logic.LEGACY_CURRENCY_OPTIONS["18 - Pesos Mexicanos - MXN"],
            "18 - Mexican Pesos - MXN",
        )
        self.assertEqual(rate_logic.iso_from_option("18 - Mexican Pesos - MXN"), "MXN")
        self.assertEqual(rate_logic.variable_from_option("24 - Euro - EUR"), 24)

    def test_configuration_doctype_is_english(self):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cambiare_gtq",
            "doctype",
            "configuration_cambiare",
            "configuration_cambiare.json",
        )
        with open(path, "r") as handle:
            doc = json.load(handle)
        fields = {item["fieldname"]: item for item in doc["fields"]}
        self.assertIn("frequency", fields)
        self.assertNotIn("frecuencia", fields)
        self.assertEqual(fields["frequency"]["label"], "Query Frequency")
        self.assertIn("\nHourly\nDaily\nWeekly\nMonthly", fields["frequency"]["options"])
        self.assertEqual(fields["disable_queries"]["label"], "Disable Queries")
        self.assertEqual(fields["currencies"]["label"], "Currencies")
        self.assertNotIn("Cada Hora", json.dumps(doc))


if __name__ == "__main__":
    unittest.main()
