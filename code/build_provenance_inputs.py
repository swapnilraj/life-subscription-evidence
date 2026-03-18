#!/usr/bin/env python3
"""Build provenance model inputs from primary-source fetch + deterministic extraction.

This script provides a reproducible codepath for generating cached
`research/data/provenance/model_inputs/*.json` files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import io
import json
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
PROV_DIR = ROOT / "research" / "data" / "provenance"
RAW_DIR = PROV_DIR / "raw"
MODEL_INPUT_DIR = PROV_DIR / "model_inputs"


@dataclass
class ExtractionResult:
    value: float
    source_id: str
    rule: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_registry() -> Dict:
    with open(PROV_DIR / "primary_sources.json", "r") as handle:
        return json.load(handle)


def _artifact_suffix(source: Dict[str, Any]) -> str:
    artifact_format = source.get("artifact_format", "html").lower()
    if artifact_format == "csv":
        return "csv"
    if artifact_format == "ods":
        return "ods"
    if artifact_format == "xlsx":
        return "xlsx"
    if artifact_format == "json":
        return "json"
    if artifact_format == "txt":
        return "txt"
    return "html"


def _looks_rate_limited(content: bytes) -> bool:
    marker_a = b"Rate limited - too many HTTP requests"
    marker_b = b"Temporary access block to this page"
    return marker_a in content or marker_b in content


def _request_headers(url: str) -> Dict[str, str]:
    if "bankofengland.co.uk/boeapps/database/fromshowcolumns.asp" in url:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    if "ons.gov.uk/generator" in url:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
            ),
            "Accept": "text/csv,application/octet-stream,*/*;q=0.8",
        }
    return {"User-Agent": "life-subscription-provenance-bot/1.0"}


def fetch_source_artifacts(registry: Dict, refresh: bool = False, persist: bool = True) -> Dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "version": "1.0",
        "generated_utc": _now_iso(),
        "artifacts": {},
    }

    for source in registry["sources"]:
        source_id = source["id"]
        url = source["url"]
        out_path = RAW_DIR / f"{source_id}.{_artifact_suffix(source)}"
        artifact_format = source.get("artifact_format", "html")

        fetched_utc = None
        error = None

        try:
            if refresh or not out_path.exists():
                last_exc: Exception | None = None
                content = b""
                status = 0
                for attempt in range(3):
                    try:
                        response = requests.get(
                            url,
                            timeout=45,
                            headers=_request_headers(url),
                        )
                        status = response.status_code
                        response.raise_for_status()
                        content = response.content
                        if _looks_rate_limited(content):
                            raise RuntimeError("temporary_rate_limit_page_detected")
                        break
                    except Exception as exc:
                        last_exc = exc
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                        else:
                            raise last_exc
                out_path.write_bytes(content)
                fetched_utc = _now_iso()
            else:
                content = out_path.read_bytes()
                status = 200
        except Exception as exc:
            if out_path.exists():
                content = out_path.read_bytes()
                status = 200
                error = f"fetch_failed_using_cached_artifact: {exc}"
            else:
                content = b""
                status = 0
                error = str(exc)

        artifacts["artifacts"][source_id] = {
            "url": url,
            "artifact_format": artifact_format,
            "path": str(out_path.relative_to(ROOT)),
            "status": status,
            "sha256": _sha256(content) if content else None,
            "fetched_utc": fetched_utc,
            "error": error,
        }

    if persist:
        with open(PROV_DIR / "source_artifacts.lock.json", "w") as handle:
            json.dump(artifacts, handle, indent=2)

    return artifacts


def validate_artifact_hashes(registry: Dict, artifacts: Dict) -> None:
    mismatches = []
    missing_required = []

    artifact_map = artifacts.get("artifacts", {})
    for source in registry.get("sources", []):
        source_id = source["id"]
        artifact = artifact_map.get(source_id, {})
        actual_hash = artifact.get("sha256")
        expected_hash = source.get("expected_sha256")
        required_for_extraction = source.get("required_for_extraction", False)

        if required_for_extraction and not actual_hash:
            missing_required.append(source_id)
            continue

        if expected_hash and actual_hash and expected_hash != actual_hash:
            mismatches.append((source_id, expected_hash, actual_hash))

    if missing_required or mismatches:
        messages = []
        if missing_required:
            messages.append(f"Missing required source artifacts: {', '.join(sorted(missing_required))}")
        if mismatches:
            diff_text = "; ".join(
                f"{source_id} expected={expected} actual={actual}"
                for source_id, expected, actual in mismatches
            )
            messages.append(f"Source hash drift detected: {diff_text}")
        messages.append("Review source changes, then run with --bless-source-hashes to accept new hashes.")
        raise ValueError(" | ".join(messages))


def bless_source_hashes(registry: Dict, artifacts: Dict) -> None:
    artifact_map = artifacts.get("artifacts", {})
    for source in registry.get("sources", []):
        artifact = artifact_map.get(source["id"], {})
        if artifact.get("sha256"):
            source["expected_sha256"] = artifact["sha256"]
    registry["updated_utc"] = _now_iso()
    with open(PROV_DIR / "primary_sources.json", "w") as handle:
        json.dump(registry, handle, indent=2)


def _extract_with_regex(
    text: str,
    pattern: str,
    source_id: str,
    cast=float,
    flags: int = re.S | re.I,
) -> ExtractionResult:
    match = re.search(pattern, text, flags)
    if not match:
        raise ValueError(f"Pattern did not match for {source_id}: {pattern}")

    raw = match.group(1).replace(",", "")
    value = cast(raw)
    return ExtractionResult(value=value, source_id=source_id, rule=pattern)


def _html_to_text(path: Path) -> str:
    html = path.read_text(errors="ignore")
    return html_lib.unescape(re.sub(r"<[^>]+>", " ", html))


def _load_csv_rows(path: Path) -> list[list[str]]:
    csv.field_size_limit(10_000_000)
    text = path.read_text(errors="ignore")
    return list(csv.reader(io.StringIO(text)))


def _load_ods_rows(path: Path, table_name: str | None = None) -> list[list[str]]:
    with zipfile.ZipFile(path, "r") as archive:
        content = archive.read("content.xml")

    root = ET.fromstring(content)
    namespaces = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }
    spreadsheet = root.find(".//office:spreadsheet", namespaces)
    if spreadsheet is None:
        raise ValueError(f"Could not locate office:spreadsheet in ODS: {path}")

    target_table = None
    tables = spreadsheet.findall("table:table", namespaces)
    for table in tables:
        name = table.attrib.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name")
        if table_name is None or name == table_name:
            target_table = table
            break
    if target_table is None:
        raise ValueError(f"Could not find table '{table_name}' in ODS: {path}")

    rows: list[list[str]] = []
    for row in target_table.findall("table:table-row", namespaces):
        values: list[str] = []
        for cell in row.findall("table:table-cell", namespaces):
            col_repeat = int(
                cell.attrib.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated", "1")
            )
            text_parts = ["".join(node.itertext()) for node in cell.findall("text:p", namespaces)]
            text_value = " ".join(part.strip() for part in text_parts if part.strip()).strip()
            if not text_value:
                text_value = cell.attrib.get("{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value", "")
            values.extend([text_value] * col_repeat)
        rows.append(values.copy())
    return rows


def _parse_numeric(value: str) -> float:
    cleaned = re.sub(r"[^0-9.\\-]", "", value or "")
    if not cleaned:
        raise ValueError(f"Unable to parse numeric value from '{value}'")
    return float(cleaned)


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _extract_boe_latest_series(path: Path, source_id: str, series_code: str) -> ExtractionResult:
    html = path.read_text(errors="ignore")
    series_codes = re.findall(r"<strong class=['\"]highlight['\"]>([A-Z0-9]+)</strong>", html)
    if series_code not in series_codes:
        raise ValueError(f"Series {series_code} not found in BoE table")
    series_index = series_codes.index(series_code)

    rows = re.findall(r"<tr>\s*<td align=\"right\"[^>]*>([^<]+)</td>(.*?)</tr>", html, re.S)
    for date_text, row_html in reversed(rows):
        cells = [cell.strip() for cell in re.findall(r"<td align=\"right\"[^>]*>\s*([^<]+)\s*</td>", row_html, re.S)]
        if len(cells) <= series_index:
            continue
        raw_value = cells[series_index]
        if raw_value in {"..", ""}:
            continue
        value = float(raw_value.replace(",", ""))
        return ExtractionResult(
            value=value,
            source_id=source_id,
            rule=f"BoE fromshowcolumns table series={series_code}, date={date_text.strip()}",
        )

    raise ValueError(f"No populated observations found for BoE series {series_code}")


def _govuk_ldjson_to_text(path: Path) -> str:
    html = path.read_text(errors="ignore")
    script_blocks = re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", html, re.S | re.I)
    chunks: list[str] = []

    def _collect_strings(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                _collect_strings(value)
        elif isinstance(node, list):
            for value in node:
                _collect_strings(value)
        elif isinstance(node, str):
            chunks.append(node)

    for block in script_blocks:
        try:
            payload = json.loads(block)
        except Exception:
            continue
        _collect_strings(payload)

    if not chunks:
        return _html_to_text(path)

    text = html_lib.unescape(" ".join(chunks))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_latest_period_rate_from_section(
    text: str,
    section_pattern: str,
    source_id: str,
    section_label: str,
) -> ExtractionResult:
    section_match = re.search(section_pattern, text, re.S | re.I)
    if not section_match:
        raise ValueError(f"Section not found for {source_id}: {section_label}")
    section_text = section_match.group(1)
    period_rows = re.findall(
        r"(1 Sep \d{4}\s*to\s*31 Aug \d{4})\s*([0-9]+(?:\.[0-9]+)?)%\s*([0-9]+(?:\.[0-9]+)?)%",
        section_text,
        re.I,
    )
    if not period_rows:
        raise ValueError(f"No period rows found in {section_label} for {source_id}")
    period, _, rate = period_rows[-1]
    return ExtractionResult(
        value=float(rate),
        source_id=source_id,
        rule=f"{section_label}: latest period '{period}', extracted rate column",
    )


def _extract_council_tax_band_d_annual(path: Path, source_id: str) -> ExtractionResult:
    rows = _load_ods_rows(path, table_name="Table_2")
    england_row = next((row for row in rows if row and row[0].strip() == "England"), None)
    if england_row is None or len(england_row) < 4:
        raise ValueError("Could not locate England row in council-tax ODS table")
    annual_value = _parse_numeric(england_row[3])
    return ExtractionResult(
        value=annual_value,
        source_id=source_id,
        rule="ODS Table_2 row='England', column='Average council tax including parish precepts (Band D)'",
    )


def extract_primary_metrics(persist: bool = True) -> Dict[str, ExtractionResult]:
    required_paths = {
        "gov_repay_your_student_loan": RAW_DIR / "gov_repay_your_student_loan.html",
        "gov_icr_repayment_plans_interest_rates": RAW_DIR / "gov_icr_repayment_plans_interest_rates.html",
        "gov_council_tax_band_d_england_2024_25_table2": RAW_DIR / "gov_council_tax_band_d_england_2024_25_table2.ods",
        "gov_leasehold_extending_or_ending_lease": RAW_DIR / "gov_leasehold_extending_or_ending_lease.html",
        "ons_family_spending_fye_2024": RAW_DIR / "ons_family_spending_fye_2024.html",
        "ons_housing_affordability_2024": RAW_DIR / "ons_housing_affordability_2024.html",
        "ons_private_rent_and_house_prices_apr2024": RAW_DIR / "ons_private_rent_and_house_prices_apr2024.html",
        "ons_household_disposable_income": RAW_DIR / "ons_household_disposable_income.html",
        "boe_quoted_rates": RAW_DIR / "boe_quoted_rates.html",
        "ons_private_rent_fig1_csv": RAW_DIR / "ons_private_rent_fig1_csv.csv",
    }
    if any(not path.exists() for path in required_paths.values()):
        raise FileNotFoundError(
            "Required source artifacts missing. Run with --refresh-sources or ensure cache files exist."
        )

    gov_repay_text = _html_to_text(required_paths["gov_repay_your_student_loan"])
    gov_icr_interest_text = _govuk_ldjson_to_text(required_paths["gov_icr_repayment_plans_interest_rates"])
    leasehold_text = _html_to_text(required_paths["gov_leasehold_extending_or_ending_lease"])
    ons_spend_text = _html_to_text(required_paths["ons_family_spending_fye_2024"])
    affordability_text = _html_to_text(required_paths["ons_housing_affordability_2024"])
    rent_text = _html_to_text(required_paths["ons_private_rent_and_house_prices_apr2024"])
    income_text = _html_to_text(required_paths["ons_household_disposable_income"])

    # Prefer structured dataset endpoints where available; fall back to bulletin text extraction.
    spending_2024_result: ExtractionResult
    spending_fig1_csv = RAW_DIR / "ons_family_spending_fig1_csv.csv"
    spending_2024_result = _extract_with_regex(
        ons_spend_text,
        r"Average weekly household expenditure was\s*£?([0-9]+\.[0-9]+)",
        "ons_family_spending_fye_2024",
    )
    if spending_fig1_csv.exists():
        try:
            spending_fig1_rows = _load_csv_rows(spending_fig1_csv)
            spending_header = next(
                (
                    row
                    for row in spending_fig1_rows
                    if row and "Real-terms mean weekly expenditure" in row
                ),
                None,
            )
            if spending_header is None:
                raise ValueError("Could not find real-terms expenditure header in family-spending Figure 1 CSV")
            spending_value_idx = spending_header.index("Real-terms mean weekly expenditure")
            spending_2024 = next(
                (
                    row
                    for row in spending_fig1_rows
                    if row and row[0].strip() in {"FYE 2024", "2024"}
                ),
                None,
            )
            if spending_2024 is None:
                raise ValueError("Could not find FYE 2024 row in family-spending Figure 1 CSV")
            spending_2024_result = ExtractionResult(
                value=_parse_numeric(spending_2024[spending_value_idx]),
                source_id="ons_family_spending_fig1_csv",
                rule="CSV row='FYE 2024', column='Real-terms mean weekly expenditure'",
            )
        except Exception:
            spending_2024_result = _extract_with_regex(
                ons_spend_text,
                r"Average weekly household expenditure was\s*£?([0-9]+\.[0-9]+)",
                "ons_family_spending_fye_2024",
            )

    housing_weekly_result = _extract_with_regex(
        ons_spend_text,
        r"housing \(net\), fuel and power at 18%\s*\(£?([0-9]+\.[0-9]+)\)",
        "ons_family_spending_fye_2024",
    )
    transport_weekly_result = _extract_with_regex(
        ons_spend_text,
        r"Transport was the second biggest proportional expense at 14%\s*\(£?([0-9]+\.[0-9]+)\)",
        "ons_family_spending_fye_2024",
    )

    affordability_home_result = _extract_with_regex(
        affordability_text,
        r"median average home in England, at £([0-9,]+), cost",
        "ons_housing_affordability_2024",
    )
    affordability_earnings_result = _extract_with_regex(
        affordability_text,
        r"median average earnings of a full-time employee \(£([0-9,]+)\)",
        "ons_housing_affordability_2024",
    )
    affordability_ratio_result = _extract_with_regex(
        affordability_text,
        r"median average home in England, at £[0-9,]+, cost ([0-9]+\.[0-9]+) times",
        "ons_housing_affordability_2024",
    )
    affordability_table_csv = RAW_DIR / "ons_housing_affordability_table1_csv.csv"
    if affordability_table_csv.exists():
        try:
            affordability_rows = _load_csv_rows(affordability_table_csv)
            affordability_england = next((row for row in affordability_rows if row and row[0].strip() == "England"), None)
            if affordability_england is None:
                raise ValueError("Could not find England row in affordability table CSV")
            affordability_home_result = ExtractionResult(
                value=_parse_numeric(affordability_england[1]),
                source_id="ons_housing_affordability_table1_csv",
                rule="CSV row=England, column='Median House price (12 months to Sep 2024)'",
            )
            affordability_earnings_result = ExtractionResult(
                value=_parse_numeric(affordability_england[2]),
                source_id="ons_housing_affordability_table1_csv",
                rule="CSV row=England, column='Median Earnings'",
            )
            affordability_ratio_result = ExtractionResult(
                value=_parse_numeric(affordability_england[3]),
                source_id="ons_housing_affordability_table1_csv",
                rule="CSV row=England, column='2024 Affordability Ratio'",
            )
        except Exception:
            affordability_home_result = _extract_with_regex(
                affordability_text,
                r"median average home in England, at £([0-9,]+), cost",
                "ons_housing_affordability_2024",
            )
            affordability_earnings_result = _extract_with_regex(
                affordability_text,
                r"median average earnings of a full-time employee \(£([0-9,]+)\)",
                "ons_housing_affordability_2024",
            )
            affordability_ratio_result = _extract_with_regex(
                affordability_text,
                r"median average home in England, at £[0-9,]+, cost ([0-9]+\.[0-9]+) times",
                "ons_housing_affordability_2024",
            )

    rent_gb_result = _extract_with_regex(
        rent_text,
        r"average private rent in Great Britain was £([0-9,]+) in March 2024",
        "ons_private_rent_and_house_prices_apr2024",
    )
    rent_eng_result = _extract_with_regex(
        rent_text,
        r"Average private rent for England was £([0-9,]+) in March 2024",
        "ons_private_rent_and_house_prices_apr2024",
    )
    rent_inflation_result = _extract_with_regex(
        rent_text,
        r"Average private rent for England was £[0-9,]+ in March 2024, up ([0-9]+\.[0-9]+)%",
        "ons_private_rent_and_house_prices_apr2024",
    )
    rent_fig2_csv = RAW_DIR / "ons_private_rent_fig2_csv.csv"
    if rent_fig2_csv.exists():
        try:
            rent_rows = _load_csv_rows(rent_fig2_csv)
            rent_header = next((row for row in rent_rows if row and row[0].strip() == "Date"), None)
            if rent_header is None:
                raise ValueError("Could not find Date header in private-rent CSV")
            rent_gb_idx = rent_header.index("Great Britain")
            rent_eng_idx = rent_header.index("England")
            rent_mar_2024 = next((row for row in rent_rows if row and row[0].strip() == "Mar 2024"), None)
            rent_mar_2023 = next((row for row in rent_rows if row and row[0].strip() == "Mar 2023"), None)
            if rent_mar_2024 is None or rent_mar_2023 is None:
                raise ValueError("Could not find Mar 2024/Mar 2023 rows in private-rent CSV")
            england_rent_2024 = _parse_numeric(rent_mar_2024[rent_eng_idx])
            england_rent_2023 = _parse_numeric(rent_mar_2023[rent_eng_idx])
            rent_inflation_pct = ((england_rent_2024 / england_rent_2023) - 1) * 100
            rent_gb_result = ExtractionResult(
                value=_parse_numeric(rent_mar_2024[rent_gb_idx]),
                source_id="ons_private_rent_fig2_csv",
                rule="CSV row='Mar 2024', column='Great Britain'",
            )
            rent_eng_result = ExtractionResult(
                value=england_rent_2024,
                source_id="ons_private_rent_fig2_csv",
                rule="CSV row='Mar 2024', column='England'",
            )
            rent_inflation_result = ExtractionResult(
                value=round(rent_inflation_pct, 1),
                source_id="ons_private_rent_fig2_csv",
                rule="Derived from CSV rows 'Mar 2023' and 'Mar 2024', column='England'",
            )
        except Exception:
            rent_gb_result = _extract_with_regex(
                rent_text,
                r"average private rent in Great Britain was £([0-9,]+) in March 2024",
                "ons_private_rent_and_house_prices_apr2024",
            )
            rent_eng_result = _extract_with_regex(
                rent_text,
                r"Average private rent for England was £([0-9,]+) in March 2024",
                "ons_private_rent_and_house_prices_apr2024",
            )
            rent_inflation_result = _extract_with_regex(
                rent_text,
                r"Average private rent for England was £[0-9,]+ in March 2024, up ([0-9]+\.[0-9]+)%",
                "ons_private_rent_and_house_prices_apr2024",
            )

    rent_fig1_rows = _load_csv_rows(required_paths["ons_private_rent_fig1_csv"])
    rent_fig1_header = next((row for row in rent_fig1_rows if row and row[0].strip() == "Date"), None)
    if rent_fig1_header is None or "UK HPI" not in rent_fig1_header:
        raise ValueError("Could not find Date/UK HPI columns in private-rent Figure 1 CSV")
    uk_hpi_idx = rent_fig1_header.index("UK HPI")
    uk_hpi_series: list[Tuple[datetime, float]] = []
    for row in rent_fig1_rows[rent_fig1_rows.index(rent_fig1_header) + 1 :]:
        if not row or len(row) <= uk_hpi_idx:
            continue
        date_raw = row[0].strip()
        value_raw = row[uk_hpi_idx].strip()
        if not date_raw or not value_raw:
            continue
        try:
            date_value = datetime.strptime(date_raw, "%b %Y")
            uk_hpi_value = float(value_raw)
        except Exception:
            continue
        uk_hpi_series.append((date_value, uk_hpi_value))
    if not uk_hpi_series:
        raise ValueError("No UK HPI observations found in private-rent Figure 1 CSV")
    trailing_window = uk_hpi_series[-60:] if len(uk_hpi_series) >= 60 else uk_hpi_series
    house_price_growth_5y_avg_pct = sum(value for _, value in trailing_window) / len(trailing_window)
    house_price_growth_result = ExtractionResult(
        value=round(house_price_growth_5y_avg_pct, 3),
        source_id="ons_private_rent_fig1_csv",
        rule=(
            "CSV column='UK HPI' trailing mean over last "
            f"{len(trailing_window)} non-null monthly observations "
            f"({trailing_window[0][0].strftime('%b %Y')} to {trailing_window[-1][0].strftime('%b %Y')})"
        ),
    )

    plan1_interest_rate_result = _extract_latest_period_rate_from_section(
        gov_icr_interest_text,
        r"interest rate for Plan 1 loans by year:\s*(.*?)(?:Repayment Plan 2 loans|Repayment Plan 3 loans|Prevailing Market Rate)",
        "gov_icr_repayment_plans_interest_rates",
        "Plan 1 interest-rate table",
    )
    plan2_max_interest_rate_result = _extract_latest_period_rate_from_section(
        gov_icr_interest_text,
        r"maximum interest rates for Plan 2 loans by year:\s*(.*?)(?:Those earning £25,000|Repayment Plan 3 loans|Prevailing Market Rate)",
        "gov_icr_repayment_plans_interest_rates",
        "Plan 2 max-interest table",
    )
    council_tax_band_d_annual_result = _extract_council_tax_band_d_annual(
        required_paths["gov_council_tax_band_d_england_2024_25_table2"],
        "gov_council_tax_band_d_england_2024_25_table2",
    )

    metrics: Dict[str, ExtractionResult] = {
        "plan_1_threshold": _extract_with_regex(
            gov_repay_text,
            r"Plan 1 student loan.*?£([0-9,]+) a year",
            "gov_repay_your_student_loan",
        ),
        "plan_2_threshold": _extract_with_regex(
            gov_repay_text,
            r"Plan 2 student loan.*?£([0-9,]+) a year",
            "gov_repay_your_student_loan",
        ),
        "plan_5_threshold": _extract_with_regex(
            gov_repay_text,
            r"Plan 5 student loan.*?£([0-9,]+) a year",
            "gov_repay_your_student_loan",
        ),
        "plan_repayment_rate_pct": _extract_with_regex(
            gov_repay_text,
            r"pay\s*([0-9]+)%\s*of\s*your\s*income\s*over\s*the\s*lowest\s*threshold",
            "gov_repay_your_student_loan",
            cast=int,
        ),
        "plan_1_write_off_years": _extract_with_regex(
            gov_repay_text,
            r"Plan 1 loans get written off.*?on or after 1 September 2006.*?written off\s*([0-9]+)\s*years",
            "gov_repay_your_student_loan",
            cast=int,
        ),
        "plan_2_write_off_years": _extract_with_regex(
            gov_repay_text,
            r"Plan 2 loans are written off\s*([0-9]+)\s*years",
            "gov_repay_your_student_loan",
            cast=int,
        ),
        "plan_5_write_off_years": _extract_with_regex(
            gov_repay_text,
            r"Plan 5 loans are written off\s*([0-9]+)\s*years",
            "gov_repay_your_student_loan",
            cast=int,
        ),
        "plan_1_interest_rate_pct": plan1_interest_rate_result,
        "plan_2_max_interest_rate_pct": plan2_max_interest_rate_result,
        "weekly_expenditure_2024": spending_2024_result,
        "housing_weekly_2024": housing_weekly_result,
        "transport_weekly_2024": transport_weekly_result,
        "median_home_price_england_2024": affordability_home_result,
        "median_earnings_england_2024": affordability_earnings_result,
        "affordability_ratio_england_2024": affordability_ratio_result,
        "average_private_rent_gb_march_2024": rent_gb_result,
        "average_private_rent_england_march_2024": rent_eng_result,
        "rent_inflation_england_march_2024_pct": rent_inflation_result,
        "house_price_growth_uk_hpi_5y_avg_pct": house_price_growth_result,
        "average_council_tax_band_d_england_2024_25_annual": council_tax_band_d_annual_result,
        "lease_extension_cost_jump_threshold_years": _extract_with_regex(
            leasehold_text,
            r"When there are\s*([0-9]+)\s*years or less remaining on your lease, the cost of extending it increases significantly",
            "gov_leasehold_extending_or_ending_lease",
            cast=int,
        ),
        "median_household_disposable_income_uk_fye2023": _extract_with_regex(
            income_text,
            r"median household disposable income in the UK was £([0-9,]+), a decrease",
            "ons_household_disposable_income",
        ),
        "mortgage_rate_2y_75ltv_pct": _extract_boe_latest_series(
            required_paths["boe_quoted_rates"],
            source_id="boe_quoted_rates",
            series_code="IUMBV34",
        ),
        "savings_return_1y_fixed_bond_pct": _extract_boe_latest_series(
            required_paths["boe_quoted_rates"],
            source_id="boe_quoted_rates",
            series_code="IUMWTFA",
        ),
    }

    out = {
        "version": "1.0",
        "generated_utc": _now_iso(),
        "metrics": {
            key: {
                "value": item.value,
                "source_id": item.source_id,
                "rule": item.rule,
            }
            for key, item in metrics.items()
        },
    }
    if persist:
        with open(PROV_DIR / "extracted_metrics.json", "w") as handle:
            json.dump(out, handle, indent=2)

    return metrics


def _load_model_input(name: str) -> Dict:
    with open(MODEL_INPUT_DIR / name, "r") as handle:
        return json.load(handle)


def _write_model_input(name: str, payload: Dict) -> None:
    with open(MODEL_INPUT_DIR / name, "w") as handle:
        json.dump(payload, handle, indent=2)


def write_assumption_register() -> None:
    lines = [
        "# Model Assumption and Derived Register",
        "",
        "Generated by `code/build_provenance_inputs.py` from current `model_inputs/*.json`.",
        "",
        "This register distinguishes values that are source-derived vs explicit assumptions.",
        "",
    ]

    for file_path in sorted(MODEL_INPUT_DIR.glob("*_inputs.json")):
        payload = _load_model_input(file_path.name)
        lines.append(f"## {file_path.name}")
        lines.append("")
        lines.append("| Path | Kind | Details |")
        lines.append("|---|---|---|")
        for path, provenance in _iter_provenance_entries(payload):
            kind = provenance.get("kind", "")
            if kind == "assumption":
                source_ids = ", ".join(provenance.get("source_ids", []))
                basis = provenance.get("assumption_basis", "")
                assumption_class = provenance.get("assumption_class", "")
                details = f"class: {assumption_class}; basis: {basis}"
                if source_ids:
                    details = f"sources: {source_ids}; {details}"
            elif kind == "derived":
                source_ids = ", ".join(provenance.get("source_ids", []))
                method = provenance.get("method", "")
                details = f"sources: {source_ids}; method: {method}"
            else:
                details = f"source: {provenance.get('source_id', '')}"
            lines.append(f"| `{path}` | `{kind}` | {details} |")
        lines.append("")

    (PROV_DIR / "ASSUMPTION_REGISTER.md").write_text("\n".join(lines))


def regenerate_model_inputs(metrics: Dict[str, ExtractionResult], artifacts: Dict) -> None:
    metrics_payload = {
        key: {"value": item.value, "source_id": item.source_id, "rule": item.rule}
        for key, item in metrics.items()
    }
    generated_meta = {
        "generator": "code/build_provenance_inputs.py",
        "generated_utc": _now_iso(),
        "artifact_lock_sha256": _sha256(json.dumps(artifacts, sort_keys=True).encode()),
        "extracted_metrics_sha256": _sha256(json.dumps(metrics_payload, sort_keys=True).encode()),
    }

    # Student loans: thresholds from live GOV.UK extraction
    student = _load_model_input("student_loans_inputs.json")
    repayment_rate = round(metrics["plan_repayment_rate_pct"].value / 100, 4)
    for plan in student["plans"]:
        if plan["name"] == "Plan 1":
            metric_key = "plan_1_threshold"
            write_off_key = "plan_1_write_off_years"
            interest_metric_key = "plan_1_interest_rate_pct"
            interest_note = f"interest_rate='{metrics[interest_metric_key].rule}'"
        elif plan["name"] == "Plan 2":
            metric_key = "plan_2_threshold"
            write_off_key = "plan_2_write_off_years"
            interest_metric_key = "plan_2_max_interest_rate_pct"
            interest_note = f"interest_rate='{metrics[interest_metric_key].rule}'"
        elif plan["name"] == "Plan 5":
            metric_key = "plan_5_threshold"
            write_off_key = "plan_5_write_off_years"
            interest_metric_key = "plan_2_max_interest_rate_pct"
            interest_note = (
                "interest_rate='Plan 5 proxy set equal to extracted Plan 2 latest max rate "
                f"rule ({metrics[interest_metric_key].rule})'"
            )
        else:
            continue
        plan["threshold"] = metrics[metric_key].value
        plan["rate"] = repayment_rate
        plan["interest_rate"] = round(metrics[interest_metric_key].value / 100, 4)
        plan["write_off_years"] = int(metrics[write_off_key].value)
        plan["provenance"] = {
            "kind": "derived",
            "source_ids": _unique_strings([metrics[metric_key].source_id, metrics[interest_metric_key].source_id]),
            "method": (
                "Policy extraction from cached source artifact using rules: "
                f"threshold='{metrics[metric_key].rule}', "
                f"repayment_rate='{metrics['plan_repayment_rate_pct'].rule}', "
                f"write_off='{metrics[write_off_key].rule}', "
                f"{interest_note}."
            ),
        }
    student["scenario_parameters"]["graduate_tax"]["threshold"] = metrics["plan_5_threshold"].value
    student["scenario_parameters"]["graduate_tax"]["rate"] = repayment_rate
    student["scenario_parameters"]["graduate_tax"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["gov_repay_your_student_loan", "gov_icr_repayment_plans_interest_rates"],
        "assumption_class": "scenario_model",
        "assumption_basis": (
            "Counterfactual benchmark definition; threshold is auto-set from extracted Plan 5 "
            "repayment threshold and rate auto-set from extracted statutory repayment rate; "
            "working years remains a scenario assumption."
        ),
    }
    student["scenario_parameters"]["default_salary_growth"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["ons_household_disposable_income"],
        "assumption_class": "common_parlance",
        "assumption_basis": "Scenario assumption for nominal annual salary progression anchored to ONS income trend context.",
    }
    student["salary_bands"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["gov_student_loans_england_2024_25"],
        "assumption_class": "scenario_model",
        "assumption_basis": "Representative salary bands for scenario analysis informed by borrower distribution context in official release.",
    }
    student["provenance_blocks"] = [
        {
            "name": "policy_parameters_extracted",
            "fields": ["plans[].threshold", "plans[].rate", "plans[].write_off_years"],
            "provenance": {
                "kind": "derived",
                "source_ids": ["gov_repay_your_student_loan"],
                "method": "Programmatically extracted from GOV.UK repayment-policy page during provenance build.",
            },
        },
        {
            "name": "plan_interest_rate_inputs",
            "fields": ["plans[0].interest_rate", "plans[1].interest_rate"],
            "provenance": {
                "kind": "derived",
                "source_ids": ["gov_icr_repayment_plans_interest_rates"],
                "method": (
                    "Programmatically extracted latest Plan 1 and Plan 2 interest-rate rows from "
                    "GOV.UK policy-statistics page."
                ),
            },
        },
        {
            "name": "plan5_interest_rate_proxy_assumption",
            "fields": ["plans[2].interest_rate"],
            "provenance": {
                "kind": "assumption",
                "source_ids": ["gov_icr_repayment_plans_interest_rates"],
                "assumption_class": "proxy",
                "assumption_basis": (
                    "Plan 5 borrower repayment cohort begins in 2026; model proxies Plan 5 effective "
                    "interest rate to the latest published Plan 2 maximum rate pending direct observed series."
                ),
            },
        },
        {
            "name": "plan_finance_assumptions",
            "fields": ["plans[].avg_debt"],
            "provenance": {
                "kind": "assumption",
                "source_ids": ["gov_student_loans_england_2024_25", "slc_annual_report_2024_25"],
                "assumption_class": "scenario_model",
                "assumption_basis": (
                    "Plan-level debt simplifications used for deterministic simulation; benchmarked against "
                    "official SLC/GOV.UK publications."
                ),
            },
        },
    ]
    student["generated"] = generated_meta
    _write_model_input("student_loans_inputs.json", student)

    # Historical: refresh extractable 2024 fields and explicitly mark backcast snapshots.
    historical = _load_model_input("historical_inputs.json")
    for snapshot in historical["snapshots"]:
        if snapshot["year"] != 2024:
            snapshot["provenance"] = {
                "kind": "assumption",
                "source_ids": [
                    "ons_family_spending_fig1_csv",
                    "ons_household_disposable_income",
                    "ons_housing_affordability_2024",
                    "boe_household_debt",
                    "gov_english_housing_survey",
                ],
                "assumption_class": "scenario_model",
                "assumption_basis": (
                    "Backcast scenario snapshot retained for longitudinal comparison; "
                    "not directly extracted from current cached source artifacts."
                ),
            }
            continue

        weekly_income_2024 = round(metrics["median_household_disposable_income_uk_fye2023"].value / 52, 2)
        snapshot["avg_weekly_income"] = weekly_income_2024
        snapshot["avg_weekly_expenditure"] = metrics["weekly_expenditure_2024"].value
        snapshot["house_price_to_income_ratio"] = metrics["affordability_ratio_england_2024"].value

        for category in snapshot["categories"]:
            if category["name"] == "Housing (net), fuel and power":
                category["weekly_amount"] = metrics["housing_weekly_2024"].value
                category["provenance"] = {
                    "kind": "derived",
                    "source_ids": [metrics["housing_weekly_2024"].source_id],
                    "method": (
                        "Regex extraction from cached source artifact using rule: "
                        f"{metrics['housing_weekly_2024'].rule}"
                    ),
                }
            if category["name"].startswith("Transport"):
                category["weekly_amount"] = metrics["transport_weekly_2024"].value
                category["provenance"] = {
                    "kind": "derived",
                    "source_ids": [metrics["transport_weekly_2024"].source_id],
                    "method": (
                        "Regex extraction from cached source artifact using rule: "
                        f"{metrics['transport_weekly_2024'].rule}"
                    ),
                }
            category["as_pct_of_income"] = round((category["weekly_amount"] / weekly_income_2024) * 100, 1)

        snapshot["provenance"] = {
            "kind": "derived",
            "source_ids": [
                metrics["weekly_expenditure_2024"].source_id,
                metrics["median_household_disposable_income_uk_fye2023"].source_id,
                metrics["affordability_ratio_england_2024"].source_id,
            ],
            "method": (
                "Computed from extracted metrics: weekly expenditure and category totals "
                f"from rule '{metrics['weekly_expenditure_2024'].rule}', "
                f"median disposable income from rule '{metrics['median_household_disposable_income_uk_fye2023'].rule}', "
                f"and affordability ratio from rule '{metrics['affordability_ratio_england_2024'].rule}'."
            ),
        }
    historical["generated"] = generated_meta
    _write_model_input("historical_inputs.json", historical)

    # Rent vs own: fill baseline market values from extracted official stats.
    rent_vs_own = _load_model_input("rent_vs_own_inputs.json")
    rent_params = rent_vs_own["parameters"]
    rent_params["property_price_2024"] = metrics["median_home_price_england_2024"].value
    rent_params["monthly_rent_2024"] = metrics["average_private_rent_gb_march_2024"].value
    rent_params["rent_inflation"] = round(metrics["rent_inflation_england_march_2024_pct"].value / 100, 4)
    rent_params["mortgage_rate"] = round(metrics["mortgage_rate_2y_75ltv_pct"].value / 100, 4)
    rent_params["house_price_growth"] = round(metrics["house_price_growth_uk_hpi_5y_avg_pct"].value / 100, 4)
    rent_params["savings_return"] = round(metrics["savings_return_1y_fixed_bond_pct"].value / 100, 4)
    rent_params["property_tax_monthly"] = round(
        metrics["average_council_tax_band_d_england_2024_25_annual"].value / 12, 2
    )
    market_source_ids = _unique_strings(
        [
            metrics["median_home_price_england_2024"].source_id,
            metrics["average_private_rent_gb_march_2024"].source_id,
            metrics["rent_inflation_england_march_2024_pct"].source_id,
            metrics["mortgage_rate_2y_75ltv_pct"].source_id,
            metrics["house_price_growth_uk_hpi_5y_avg_pct"].source_id,
            metrics["savings_return_1y_fixed_bond_pct"].source_id,
            metrics["average_council_tax_band_d_england_2024_25_annual"].source_id,
        ]
    )
    rent_vs_own["provenance_blocks"][0]["fields"] = [
        "property_price_2024",
        "monthly_rent_2024",
        "rent_inflation",
        "mortgage_rate",
        "house_price_growth",
        "savings_return",
        "property_tax_monthly",
    ]
    rent_vs_own["provenance_blocks"][0]["provenance"] = {
        "kind": "derived",
        "source_ids": market_source_ids,
        "method": (
            "Computed from extracted metrics: property price from rule "
            f"'{metrics['median_home_price_england_2024'].rule}' and private rent from rule "
            f"'{metrics['average_private_rent_gb_march_2024'].rule}', and rent inflation from rule "
            f"'{metrics['rent_inflation_england_march_2024_pct'].rule}', and mortgage rate from rule "
            f"'{metrics['mortgage_rate_2y_75ltv_pct'].rule}', and house-price growth from rule "
            f"'{metrics['house_price_growth_uk_hpi_5y_avg_pct'].rule}', and savings return from rule "
            f"'{metrics['savings_return_1y_fixed_bond_pct'].rule}', and council-tax baseline from rule "
            f"'{metrics['average_council_tax_band_d_england_2024_25_annual'].rule}'."
        ),
    }
    rent_vs_own["provenance_blocks"][1]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["boe_quoted_rates"],
        "assumption_class": "common_parlance",
        "assumption_basis": (
            "Mortgage term remains a scenario assumption; market rate is source-derived."
        ),
    }
    rent_vs_own["provenance_blocks"][1]["fields"] = ["mortgage_term_years"]
    rent_vs_own["provenance_blocks"][2]["fields"] = [
        "maintenance_percent",
    ]
    rent_vs_own["provenance_blocks"][2]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["ons_family_spending_fye_2024"],
        "assumption_class": "scenario_model",
        "assumption_basis": (
            "Home-maintenance burden remains a scenario parameter; baseline fixed costs and market rates "
            "are source-derived."
        ),
    }
    extra_blocks = [
        {
            "name": "fixed_housing_cost_assumptions",
            "fields": ["insurance_monthly", "renters_insurance_monthly"],
            "provenance": {
                "kind": "assumption",
                "source_ids": ["ons_family_spending_fye_2024"],
                "assumption_class": "scenario_model",
                "assumption_basis": (
                    "Representative monthly insurance assumptions informed by ONS household expenditure composition."
                ),
            },
        },
        {
            "name": "simulation_horizon_assumptions",
            "fields": ["start_year", "start_age", "years", "deposit_percent"],
            "provenance": {
                "kind": "assumption",
                "source_ids": ["ons_housing_affordability_2024"],
                "assumption_class": "common_parlance",
                "assumption_basis": (
                    "Simulation-horizon and deposit settings are scenario design parameters anchored to current "
                    "housing-affordability context."
                ),
            },
        },
    ]
    existing_by_name = {
        block.get("name"): block for block in rent_vs_own.get("provenance_blocks", []) if block.get("name")
    }
    for block in extra_blocks:
        if block["name"] in existing_by_name:
            existing_by_name[block["name"]].update(block)
        else:
            rent_vs_own.setdefault("provenance_blocks", []).append(block)
    rent_vs_own["provenance"] = {
        "kind": "derived",
        "source_ids": market_source_ids,
        "method": (
            "Computed from extracted metrics for baseline market inputs, with non-market "
            "scenario assumptions explicitly labeled."
        ),
    }
    rent_vs_own["generated"] = generated_meta
    _write_model_input("rent_vs_own_inputs.json", rent_vs_own)

    # Leasehold: anchor property baseline to extracted official housing price.
    leasehold = _load_model_input("leasehold_inputs.json")
    leasehold["property_value"]["value"] = metrics["median_home_price_england_2024"].value
    leasehold["property_value"]["provenance"] = {
        "kind": "derived",
        "source_ids": [metrics["median_home_price_england_2024"].source_id],
        "method": (
            "Computed from extracted metrics: property baseline from rule "
            f"'{metrics['median_home_price_england_2024'].rule}'."
        ),
    }
    leasehold["initial_service_charge"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["gov_english_housing_survey", "gov_leasehold_statistics"],
        "assumption_class": "scenario_model",
        "assumption_basis": (
            "Representative annual service charge scenario baseline; "
            "not directly machine-extracted from a primary-source table in this pipeline."
        ),
    }
    leasehold["lease_length"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["gov_leasehold_statistics"],
        "assumption_class": "common_parlance",
        "assumption_basis": "Scenario contract length baseline for lifecycle simulation.",
    }
    leasehold["extend_at_years"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["gov_leasehold_statistics", "gov_leasehold_extending_or_ending_lease"],
        "assumption_class": "policy_anchor",
        "assumption_basis": (
            "Policy-anchored timing assumption: GOV.UK lease guidance indicates extension costs increase "
            f"at {int(metrics['lease_extension_cost_jump_threshold_years'].value)} years or less remaining; "
            "model extends at 75 years as a conservative buffer."
        ),
    }
    leasehold["freehold_comparator"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["ons_family_spending_fye_2024"],
        "assumption_class": "scenario_model",
        "assumption_basis": "Comparator assumptions for long-run freehold maintenance costs.",
    }
    for scenario in leasehold["scenarios"]:
        scenario["provenance"] = {
            "kind": "assumption",
            "source_ids": ["gov_leasehold_statistics"],
            "assumption_class": "scenario_model",
            "assumption_basis": (
                "Ground-rent clause scenario for stress testing; "
                "modeled assumption rather than directly extracted microdata."
            ),
        }
    leasehold["provenance"] = {
        "kind": "derived",
        "source_ids": [metrics["median_home_price_england_2024"].source_id],
        "method": (
            "Computed from extracted metrics for property baseline, with all lease-term and "
            "ground-rent structures explicitly labeled as assumptions."
        ),
    }
    leasehold["generated"] = generated_meta
    _write_model_input("leasehold_inputs.json", leasehold)

    # Subscriptions: derive income baselines from extracted household disposable income.
    subscriptions = _load_model_input("subscriptions_inputs.json")
    historical_income = {snap["year"]: snap["avg_weekly_income"] for snap in historical["snapshots"]}
    baseline_monthly = metrics["median_household_disposable_income_uk_fye2023"].value / 12
    subscriptions["income_monthly"]["2025"] = round(baseline_monthly)
    subscriptions["income_monthly"]["2015"] = round(
        baseline_monthly * (historical_income[2015] / historical_income[2024])
    )
    subscriptions["income_monthly"]["2005"] = round(
        baseline_monthly * (historical_income[2005] / historical_income[2024])
    )
    subscriptions["income_monthly"]["provenance"] = {
        "kind": "derived",
        "source_ids": [
            metrics["median_household_disposable_income_uk_fye2023"].source_id,
            "ons_family_spending_fye_2024",
        ],
        "method": (
            "Computed from extracted metrics: baseline monthly income from rule "
            f"'{metrics['median_household_disposable_income_uk_fye2023'].rule}', then "
            "backcast to 2015/2005 using modeled historical income ratios."
        ),
    }
    for year_key in ["2005", "2015", "2025"]:
        subscriptions["household_stacks"][year_key]["provenance"] = {
            "kind": "assumption",
            "source_ids": ["ons_family_spending_fye_2024", "ons_household_disposable_income"],
            "assumption_class": "scenario_model",
            "assumption_basis": (
                "Category-level household stack is an explicit scenario model, not direct "
                "source extraction."
            ),
        }
    subscription_years = sorted(int(year_key) for year_key in subscriptions["household_stacks"].keys())
    subscription_counts = []
    for year in subscription_years:
        expenses = subscriptions["household_stacks"][str(year)]["expenses"]
        subscription_counts.append(float(sum(1 for expense in expenses if expense.get("is_subscription", False))))
    subscriptions["subscription_count_series"]["years"] = subscription_years
    subscriptions["subscription_count_series"]["counts"] = subscription_counts
    subscriptions["subscription_count_series"]["provenance"] = {
        "kind": "assumption",
        "source_ids": ["ons_family_spending_fye_2024"],
        "assumption_class": "scenario_model",
        "assumption_basis": (
            "Computed from modeled household stack definitions in this repository; "
            "not an externally measured household-level subscription count series."
        ),
    }
    subscriptions["provenance"] = {
        "kind": "derived",
        "source_ids": [metrics["median_household_disposable_income_uk_fye2023"].source_id],
        "method": (
            "Computed from extracted metrics for income baseline; stack compositions remain "
            "explicit scenario assumptions."
        ),
    }
    subscriptions["generated"] = generated_meta
    _write_model_input("subscriptions_inputs.json", subscriptions)


def verify_generated_inputs(metrics: Dict[str, ExtractionResult]) -> Tuple[bool, str]:
    student = _load_model_input("student_loans_inputs.json")
    expected = {
        "Plan 1": metrics["plan_1_threshold"].value,
        "Plan 2": metrics["plan_2_threshold"].value,
        "Plan 5": metrics["plan_5_threshold"].value,
    }
    for plan in student["plans"]:
        name = plan["name"]
        if name in expected and float(plan["threshold"]) != float(expected[name]):
            return False, f"Threshold mismatch for {name}: got {plan['threshold']}, expected {expected[name]}"

    historical = _load_model_input("historical_inputs.json")
    target = next((snapshot for snapshot in historical["snapshots"] if snapshot["year"] == 2024), None)
    if target is None:
        return False, "Missing 2024 snapshot in historical inputs"
    if float(target["avg_weekly_expenditure"]) != float(metrics["weekly_expenditure_2024"].value):
        return False, (
            "Historical weekly expenditure mismatch: "
            f"got {target['avg_weekly_expenditure']}, expected {metrics['weekly_expenditure_2024'].value}"
        )
    expected_weekly_income = round(metrics["median_household_disposable_income_uk_fye2023"].value / 52, 2)
    if float(target["avg_weekly_income"]) != float(expected_weekly_income):
        return False, (
            "Historical weekly income mismatch: "
            f"got {target['avg_weekly_income']}, expected {expected_weekly_income}"
        )

    rent_vs_own = _load_model_input("rent_vs_own_inputs.json")
    if float(rent_vs_own["parameters"]["property_price_2024"]) != float(metrics["median_home_price_england_2024"].value):
        return False, (
            "Rent-vs-own property_price_2024 mismatch: "
            f"got {rent_vs_own['parameters']['property_price_2024']}, "
            f"expected {metrics['median_home_price_england_2024'].value}"
        )
    if float(rent_vs_own["parameters"]["monthly_rent_2024"]) != float(metrics["average_private_rent_gb_march_2024"].value):
        return False, (
            "Rent-vs-own monthly_rent_2024 mismatch: "
            f"got {rent_vs_own['parameters']['monthly_rent_2024']}, "
            f"expected {metrics['average_private_rent_gb_march_2024'].value}"
        )
    expected_rent_inflation = round(metrics["rent_inflation_england_march_2024_pct"].value / 100, 4)
    if float(rent_vs_own["parameters"]["rent_inflation"]) != float(expected_rent_inflation):
        return False, (
            "Rent-vs-own rent_inflation mismatch: "
            f"got {rent_vs_own['parameters']['rent_inflation']}, expected {expected_rent_inflation}"
        )
    expected_house_growth = round(metrics["house_price_growth_uk_hpi_5y_avg_pct"].value / 100, 4)
    if float(rent_vs_own["parameters"]["house_price_growth"]) != float(expected_house_growth):
        return False, (
            "Rent-vs-own house_price_growth mismatch: "
            f"got {rent_vs_own['parameters']['house_price_growth']}, expected {expected_house_growth}"
        )
    expected_savings_return = round(metrics["savings_return_1y_fixed_bond_pct"].value / 100, 4)
    if float(rent_vs_own["parameters"]["savings_return"]) != float(expected_savings_return):
        return False, (
            "Rent-vs-own savings_return mismatch: "
            f"got {rent_vs_own['parameters']['savings_return']}, expected {expected_savings_return}"
        )
    expected_property_tax_monthly = round(metrics["average_council_tax_band_d_england_2024_25_annual"].value / 12, 2)
    if float(rent_vs_own["parameters"]["property_tax_monthly"]) != float(expected_property_tax_monthly):
        return False, (
            "Rent-vs-own property_tax_monthly mismatch: "
            f"got {rent_vs_own['parameters']['property_tax_monthly']}, expected {expected_property_tax_monthly}"
        )

    leasehold = _load_model_input("leasehold_inputs.json")
    if float(leasehold["property_value"]["value"]) != float(metrics["median_home_price_england_2024"].value):
        return False, (
            "Leasehold property_value mismatch: "
            f"got {leasehold['property_value']['value']}, expected {metrics['median_home_price_england_2024'].value}"
        )

    subscriptions = _load_model_input("subscriptions_inputs.json")
    expected_income_2025 = round(metrics["median_household_disposable_income_uk_fye2023"].value / 12)
    if int(subscriptions["income_monthly"]["2025"]) != int(expected_income_2025):
        return False, (
            "Subscriptions income_monthly[2025] mismatch: "
            f"got {subscriptions['income_monthly']['2025']}, expected {expected_income_2025}"
        )
    expected_grad_threshold = float(metrics["plan_5_threshold"].value)
    if float(student["scenario_parameters"]["graduate_tax"]["threshold"]) != expected_grad_threshold:
        return False, (
            "Graduate-tax threshold mismatch: "
            f"got {student['scenario_parameters']['graduate_tax']['threshold']}, expected {expected_grad_threshold}"
        )
    expected_repayment_rate = round(metrics["plan_repayment_rate_pct"].value / 100, 4)
    if float(student["scenario_parameters"]["graduate_tax"]["rate"]) != expected_repayment_rate:
        return False, (
            "Graduate-tax rate mismatch: "
            f"got {student['scenario_parameters']['graduate_tax']['rate']}, expected {expected_repayment_rate}"
        )
    for plan in student["plans"]:
        if float(plan["rate"]) != expected_repayment_rate:
            return False, f"Repayment rate mismatch for {plan['name']}: got {plan['rate']}, expected {expected_repayment_rate}"
    if int(next(plan for plan in student["plans"] if plan["name"] == "Plan 1")["write_off_years"]) != int(
        metrics["plan_1_write_off_years"].value
    ):
        return False, "Plan 1 write_off_years mismatch"
    if int(next(plan for plan in student["plans"] if plan["name"] == "Plan 2")["write_off_years"]) != int(
        metrics["plan_2_write_off_years"].value
    ):
        return False, "Plan 2 write_off_years mismatch"
    if int(next(plan for plan in student["plans"] if plan["name"] == "Plan 5")["write_off_years"]) != int(
        metrics["plan_5_write_off_years"].value
    ):
        return False, "Plan 5 write_off_years mismatch"
    expected_mortgage_rate = round(metrics["mortgage_rate_2y_75ltv_pct"].value / 100, 4)
    if float(rent_vs_own["parameters"]["mortgage_rate"]) != expected_mortgage_rate:
        return False, (
            "Rent-vs-own mortgage_rate mismatch: "
            f"got {rent_vs_own['parameters']['mortgage_rate']}, expected {expected_mortgage_rate}"
        )
    expected_plan1_interest = round(metrics["plan_1_interest_rate_pct"].value / 100, 4)
    if float(next(plan for plan in student["plans"] if plan["name"] == "Plan 1")["interest_rate"]) != expected_plan1_interest:
        return False, "Plan 1 interest_rate mismatch"
    expected_plan2_interest = round(metrics["plan_2_max_interest_rate_pct"].value / 100, 4)
    if float(next(plan for plan in student["plans"] if plan["name"] == "Plan 2")["interest_rate"]) != expected_plan2_interest:
        return False, "Plan 2 interest_rate mismatch"
    if float(next(plan for plan in student["plans"] if plan["name"] == "Plan 5")["interest_rate"]) != expected_plan2_interest:
        return False, "Plan 5 interest_rate proxy mismatch"

    return True, "Verification passed"


def _iter_provenance_entries(node: Any, path: str = "$") -> Iterator[Tuple[str, Dict[str, Any]]]:
    if isinstance(node, dict):
        provenance = node.get("provenance")
        if isinstance(provenance, dict):
            yield path, provenance
        for key, value in node.items():
            if key == "provenance":
                continue
            child = f"{path}.{key}" if path != "$" else f"$.{key}"
            yield from _iter_provenance_entries(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_provenance_entries(value, f"{path}[{index}]")


def _is_extraction_backed_method(method: str) -> bool:
    markers = [
        "Regex extraction from cached source artifact",
        "Policy extraction from cached source artifact",
        "Snapshot refreshed from cached source artifact",
        "Computed from extracted metrics",
        "Programmatically extracted from GOV.UK repayment-policy page",
        "Programmatically extracted latest Plan 1 and Plan 2 interest-rate rows",
    ]
    return any(marker in method for marker in markers)


def audit_extraction_coverage() -> None:
    report = {}
    for file_path in sorted(MODEL_INPUT_DIR.glob("*_inputs.json")):
        payload = json.loads(file_path.read_text())
        entries = list(_iter_provenance_entries(payload))
        extracted = 0
        assumptions = 0
        unresolved_paths = []
        for path, provenance in entries:
            method = provenance.get("method", "")
            kind = provenance.get("kind")
            if _is_extraction_backed_method(method):
                extracted += 1
            elif kind == "assumption":
                assumptions += 1
            else:
                unresolved_paths.append(path)
        report[file_path.name] = {
            "total_provenance_entries": len(entries),
            "extraction_backed_entries": extracted,
            "assumption_entries": assumptions,
            "non_extracted_entries": len(unresolved_paths),
            "sample_non_extracted_paths": unresolved_paths[:10],
        }

    print(json.dumps(report, indent=2))


def record_build_run(refresh_sources: bool) -> None:
    manifest_path = PROV_DIR / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {"version": "1.0", "runs": []}

    manifest.setdefault("runs", []).append(
        {
            "timestamp_utc": _now_iso(),
            "script": "build_provenance_inputs.py",
            "input_files": [
                "research/data/provenance/primary_sources.json",
                "research/data/provenance/raw/*.*",
            ],
            "output_files": [
                "research/data/provenance/source_artifacts.lock.json",
                "research/data/provenance/extracted_metrics.json",
                "research/data/provenance/model_inputs/*.json",
                "research/data/provenance/ASSUMPTION_REGISTER.md",
            ],
            "metadata": {"refresh_sources": refresh_sources},
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild provenance model inputs from source artifacts")
    parser.add_argument("--refresh-sources", action="store_true", help="Refetch source pages before extraction")
    parser.add_argument("--verify", action="store_true", help="Verify cached model inputs against current extraction")
    parser.add_argument("--audit", action="store_true", help="Print extraction coverage report for model inputs")
    parser.add_argument(
        "--bless-source-hashes",
        action="store_true",
        help="Update expected source hashes in primary_sources.json from currently cached/fetched artifacts",
    )
    args = parser.parse_args()

    registry = load_registry()
    persist_outputs = not args.verify
    artifacts = fetch_source_artifacts(
        registry,
        refresh=args.refresh_sources,
        persist=persist_outputs,
    )
    if args.bless_source_hashes:
        bless_source_hashes(registry, artifacts)
        registry = load_registry()
    validate_artifact_hashes(registry, artifacts)
    metrics = extract_primary_metrics(persist=persist_outputs)

    if args.verify:
        ok, message = verify_generated_inputs(metrics)
        print(message)
        if args.audit:
            audit_extraction_coverage()
        raise SystemExit(0 if ok else 1)

    regenerate_model_inputs(metrics, artifacts)
    write_assumption_register()
    record_build_run(refresh_sources=args.refresh_sources)
    ok, message = verify_generated_inputs(metrics)
    print(message)
    if args.audit:
        audit_extraction_coverage()


if __name__ == "__main__":
    main()
