"""Constants for the serial-number date decoder.

The decode rules themselves are data, not code: they live in
research/serial_formats.csv (brands we verified for 360 9th St) and the
optional research/serial_formats_extended.csv (long-tail brands). Each rule
row cites its public source in the source_url column.
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
RULE_FILES = [
    PROJECT_DIR / "research" / "serial_formats.csv",
    PROJECT_DIR / "research" / "serial_formats_extended.csv",
]

# Newest plausible manufacture year. Two-digit years resolve into the rule era
# capped at this year.
CURRENT_YEAR = 2026

# A rule with a blank era_start is assumed to cover the last 50 years.
DEFAULT_ERA_START = CURRENT_YEAR - 50

CONFIDENCE_ORDER = {"High": 3, "Medium": 2, "Low": 1, "n/a": 0, "": 0}
CONFIDENCE_BY_SCORE = {3: "High", 2: "Medium", 1: "Low", 0: "Low"}

MONTH_ABBREVIATIONS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]

MAX_WEEK = 53
MAX_DAY_OF_YEAR = 366

# Keywords in an inventory equipment_type that map to the equipment_types tags
# used in the rule files. An inventory row can carry several tags.
EQUIPMENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "tankless_water_heater": ["tankless"],
    "water_heater": ["water heater", "water-heater"],
    "coil": ["coil"],
    "hvac": [
        "rooftop", "condensing unit", "furnace", "air handler", "heat pump",
        "split", "coil", "air conditioner", "packaged",
    ],
    "boiler": ["boiler"],
    "ice_machine": ["ice machine", "ice maker"],
    "refrigeration": ["refrigerator", "freezer", "reach-in", "walk-in"],
    "dishwasher": ["dishwasher"],
    "fan": ["exhaust fan", "fan"],
    "hood": ["hood"],
}

# Tags that accept any equipment type.
WILDCARD_EQUIPMENT_TAGS = {"any", "all", ""}
