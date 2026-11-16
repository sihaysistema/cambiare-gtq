# -*- coding: utf-8 -*-
# Copyright (c) 2026, Si Hay Sistema and contributors
# For license information, please see license.txt
"""Banco de Guatemala rates and the pure lookup rules.

This module does not import Frappe. The whitelisted API in
``exchange_rates`` is a thin adapter over :class:`ExchangeService`.

Rate meaning
------------
A stored rate converts an amount in ``from_currency`` into ``to_currency``:

    amount_in_to = amount_in_from * rate

That is the ERPNext Currency Exchange convention.

Banguat's USD quote (variable 2, field ``venta``) is quetzales per 1 US
dollar, so ``USD -> GTQ`` stores that number and ``GTQ -> USD`` stores its
reciprocal.

For every other variable, ``venta`` is units of that currency per 1 US
dollar. Quetzales per 1 unit of the currency are::

    usd_to_gtq / units_per_usd

Both directions are stored. ``USD -> GTQ`` of 7.64 means 1 USD = 7.64 GTQ.
``GTQ -> USD`` of 0.13089 means 1 GTQ = 0.13089 USD.
"""

from __future__ import unicode_literals

import datetime
import re

WSDL_URL = "https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?WSDL"
USD_VARIABLE = 2

# (banguat variable, English name, ISO code)
# Variable 6 is labeled "Francos Franceses" by Banguat while this app has
# always stored it as CHF. Variable 8 is "Liras Italianas" stored as GBP.
# The numbers and ISO codes are unchanged; only the description is English.
CURRENCIES = (
    (3, "Japanese Yen", "JPY"),
    (6, "French Francs", "CHF"),
    (7, "Canadian Dollars", "CAD"),
    (8, "Italian Lira", "GBP"),
    (15, "Swedish Krona", "SEK"),
    (16, "Costa Rican Colones", "CRC"),
    (17, "Salvadoran Colones", "SVC"),
    (18, "Mexican Pesos", "MXN"),
    (19, "Honduran Lempiras", "HNL"),
    (21, "Nicaraguan Cordobas", "NIO"),
    (22, "Venezuelan Bolivares", "VEF"),
    (23, "Danish Krone", "DKK"),
    (24, "Euro", "EUR"),
    (25, "Norwegian Krone", "NOK"),
    (29, "Argentine Peso", "ARS"),
    (30, "Brazilian Real", "BRL"),
    (31, "Korean Won", "KPW"),
    (32, "Hong Kong Dollar", "HKD"),
    (33, "Taiwan Dollar", "TWD"),
    (34, "Chinese Yuan", "CNY"),
    (35, "Pakistani Rupee", "PKR"),
    (36, "Indian Rupee", "INR"),
    (37, "Bolivar Fuerte", "BOB"),
    (38, "Colombian Peso", "COP"),
    (39, "Dominican Peso", "DOP"),
    (40, "Malaysian Ringgit", "MYR"),
    (41, "Sovereign Bolivar", "BOV"),
    (42, "Zloty", "PLN"),
)

ISO_TO_VARIABLE = {iso: variable for variable, _name, iso in CURRENCIES}
VARIABLE_TO_ISO = {variable: iso for variable, _name, iso in CURRENCIES}

LEGACY_FREQUENCY = {
    "Cada Hora": "Hourly",
    "Cada Dia": "Daily",
    "Cada Día": "Daily",
    "Cada Semana": "Weekly",
    "Cada Mes": "Monthly",
}

LEGACY_CURRENCY_OPTIONS = {
    "3 - Yenes Japoneses - JPY": "3 - Japanese Yen - JPY",
    "6 - Francos Franceses - CHF": "6 - French Francs - CHF",
    "7 - Dólares Canadienses - CAD": "7 - Canadian Dollars - CAD",
    "8 - Liras Italianas - GBP": "8 - Italian Lira - GBP",
    "15 - Coronas Suecas - SEK": "15 - Swedish Krona - SEK",
    "16 - Colones Costarricenses - CRC": "16 - Costa Rican Colones - CRC",
    "17 - Colones Salvadoreños - SVC": "17 - Salvadoran Colones - SVC",
    "18 - Pesos Mexicanos - MXN": "18 - Mexican Pesos - MXN",
    "19 - Lempiras Hondureños - HNL": "19 - Honduran Lempiras - HNL",
    "21 - Córdobas Nicaragüenses - NIO": "21 - Nicaraguan Cordobas - NIO",
    "22 - Bolivares Venezolanos - VEF": "22 - Venezuelan Bolivares - VEF",
    "23 - Corona Danesa - DKK": "23 - Danish Krone - DKK",
    "24 - Euro - EUR": "24 - Euro - EUR",
    "25 - Corona Noruega - NOK": "25 - Norwegian Krone - NOK",
    "29 - Peso Argentina - ARS": "29 - Argentine Peso - ARS",
    "30 - Real Brasileño - BRL": "30 - Brazilian Real - BRL",
    "31 - Won Coreano - KPW": "31 - Korean Won - KPW",
    "32 - Dólar Hong Kong - HKD": "32 - Hong Kong Dollar - HKD",
    "33 - Dólar Taiwán - TWD": "33 - Taiwan Dollar - TWD",
    "34 - Yuan China - CNY": "34 - Chinese Yuan - CNY",
    "35 - Rupia Pakistán - PKR": "35 - Pakistani Rupee - PKR",
    "36 - Rupee India - INR": "36 - Indian Rupee - INR",
    "37 - Bolivar Fuerte - BOB": "37 - Bolivar Fuerte - BOB",
    "38 - Peso Colombiano - COP": "38 - Colombian Peso - COP",
    "39 - Peso Dominicano - DOP": "39 - Dominican Peso - DOP",
    "40 - Ringgit Malasia - MYR": "40 - Malaysian Ringgit - MYR",
    "41 - Bolívar Soberano - BOV": "41 - Sovereign Bolivar - BOV",
    "42 - Zloty - PLN": "42 - Zloty - PLN",
}

_OPTION_RE = re.compile(r"^\s*(\d+)\s*-\s*(.*?)\s*-\s*([A-Za-z]{3})\s*$")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


class RateError(Exception):
    """Domain error. ``code`` selects a translatable message in the adapter."""

    def __init__(self, code, args=()):
        self.code = code
        self.details = tuple(args or ())
        super(RateError, self).__init__(code)


def option_label(variable, name, iso):
    return "{0} - {1} - {2}".format(variable, name, iso)


def currency_options_text():
    lines = [option_label(variable, name, iso) for variable, name, iso in CURRENCIES]
    return "\n" + "\n".join(lines)


def iso_from_option(value):
    if not value:
        return ""
    match = _OPTION_RE.match(str(value))
    if not match:
        return ""
    return match.group(3).upper()


def variable_from_option(value):
    if not value:
        return None
    match = _OPTION_RE.match(str(value))
    if not match:
        return None
    return int(match.group(1))


def parse_date(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value).strip()
    if not text or text in ("0", "None"):
        raise RateError("bad_date", (text,))
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except ValueError:
            continue
    # Frappe sometimes returns "2026-11-01 00:00:00".
    if len(text) >= 10:
        try:
            return datetime.datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    raise RateError("bad_date", (text,))


def banguat_date(value):
    return parse_date(value).strftime("%d/%m/%Y")


def iso_date(value):
    return parse_date(value).isoformat()


def quetzales_per_unit(usd_to_gtq, units_per_usd):
    """GTQ for 1 unit of a non-USD currency quoted as units per 1 USD."""
    usd_to_gtq = float(usd_to_gtq)
    units_per_usd = float(units_per_usd)
    if usd_to_gtq <= 0 or units_per_usd <= 0:
        raise RateError("bad_quote", (usd_to_gtq, units_per_usd))
    return usd_to_gtq / units_per_usd


def reciprocal(rate):
    rate = float(rate)
    if rate == 0:
        raise RateError("bad_quote", (rate,))
    return 1.0 / rate


def daterange(from_date, to_date):
    start = parse_date(from_date)
    end = parse_date(to_date)
    if start > end:
        raise RateError("bad_range", (iso_date(start), iso_date(end)))
    day = start
    while day <= end:
        yield day
        day += datetime.timedelta(days=1)


def target_currencies(currency, configured):
    """ISO codes to fetch. USD is included when another currency needs it.

    ``currency`` empty means USD plus every configured currency.
    ``USD`` or ``GTQ`` means only the dollar/quetzal pair.
    """
    configured = [str(item).strip().upper() for item in (configured or []) if item]
    if currency in (None, ""):
        extras = [iso for iso in configured if iso not in ("USD", "GTQ") and iso in ISO_TO_VARIABLE]
        # Preserve order and drop duplicates.
        seen = set()
        ordered = []
        for iso in ["USD"] + extras:
            if iso not in seen:
                seen.add(iso)
                ordered.append(iso)
        return ordered
    iso = str(currency).strip().upper()
    if iso in ("USD", "GTQ"):
        return ["USD"]
    if iso not in ISO_TO_VARIABLE:
        raise RateError("unknown_currency", (iso,))
    return ["USD", iso]


def currencies_from_config_rows(rows):
    """Read ISO codes from Available Currencies rows (``code`` or the option)."""
    found = []
    for row in rows or []:
        iso = ""
        if isinstance(row, dict):
            iso = (row.get("code") or row.get("codigo") or "").strip().upper()
            if not iso:
                iso = iso_from_option(row.get("currency") or row.get("moneda") or "")
        else:
            iso = (getattr(row, "code", None) or getattr(row, "codigo", None) or "")
            iso = str(iso).strip().upper()
            if not iso:
                iso = iso_from_option(getattr(row, "currency", None) or getattr(row, "moneda", None))
        if iso and iso not in found:
            found.append(iso)
    return found


def resolve_closing(rows, requested):
    """Pick the row on ``requested`` or the latest row on or before it.

    ``rows`` is a list of ``{"date": date, "rate": float}``.
    Returns ``{"rate", "rate_date", "source"}`` or ``None``.
    ``source`` is ``exact`` or ``fallback``.
    """
    requested = parse_date(requested)
    exact = None
    prior = None
    for row in rows or []:
        row_date = parse_date(row["date"])
        rate = float(row["rate"])
        provider = row.get("rate_source") if isinstance(row, dict) else None
        if row_date == requested:
            exact = {"rate": rate, "rate_date": row_date, "source": "exact", "rate_source": provider}
        elif row_date < requested and (prior is None or row_date > prior["rate_date"]):
            prior = {"rate": rate, "rate_date": row_date, "source": "fallback", "rate_source": provider}
    return exact or prior


def average_rates(rates):
    """Unweighted arithmetic mean. ``rates`` must be non-empty."""
    values = [float(rate) for rate in rates]
    if not values:
        raise RateError("not_found", ())
    return sum(values) / float(len(values))


def _get(obj, key):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def parse_var_rows(payload):
    """Normalize a TipoCambioRango* result into plain dicts.

    Accepts a zeep object or a dict. One ``Var`` is not always a list.
    """
    vars_node = _get(payload, "Vars")
    items = _as_list(_get(vars_node, "Var") if vars_node is not None else None)
    rows = []
    for item in items:
        fecha = _get(item, "fecha")
        venta = _get(item, "venta")
        if fecha is None or venta is None:
            continue
        try:
            rate = float(venta)
        except (TypeError, ValueError):
            continue
        if rate <= 0:
            continue
        rows.append({
            "variable": _get(item, "moneda"),
            "date": parse_date(fecha),
            "rate": rate,
        })
    return rows


class ZeepBanguatClient(object):
    """SOAP client for the Banguat TipoCambio service. Uses zeep."""

    def __init__(self, service=None, wsdl=WSDL_URL):
        if service is None:
            try:
                from zeep import Client
                from zeep.transports import Transport
            except ImportError:
                raise RateError("banguat", ("zeep is not installed",))
            try:
                service = Client(
                    wsdl, transport=Transport(timeout=30, operation_timeout=30)
                ).service
            except Exception as exc:
                raise RateError("banguat", (str(exc),))
        self.service = service

    def usd_range(self, from_date, to_date):
        try:
            payload = self.service.TipoCambioRango(
                fechainit=banguat_date(from_date),
                fechafin=banguat_date(to_date),
            )
        except RateError:
            raise
        except Exception as exc:
            raise RateError("banguat", (str(exc),))
        return parse_var_rows(payload)

    def currency_range(self, variable, from_date, to_date):
        try:
            payload = self.service.TipoCambioRangoMoneda(
                fechainit=banguat_date(from_date),
                fechafin=banguat_date(to_date),
                moneda=int(variable),
            )
        except RateError:
            raise
        except Exception as exc:
            raise RateError("banguat", (str(exc),))
        return parse_var_rows(payload)


class MemoryBook(object):
    """In-memory rate book used by tests and as the book contract."""

    def __init__(self):
        self.rows = []

    def add(self, rate_date, from_currency, to_currency, rate):
        rate_date = parse_date(rate_date)
        for row in self.rows:
            if (
                row["date"] == rate_date
                and row["from_currency"] == from_currency
                and row["to_currency"] == to_currency
            ):
                return 0, 1
        self.rows.append({
            "date": rate_date,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": float(rate),
        })
        return 1, 0

    def find(self, from_currency, to_currency):
        return [
            {"date": row["date"], "rate": row["rate"]}
            for row in self.rows
            if row["from_currency"] == from_currency and row["to_currency"] == to_currency
        ]


class ExchangeService(object):
    def __init__(self, book, client):
        self.book = book
        self.client = client

    def backfill(self, from_date, to_date, currency=None, configured=None):
        start = parse_date(from_date)
        end = parse_date(to_date)
        if start > end:
            raise RateError("bad_range", (iso_date(start), iso_date(end)))
        targets = target_currencies(currency, configured)
        usd_rows = self.client.usd_range(start, end)
        usd_by_date = {}
        for row in usd_rows:
            if start <= row["date"] <= end:
                usd_by_date[row["date"]] = row["rate"]

        created = 0
        skipped = 0
        if "USD" in targets:
            for rate_date, usd_to_gtq in sorted(usd_by_date.items()):
                made, existed = self._store_both(rate_date, "USD", "GTQ", usd_to_gtq)
                created += made
                skipped += existed

        for iso in targets:
            if iso == "USD":
                continue
            variable = ISO_TO_VARIABLE[iso]
            quotes = self.client.currency_range(variable, start, end)
            for quote in quotes:
                if quote["date"] < start or quote["date"] > end:
                    continue
                usd_to_gtq = usd_by_date.get(quote["date"])
                if not usd_to_gtq:
                    continue
                gtq_per_unit = quetzales_per_unit(usd_to_gtq, quote["rate"])
                made, existed = self._store_both(quote["date"], iso, "GTQ", gtq_per_unit)
                created += made
                skipped += existed

        return {
            "created": created,
            "skipped": skipped,
            "from_date": iso_date(start),
            "to_date": iso_date(end),
            "currencies": targets,
        }

    def _store_both(self, rate_date, from_currency, to_currency, rate):
        created, skipped = self.book.add(rate_date, from_currency, to_currency, rate)
        inv_created, inv_skipped = self.book.add(
            rate_date, to_currency, from_currency, reciprocal(rate)
        )
        return created + inv_created, skipped + inv_skipped

    def get_closing_rate(self, from_currency, to_currency, rate_date, fetch_if_missing=True):
        from_currency = str(from_currency or "").strip().upper()
        to_currency = str(to_currency or "").strip().upper()
        requested = parse_date(rate_date)
        if not from_currency or not to_currency:
            raise RateError("not_found", (from_currency, to_currency, iso_date(requested)))
        if from_currency == to_currency:
            return self._result(1.0, requested, from_currency, to_currency, "identity")

        direct = resolve_closing(self.book.find(from_currency, to_currency), requested)
        if direct and direct["source"] == "exact":
            return self._result(
                direct["rate"], direct["rate_date"], from_currency, to_currency, "exact",
                direct.get("rate_source"),
            )

        fetched = False
        if _is_truthy(fetch_if_missing) and _involves_gtq(from_currency, to_currency):
            foreign = from_currency if from_currency != "GTQ" else to_currency
            self.backfill(requested, requested, currency=foreign)
            fetched = True
            direct = resolve_closing(self.book.find(from_currency, to_currency), requested)
            if direct and direct["source"] == "exact":
                return self._result(
                    direct["rate"], direct["rate_date"], from_currency, to_currency, "banguat",
                    direct.get("rate_source") or "Banguat",
                )

        inverse = resolve_closing(self.book.find(to_currency, from_currency), requested)
        if inverse and inverse["source"] == "exact":
            source = "banguat" if fetched else "inverse"
            return self._result(
                reciprocal(inverse["rate"]), inverse["rate_date"], from_currency, to_currency, source,
                inverse.get("rate_source"),
            )
        if direct:
            return self._result(
                direct["rate"], direct["rate_date"], from_currency, to_currency, "fallback",
                direct.get("rate_source"),
            )
        if inverse:
            return self._result(
                reciprocal(inverse["rate"]), inverse["rate_date"], from_currency, to_currency, "fallback",
                inverse.get("rate_source"),
            )
        raise RateError("not_found", (from_currency, to_currency, iso_date(requested)))

    def get_average_rate(self, from_currency, to_currency, from_date, to_date, fetch_if_missing=True):
        from_currency = str(from_currency or "").strip().upper()
        to_currency = str(to_currency or "").strip().upper()
        start = parse_date(from_date)
        end = parse_date(to_date)
        if start > end:
            raise RateError("bad_range", (iso_date(start), iso_date(end)))
        if from_currency == to_currency:
            days = (end - start).days + 1
            return {
                "average": 1.0,
                "days": days,
                "from_date": iso_date(start),
                "to_date": iso_date(end),
                "from_currency": from_currency,
                "to_currency": to_currency,
                "covered_from": iso_date(start),
                "covered_to": iso_date(end),
            }

        if _is_truthy(fetch_if_missing) and _involves_gtq(from_currency, to_currency):
            foreign = from_currency if from_currency != "GTQ" else to_currency
            self.backfill(start, end, currency=foreign)

        used = []
        for day in daterange(start, end):
            try:
                closing = self.get_closing_rate(
                    from_currency, to_currency, day, fetch_if_missing=False
                )
            except RateError as exc:
                if exc.code == "not_found":
                    continue
                raise
            used.append((day, closing["rate"]))
        if not used:
            raise RateError(
                "not_found",
                (from_currency, to_currency, iso_date(start) + " - " + iso_date(end)),
            )
        return {
            "average": average_rates([rate for _day, rate in used]),
            "days": len(used),
            "from_date": iso_date(start),
            "to_date": iso_date(end),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "covered_from": iso_date(used[0][0]),
            "covered_to": iso_date(used[-1][0]),
        }

    def _result(self, rate, rate_date, from_currency, to_currency, source, rate_source=None):
        result = {
            "rate": float(rate),
            "rate_date": iso_date(rate_date),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "source": source,
            "meaning": "1 {0} = {1} {2}".format(from_currency, float(rate), to_currency),
        }
        if rate_source:
            result["rate_source"] = rate_source
        return result


def _involves_gtq(from_currency, to_currency):
    pair = {from_currency, to_currency}
    if "GTQ" not in pair:
        return False
    other = from_currency if to_currency == "GTQ" else to_currency
    return other == "USD" or other in ISO_TO_VARIABLE


def _is_truthy(value):
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() not in ("0", "false", "no", "off", "")
