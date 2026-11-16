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

    def test_catalog_matches_banguat_variables(self):
        expected = {
            2: "USD", 3: "JPY", 4: "BEF", 5: "CHF", 6: "FRF", 7: "CAD", 8: "ITL",
            9: "GBP", 11: "DEM", 12: "ESP", 13: "ATS", 14: "NLG", 15: "SEK",
            16: "CRC", 17: "SVC", 18: "MXN", 19: "HNL", 21: "NIO", 22: "VEB", 23: "DKK",
            24: "EUR", 25: "NOK", 26: "XDR", 27: "PTE", 28: "IDB", 29: "ARS", 30: "BRL",
            31: "KRW", 32: "HKD", 33: "TWD", 34: "CNY", 35: "PKR", 36: "INR", 37: "VEF",
            38: "COP", 39: "DOP", 40: "MYR", 41: "VES", 42: "PLN",
        }
        self.assertEqual(rate_logic.VARIABLE_TO_ISO, expected)
        self.assertNotIn(1, rate_logic.VARIABLE_TO_ISO)
        options = rate_logic.currency_options_text()
        self.assertIn("\n5 - Swiss Francs - CHF\n", options)
        self.assertIn("\n6 - French Francs - FRF\n", options)
        self.assertIn("\n9 - Pounds Sterling - GBP\n", options)
        self.assertNotIn("KPW", options)
        self.assertNotIn("BOB", options)
        self.assertNotIn("BOV", options)

    def test_saved_row_keeps_the_iso_code_and_repairs_the_variable(self):
        self.assertEqual(
            rate_logic.canonical_saved_currency("6 - French Francs - CHF"),
            ("5 - Swiss Francs - CHF", "CHF"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("6 - Francos Franceses - CHF"),
            ("5 - Swiss Francs - CHF", "CHF"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("8 - Italian Lira - GBP"),
            ("9 - Pounds Sterling - GBP", "GBP"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("22 - Venezuelan Bolivares - VEF"),
            ("37 - Bolivar Fuerte - VEF", "VEF"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("31 - Korean Won - KPW"),
            ("31 - Korean Won - KRW", "KRW"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("37 - Bolivar Fuerte - BOB"),
            ("37 - Bolivar Fuerte - VEF", "VEF"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("41 - Sovereign Bolivar - BOV"),
            ("41 - Sovereign Bolivar - VES", "VES"),
        )
        self.assertEqual(
            rate_logic.canonical_saved_currency("18 - Mexican Pesos - MXN", "MXN"),
            ("18 - Mexican Pesos - MXN", "MXN"),
        )
        self.assertEqual(
            rate_logic.LEGACY_CURRENCY_OPTIONS["6 - Francos Franceses - CHF"],
            "5 - Swiss Francs - CHF",
        )

    def test_validity_custom_fields_are_not_shipped(self):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures",
            "custom_field.json",
        )
        with open(path, "r") as handle:
            rows = json.load(handle)
        names = [row.get("name") for row in rows]
        self.assertNotIn("Currency Exchange-valid_from", names)
        self.assertNotIn("Currency Exchange-valid_to", names)
        self.assertNotIn("Currency Exchange-validity_date_ranges", names)
        self.assertIn("Currency-currency_textual_name", names)
        patches = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patches.txt")
        with open(patches, "r") as handle:
            patch_text = handle.read()
        self.assertIn(
            "cambiare_gtq.patches.v1_5.remove_currency_exchange_validity_fields",
            patch_text,
        )
        self.assertIn(
            "cambiare_gtq.patches.v1_5.remap_banguat_currencies",
            patch_text,
        )

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


def _load_series_math():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "series_math.py")
    spec = importlib.util.spec_from_file_location("cambiare_series_math_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


series_math = _load_series_math()


class TestSeriesMath(unittest.TestCase):
    def test_median_odd_and_even(self):
        self.assertEqual(series_math.median([3, 1, 2]), 2)
        self.assertEqual(series_math.median(["10", "30"]), 20)

    def test_precyos_drops_isolated_prints(self):
        points = [
            {"date": "2009-10-05", "usd": "0.000764"},
            {"date": "2010-05-22", "usd": "0.0041"},
            {"date": "2010-08-18", "usd": "0.07"},
            {"date": "2010-08-19", "usd": "0.08"},
        ]
        kept = series_math.precyos_usd_points(points)
        self.assertEqual([day for day, _rate in kept], ["2010-08-18", "2010-08-19"])

    def test_btc_gtq_uses_asof_banguat_venta(self):
        usd = {
            datetime.date(2010, 8, 17): series_math.Decimal("7.9"),
            datetime.date(2010, 8, 18): series_math.Decimal("8.0"),
        }
        self.assertEqual(
            series_math.asof_rate(usd, datetime.date(2010, 8, 19)),
            series_math.Decimal("8.0"),
        )
        self.assertEqual(
            series_math.btc_gtq("0.07", "8.0"),
            series_math.Decimal("0.560"),
        )

    def test_cross_rate_through_gtq(self):
        # 1 EUR = 8 GTQ, 1 BTC = 16 GTQ => 1 EUR = 0.5 BTC
        self.assertEqual(series_math.bridge_rate("8", "16"), series_math.Decimal("0.5"))

    def test_bisq_groups_the_utc_day_before_the_next_midnight(self):
        # 2024-01-01 00:30 UTC and 2024-01-01 23:00 UTC belong to 2024-01-01.
        trades = [
            {"trade_date": 1704069000000, "price": "100"},
            {"trade_date": 1704150000000, "price": "300"},
            {"trade_date": 1704153600000, "price": "900"},
        ]
        grouped = series_math.trades_by_utc_day(trades)
        self.assertEqual(grouped[datetime.date(2024, 1, 1)], 200)
        self.assertEqual(grouped[datetime.date(2024, 1, 2)], 900)

    def test_bisq_paging_stops_between_pages(self):
        pages = [
            [{"trade_date": 1704069000000, "price": "1"}, {"trade_date": 1704070000000, "price": "2"}],
            [{"trade_date": 1704071000000, "price": "3"}],
        ]
        calls = []

        def fetch(start, end):
            calls.append((start, end))
            return pages.pop(0) if pages else []

        pauses = []
        collected = series_math.page_bisq(
            fetch, datetime.date(2024, 1, 1), datetime.date(2024, 1, 1), lambda: pauses.append(1)
        )
        self.assertEqual(len(collected), 2)
        self.assertEqual(pauses, [])


if __name__ == "__main__":
    unittest.main()
