"""Decode serial dates and look up rated efficiency for every inventory row.

Reads output/equipment_inventory.csv (read only) and writes
output/reference_lookup_results.csv. Network responses are cached under
cache/efficiency_lookup/, so reruns are free.

Usage: uv run python run_reference_lookup.py  (from this code/ folder)
"""

import csv

from efficiency_lookup.lookup import EfficiencyResult, lookup_efficiency
from reference_lookup.compare import date_check, efficiency_check, nameplate_date_from_text
from reference_lookup.constants import (
    EXTRA_NAMEPLATES,
    INVENTORY_PATH,
    OUTPUT_COLUMNS,
    RESULTS_PATH,
)
from serial_decoder.decoder import DecodeResult, decode_serial, default_rules

MAX_ALTERNATIVES_SHOWN = 3


def read_inventory() -> list[dict[str, str]]:
    with INVENTORY_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _alternatives(decode: DecodeResult) -> str:
    others = decode.candidates[1 : 1 + MAX_ALTERNATIVES_SHOWN]
    return "; ".join(f"{c.date_text} via {c.rule.brand} {c.rule.era_start}-{c.rule.era_end}" for c in others)


def _decode_fields(decode: DecodeResult) -> dict[str, str]:
    best = decode.best
    if best is None:
        return {"decoded_date": "", "decode_rule": decode.reason, "decode_confidence": ""}
    return {
        "decoded_date": best.date_text,
        "decode_rule": best.rule_text,
        "decode_confidence": best.confidence,
        "decode_source": best.rule.source_url,
        "decode_alternatives": _alternatives(decode),
    }


def _efficiency_fields(result: EfficiencyResult, csv_efficiency: str, equipment_type: str) -> dict[str, str]:
    return {
        "efficiency_found": result.found,
        "efficiency_source": result.source_text,
        "match_quality": result.match_level,
        "match_detail": result.match_detail,
        "csv_nameplate_efficiency": csv_efficiency,
        "efficiency_check": efficiency_check(csv_efficiency, result, equipment_type),
        "notes": result.note,
    }


def build_result_row(item: dict[str, str], component: str, csv_row: dict[str, str]) -> dict[str, str]:
    # A component's own plate is separate from the parent row's install basis.
    basis = "" if component else csv_row.get("install_year_basis", "")
    decode = decode_serial(
        item["make"], item["serial"], item["equipment_type"], nameplate_date_from_text(basis)
    )
    efficiency = lookup_efficiency(
        item["make"], item["model"], item["equipment_type"], csv_row.get("capacity", "")
    )
    csv_efficiency = "" if component else csv_row.get("nameplate_efficiency", "")
    return {
        "equipment_id": csv_row["equipment_id"],
        "component": component,
        "make": item["make"],
        "model": item["model"],
        "serial": item["serial"],
        "csv_install_year": csv_row.get("install_year", ""),
        "date_check": date_check(csv_row.get("install_year", ""), basis, decode.best),
        **_decode_fields(decode),
        **_efficiency_fields(efficiency, csv_efficiency, item["equipment_type"]),
    }


def build_results(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["equipment_id"]: row for row in inventory}
    results = []
    for csv_row in inventory:
        results.append(build_result_row(csv_row, "", csv_row))
        for extra in EXTRA_NAMEPLATES:
            if extra["equipment_id"] == csv_row["equipment_id"]:
                results.append(build_result_row(extra, extra["component"], by_id[extra["equipment_id"]]))
    return results


def write_results(rows: list[dict[str, str]]) -> None:
    with RESULTS_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows({col: row.get(col, "") for col in OUTPUT_COLUMNS} for row in rows)


def main() -> None:
    rows = build_results(read_inventory())
    write_results(rows)
    warnings = default_rules().warnings
    print(f"wrote {len(rows)} rows to {RESULTS_PATH}; rule-file warnings: {len(warnings)}")
    for warning in warnings:
        print(f"  {warning}")


if __name__ == "__main__":
    main()
