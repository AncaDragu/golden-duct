"""Compare lookup results with the values already in the inventory CSV."""

import re

from efficiency_lookup.lookup import EfficiencyResult, MetricRange
from reference_lookup.constants import (
    BLANK_EFFICIENCY_MARKERS,
    CSV_METRIC_PATTERNS,
    EFFICIENCY_TOLERANCE,
    LISTING_TYPE_CHECKS,
    MAX_INSTALL_LAG_YEARS,
    MONTH_PATTERN,
)
from serial_decoder.constants import MONTH_ABBREVIATIONS
from serial_decoder.decoder import DecodeCandidate, NameplateDate


def nameplate_date_from_text(text: str) -> NameplateDate | None:
    """A printed manufacture date quoted in install_year_basis, if any."""
    match = re.search(rf"(?:DATE OF MANUFACTURE|NAMEPLATE)[^;]*?{MONTH_PATTERN}", text.upper())
    if not match:
        return None
    return NameplateDate(year=int(match.group(2)), month=MONTH_ABBREVIATIONS.index(match.group(1)) + 1)


def _stated_week(basis: str) -> int | None:
    match = re.search(r"week (\d+)", basis.lower())
    return int(match.group(1)) if match else None


def date_check(install_year: str, basis: str, best: DecodeCandidate | None) -> str:
    if best is None:
        return "no decode"
    if best.nameplate_match is False:
        return f"conflicts: nameplate date differs from serial ({best.date_text})"
    stated_week = _stated_week(basis)
    if stated_week is not None and best.week is not None and stated_week != best.week:
        return f"conflicts: basis text says week {stated_week}, serial says week {best.week}"
    if not install_year.strip().isdigit():
        return f"fills blank: manufactured {best.year}"
    lag = int(install_year) - best.year
    if 0 <= lag <= MAX_INSTALL_LAG_YEARS:
        return "agrees"
    return f"conflicts: CSV install {install_year}, serial says manufactured {best.year}"


def csv_metrics(text: str) -> dict[str, float]:
    found = {}
    for name, pattern in CSV_METRIC_PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found[name] = float(next(g for g in match.groups() if g))
    return found


def _lookup_metrics(result: EfficiencyResult) -> dict[str, MetricRange]:
    return {name.replace(" %", ""): value for name, value in result.metrics.items()}


def _agrees(value: float, value_range: MetricRange) -> bool:
    low, high = value_range
    return low * (1 - EFFICIENCY_TOLERANCE) <= value <= high * (1 + EFFICIENCY_TOLERANCE)


def listing_type_conflict(equipment_type: str, result: EfficiencyResult) -> str:
    """Flag a model match whose listed product type contradicts the inventory type."""
    text_metrics = {k: v for hit in result.rated_hits for k, v in hit.text_metrics.items()}
    for inventory_keyword, metric, required in LISTING_TYPE_CHECKS:
        listed = text_metrics.get(metric, "")
        if inventory_keyword in equipment_type.lower() and listed and required not in listed:
            return f"conflicts: listing {metric} is '{listed}', inventory says {inventory_keyword}"
    return ""


def efficiency_check(csv_text: str, result: EfficiencyResult, equipment_type: str = "") -> str:
    looked_up = _lookup_metrics(result)
    if not result.found:
        return "no data"
    type_conflict = listing_type_conflict(equipment_type, result)
    if type_conflict:
        return type_conflict
    efficiency_names = [n for n in looked_up if n in CSV_METRIC_PATTERNS]
    in_csv = csv_metrics(csv_text)
    if not in_csv and csv_text.strip().lower().split(";")[0] in BLANK_EFFICIENCY_MARKERS:
        return f"fills blank ({result.match_level} match)"
    shared = [n for n in efficiency_names if n in in_csv]
    conflicts = [n for n in shared if not _agrees(in_csv[n], looked_up[n])]
    if conflicts:
        return "conflicts: " + ", ".join(
            f"{n} CSV {in_csv[n]:g} vs listing {looked_up[n][0]:g}-{looked_up[n][1]:g}" for n in conflicts
        )
    added = [n for n in efficiency_names if n not in in_csv]
    status = "agrees on " + ", ".join(shared) if shared else "no shared metric"
    return status + (f"; adds {', '.join(added)}" if added else "")
