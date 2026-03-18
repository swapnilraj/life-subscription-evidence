#!/usr/bin/env python3
"""Build reproducible comparative baseline metrics from primary APIs."""

from __future__ import annotations

import csv
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "research" / "data" / "provenance" / "comparative_primary_metrics.json"

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
COUNTRY_SETS = {
    "macro_core": ["CN", "US", "GB", "DE", "JP", "IN", "EUU"],
    "western_core": ["US", "GB", "DE", "FR", "NL", "EUU"],
    "finance_core": ["US", "GB", "DE", "FR", "NL", "EUU"],
}

WORLD_BANK_METRICS = {
    "gfcf_pct_gdp": {"indicator": "NE.GDI.FTOT.ZS", "countries": "macro_core", "years": [2000, 2010, 2020, 2024]},
    "manufacturing_pct_gdp": {
        "indicator": "NV.IND.MANF.ZS",
        "countries": "macro_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "rnd_pct_gdp": {"indicator": "GB.XPD.RSDV.GD.ZS", "countries": "macro_core", "years": [2000, 2010, 2020, 2024]},
    "education_spend_pct_gdp": {
        "indicator": "SE.XPD.TOTL.GD.ZS",
        "countries": "macro_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "tertiary_enrolment_pct": {
        "indicator": "SE.TER.ENRR",
        "countries": "macro_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "journal_articles_count": {
        "indicator": "IP.JRN.ARTC.SC",
        "countries": "macro_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "private_credit_pct_gdp": {
        "indicator": "FS.AST.PRVT.GD.ZS",
        "countries": "finance_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "market_cap_pct_gdp": {
        "indicator": "CM.MKT.LCAP.GD.ZS",
        "countries": "finance_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "health_spend_pct_gdp": {
        "indicator": "SH.XPD.CHEX.GD.ZS",
        "countries": "western_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "life_expectancy_years": {
        "indicator": "SP.DYN.LE00.IN",
        "countries": "western_core",
        "years": [2000, 2010, 2020, 2024],
    },
    "infant_mortality_per_1000": {
        "indicator": "SP.DYN.IMRT.IN",
        "countries": "western_core",
        "years": [2000, 2010, 2020, 2024],
    },
}

EUROSTAT_ENDPOINTS = {
    "housing_overburden_2024": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "ilc_lvho07a?geo=DE&geo=FR&geo=NL&geo=EU27_2020&time=2024"
        "&incgrp=TOTAL&age=TOTAL&sex=T&unit=PC&format=JSON"
    ),
    "rent_index_2015_2024": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "prc_hicp_aind?geo=DE&geo=FR&geo=NL&geo=EU27_2020"
        "&coicop=CP041&unit=INX_A_AVG&time=2015&time=2024&format=JSON"
    ),
    "house_price_index_2015_2024": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "prc_hpi_a?geo=DE&geo=FR&geo=NL&geo=EU27_2020"
        "&unit=I15_A_AVG&purchase=TOTAL&time=2015&time=2024&format=JSON"
    ),
}

FRED_SERIES = {
    "student_loans_owned_and_securitized": {
        "id": "SLOAS",
        "series_url": "https://fred.stlouisfed.org/series/SLOAS",
        "csv_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SLOAS",
    }
}


def _fetch_text(url: str, retries: int = 4, timeout: int = 45) -> str:
    request = Request(url, headers={"User-Agent": "life-subscription-primary-metrics/1.0"})
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt == retries:
                break
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _fetch_json(url: str) -> Dict:
    return json.loads(_fetch_text(url))


def _world_bank_series(country: str, indicator: str) -> Dict[str, float]:
    url = f"{WORLD_BANK_BASE}/country/{country}/indicator/{indicator}?format=json&per_page=200"
    payload = _fetch_json(url)
    if len(payload) < 2 or not isinstance(payload[1], list):
        return {}
    return {
        entry["date"]: entry["value"]
        for entry in payload[1]
        if isinstance(entry, dict) and entry.get("value") is not None
    }


def _latest_entry(year_map: Dict[str, float]) -> Dict[str, float | int]:
    if not year_map:
        return {"year": None, "value": None}
    latest_year = max(int(year) for year in year_map.keys())
    value = year_map[str(latest_year)]
    return {"year": latest_year, "value": value}


def _build_world_bank_metrics() -> Dict:
    output: Dict[str, Dict] = {}
    for metric_key, config in WORLD_BANK_METRICS.items():
        indicator = config["indicator"]
        countries = COUNTRY_SETS[config["countries"]]
        years = [str(year) for year in config["years"]]

        metric_payload = {
            "indicator": indicator,
            "countries": countries,
            "series": {},
        }

        for country in countries:
            year_map = _world_bank_series(country, indicator)
            selected = {year: year_map.get(year) for year in years}
            metric_payload["series"][country] = {
                "latest": _latest_entry(year_map),
                "selected_years": selected,
            }

        output[metric_key] = metric_payload

    return output


def _extract_eurostat_grid(payload: Dict) -> Dict[str, Dict[str, float]]:
    geos = list(payload["dimension"]["geo"]["category"]["index"].keys())
    times = list(payload["dimension"]["time"]["category"]["index"].keys())
    values = payload.get("value", {})
    grid: Dict[str, Dict[str, float]] = {}
    for geo_index, geo in enumerate(geos):
        series: Dict[str, float] = {}
        for time_index, year in enumerate(times):
            idx = geo_index * len(times) + time_index
            entry = values.get(str(idx))
            if entry is not None:
                series[year] = entry
        grid[geo] = series
    return grid


def _build_eurostat_metrics() -> Dict:
    output: Dict[str, Dict] = {}
    for metric_key, url in EUROSTAT_ENDPOINTS.items():
        payload = _fetch_json(url)
        output[metric_key] = {
            "url": url,
            "updated": payload.get("updated"),
            "series": _extract_eurostat_grid(payload),
        }
    return output


def _build_fred_metrics() -> Dict:
    output: Dict[str, Dict] = {}
    for metric_key, config in FRED_SERIES.items():
        series_id = config["id"]
        try:
            csv_text = _fetch_text(config["csv_url"])
            rows = list(csv.DictReader(io.StringIO(csv_text)))
            values = [row for row in rows if row.get(series_id) not in (None, "", ".")]
            if not values:
                latest = {"date": None, "value": None}
            else:
                latest_row = values[-1]
                latest = {
                    "date": latest_row["observation_date"],
                    "value": float(latest_row[series_id]),
                }
            fetch_error = None
        except RuntimeError as error:
            latest = {"date": None, "value": None}
            fetch_error = str(error)

        output[metric_key] = {
            "series_id": series_id,
            "series_url": config["series_url"],
            "csv_url": config["csv_url"],
            "latest": latest,
            "fetch_error": fetch_error,
        }

    return output


def build_payload() -> Dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "code/build_comparative_primary_metrics.py",
        "world_bank": _build_world_bank_metrics(),
        "eurostat": _build_eurostat_metrics(),
        "fred": _build_fred_metrics(),
    }


def main() -> None:
    payload = build_payload()
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
