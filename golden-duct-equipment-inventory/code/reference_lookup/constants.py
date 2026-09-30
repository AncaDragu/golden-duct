"""Paths, output columns and extra nameplate readings for the reference lookup run."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
INVENTORY_PATH = PROJECT_DIR / "output" / "equipment_inventory.csv"
RESULTS_PATH = PROJECT_DIR / "output" / "reference_lookup_results.csv"

# Install year may trail manufacture by shipping and stock time.
MAX_INSTALL_LAG_YEARS = 2

# Efficiency values within this fraction of each other count as agreeing.
EFFICIENCY_TOLERANCE = 0.03

# Nameplates that sit inside another row's notes rather than its make/model/serial
# columns (a coil on top of a furnace). Read from the photos by the parent agent.
EXTRA_NAMEPLATES: list[dict[str, str]] = [
    {
        "equipment_id": "GD-FURN-02",
        "component": "Evaporator coil",
        "make": "ADP (Advanced Distributor Products)",
        "model": "C60A245C286",
        "serial": "7112B14424",
        "equipment_type": "Evaporator coil (cased, on gas furnace)",
    },
]

# Regexes that pull a comparable number out of free-text nameplate_efficiency.
# Keys match the metric names used by efficiency_lookup (without the % suffix).
CSV_METRIC_PATTERNS: dict[str, str] = {
    "SEER2": r"SEER2\s*(?:about\s*)?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*SEER2",
    "SEER": r"SEER(?!2)\s*(?:about\s*)?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*SEER(?!2)",
    "EER2": r"EER2\s*(?:about\s*)?(\d+(?:\.\d+)?)",
    "EER": r"(?<!S)EER(?!2)\s*(?:about\s*)?(\d+(?:\.\d+)?)",
    "AFUE": r"(\d+(?:\.\d+)?)\s*%\s*AFUE",
    "Thermal efficiency": r"(\d+(?:\.\d+)?)\s*%\s*thermal efficiency",
    "UEF": r"(\d?\.\d+)\s*UEF|UEF\s*(\d?\.\d+)",
}

# (inventory equipment_type keyword, listing text metric, text the listing must contain)
LISTING_TYPE_CHECKS: list[tuple[str, str, str]] = [
    ("door-type", "machine type", "Door"),
    ("under-counter", "machine type", "Under Counter"),
]

BLANK_EFFICIENCY_MARKERS = ("", "unknown", "n/a", "not read")

MONTH_PATTERN = r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s+(\d{4})\b"

OUTPUT_COLUMNS = [
    "equipment_id",
    "component",
    "make",
    "model",
    "serial",
    "decoded_date",
    "decode_rule",
    "decode_confidence",
    "decode_source",
    "decode_alternatives",
    "csv_install_year",
    "date_check",
    "efficiency_found",
    "efficiency_source",
    "match_quality",
    "match_detail",
    "csv_nameplate_efficiency",
    "efficiency_check",
    "notes",
]
