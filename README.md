# Cambiare GTQ

Exchange rates for ERPNext from the Banco de Guatemala (Banguat) SOAP service.

https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx

The app stores each quote in **Currency Exchange GTQ** and in ERPNext **Currency Exchange**, in both directions. The rate date is the standard `date` field on those documents. The unused `valid_from` and `valid_to` custom fields are not shipped, and a patch removes them from sites that already have them.

## Supported versions

Install the branch that matches the site's Frappe and ERPNext major. Do not mix branches on one site.

| Branch | Frappe / ERPNext | Python | Install |
| --- | --- | --- | --- |
| `production` | v13 | 3.7+ (zeep does not support 3.6) | `bench get-app --branch production https://github.com/sihaysistema/cambiare-gtq.git` |
| `production-v14` | v14 | 3.10+ | `bench get-app --branch production-v14 https://github.com/sihaysistema/cambiare-gtq.git` |
| `version-15` | v15 | 3.10+ | `bench get-app --branch version-15 https://github.com/sihaysistema/cambiare-gtq.git` |
| `version-16` | v16 | 3.14+ | `bench get-app --branch version-16 https://github.com/sihaysistema/cambiare-gtq.git` |

Then:

```bash
bench setup requirements
bench build --app cambiare_gtq
bench restart
bench --site [your.site.name] install-app cambiare_gtq
bench --site [your.site.name] migrate
```

App version on this line: see `__version__` in `cambiare_gtq/__init__.py`.

This branch targets Frappe / ERPNext v15 and Python 3.10 or newer. Dependencies are declared in `requirements.txt` and in `pyproject.toml` (flit). `required_apps` is `erpnext`.

## What a rate means

`rate` multiplies an amount in `from_currency` to produce `to_currency` (the same convention as ERPNext Currency Exchange):

```text
amount_in_to = amount_in_from * rate
```

Banguat publishes the US dollar as quetzales per 1 USD (`venta` on variable 2).

- `USD -> GTQ` stores that number. Example: `7.64312` means 1 USD = 7.64312 GTQ.
- `GTQ -> USD` stores the reciprocal. Example: `0.13084` means 1 GTQ = 0.13084 USD.

Other Banguat variables are quoted as units of that currency per 1 USD. Cambiare converts them to quetzales with `usd_to_gtq / units_per_usd` and stores both `XXX -> GTQ` and `GTQ -> XXX`.

The read API uses **Currency Exchange GTQ** when a date exists there, and otherwise **Currency Exchange**.

## Whitelisted API

Other apps, including Revelare's Direct Cash Flow report, call these methods. Dates are `YYYY-MM-DD`. `fetch_if_missing` defaults to `1`.

### `cambiare_gtq.exchange_rates.backfill_exchange_rates`

`backfill_exchange_rates(from_date, to_date, currency=None)`

Fetches `TipoCambioRango` / `TipoCambioRangoMoneda` and inserts missing rows. A row that already exists for the same date, from currency and to currency is skipped, not overwritten.

`currency` is an ISO code. Empty fetches USD plus every currency selected on Configuration Cambiare. `USD` or `GTQ` fetches only the dollar pair. Any other known code also stores USD for those dates, because Banguat quotes that currency against the dollar.

Returns `created`, `skipped`, `from_date`, `to_date` and `currencies`.

### `cambiare_gtq.exchange_rates.get_closing_rate`

`get_closing_rate(from_currency, to_currency, date, fetch_if_missing=1)`

Returns the rate registered on `date`. If it is missing and `fetch_if_missing` is true, that date is requested from Banguat and stored. If it is still missing, the latest registered row on or before `date` is used. If nothing exists, the method raises a translatable error.

```json
{
  "rate": 7.64312,
  "rate_date": "2026-11-15",
  "from_currency": "USD",
  "to_currency": "GTQ",
  "source": "exact",
  "meaning": "1 USD = 7.64312 GTQ"
}
```

`rate_date` is the date of the row actually used. `source` is `exact`, `banguat` (fetched and stored for that date), `inverse` (reciprocal of the opposite direction on that date), `fallback` (latest row on or before the date) or `identity` (same currency, rate 1).

### `cambiare_gtq.exchange_rates.get_average_rate`

`get_average_rate(from_currency, to_currency, from_date, to_date, fetch_if_missing=1)`

Simple unweighted arithmetic average of one rate per calendar day in the inclusive range. Each day is resolved like `get_closing_rate` (that day's row, otherwise the latest row on or before that day). This is the average used for a partial month. It is not weighted by transaction volume. `days` is the number of daily rates that were averaged.

```json
{
  "average": 7.641,
  "days": 10,
  "from_date": "2026-11-01",
  "to_date": "2026-11-10",
  "from_currency": "USD",
  "to_currency": "GTQ",
  "covered_from": "2026-11-01",
  "covered_to": "2026-11-10"
}
```

### `cambiare_gtq.convert.convert`

`convert(amount, from_currency, to_currency, date=None, from_date=None, to_date=None, method="daily", fetch_if_missing=1)`

`method` is `daily` (one date, default today) or `average` (unweighted mean of each day's rate). A direct pair is used when that date has a row. Otherwise the rate is crossed through GTQ, so EUR to BTC is the EUR/GTQ rate divided by the BTC/GTQ rate. `amount` in the response is a decimal string.

The desk page **Currency Converter** calls this method.

## Bundled history and Bitcoin

`cambiare_gtq/data/bundled_rates.csv.gz` holds one row per date and pair: Banguat rates versus GTQ for every currency the bank publishes, plus BTC/USD and BTC/GTQ from [Precyos](https://precyos.com). BTC/GTQ is the Precyos BTC/USD price times the Banguat as-of venta. The file is not a fixture. Install and migrate bulk-insert it, skipping any date and pair that already exists, so a hand-edited row is kept. Currency Exchange GTQ receives every bundled pair. ERPNext Currency Exchange receives a pair only when both currencies already exist. A date and pair that is already stored is skipped, including a Bisq row written after the file. USD to GTQ for a Bitcoin rate uses Currency Exchange GTQ when that date is there, and standard Currency Exchange otherwise. The app creates the Currency `BTC` (Bitcoin, symbol ₿, fraction Satoshi).

**Bitcoin Rate Source** on Configuration Cambiare defaults to Precyos. A scheduled run, after the Banguat pull, refreshes Bitcoin from `https://precyos.com/api/method/precyos.api.series?item_code=64.15.15.05.001`. The window is the last 14 days. Until BTC/USD exists for every day after the bundled Precyos series (2026-10-23), the window also includes that gap. Days Precyos does not publish are filled from the median of Bisq BTC/USD trades in the 24 hours before 00:00 UTC on that date (`https://markets.bisq.network/api/trades`), one request per day. That is the date convention Precyos uses. A day Bisq did not trade stays empty. Choosing Bisq uses that median for every day. `cambiare_gtq.btc_sync.refresh_btc_rates` runs the same refresh on demand. `cambiare_gtq.historical.reload_historical_rates` inserts any bundled rows that are still missing.

Each stored row has **Rate Source**: `Banguat`, `Precyos`, or `Bisq median`. A live Banguat pull sets that source. Migrate also fills `Banguat` on an existing row whose rate matches the bundled bank rate for that date and pair, and on the reciprocal of that rate. A different rate stays blank.

The Available Currencies list is built from Banguat's variable catalog. A saved row stays on the ISO code it already shows: `CHF` moves from variable 6 to variable 5, `GBP` from 8 to 9, and `VEF` from 22 to 37. Codes the bank does not publish (`KPW`, `BOB`, `BOV`) are rewritten to that variable's real code (`KRW`, `VEF`, `VES`).

Rates are sourced from Banco de Guatemala, Precyos, and Bisq. Thank you to all three.

## Scheduler

Configuration Cambiare → **Query Frequency** (`Hourly`, `Daily`, `Weekly`, `Monthly`) selects which scheduled job fetches today's Banguat rates and then refreshes Bitcoin. The Bitcoin window is the last 14 days, extended back through the first day still missing after the bundled Precyos series. **Disable Queries** turns the jobs off. USD is always fetched from Banguat. Extra currencies are the rows under Available Currencies. Live Banguat calls keep filling dates after the bundled file.

## Language

Labels, field names, options and messages are English. Spanish is in `cambiare_gtq/translations/es.csv`. Cheque amounts in words stay in Spanish because a Guatemalan cheque is written in Spanish.

## Tests

```bash
python3 cambiare_gtq/test_rate_logic.py
```

The tests mock Banguat. They do not need a site.

## License

GNU General Public License v3.0
