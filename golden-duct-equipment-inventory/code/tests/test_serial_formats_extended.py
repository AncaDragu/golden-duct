import csv
import re

import pytest

from serial_decoder.constants import MONTH_ABBREVIATIONS, RULE_FILES
from serial_decoder.decoder import decode_serial
from serial_decoder.rules import RuleSet, SerialRule, load_rules

CSV_PATH = RULE_FILES[1]
EXPECTED_COLUMNS = [
    "brand",
    "brand_family",
    "aliases",
    "equipment_types",
    "era_start",
    "era_end",
    "pattern",
    "year_rule",
    "month_or_week_rule",
    "example_serial",
    "example_decoded",
    "source_url",
    "confidence",
    "notes",
]
CONFIDENCE_LEVELS = {"High", "Medium", "Low"}
EM_DASH = chr(0x2014)
MONTH_NAMES = [m.capitalize() for m in MONTH_ABBREVIATIONS]

RULE_SET: RuleSet = load_rules([CSV_PATH])
PATTERN_RULES = [rule for rule in RULE_SET.rules if rule.pattern is not None]


def _rule_id(rule: SerialRule) -> str:
    return f"{rule.rule_id} {rule.brand} {rule.example_serial}"


def _expected_year_and_month(text: str) -> tuple[int, int | None]:
    """Latest 4-digit year in the text (ambiguous cycles list several) and any month name."""
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", text)]
    month = next((i + 1 for i, name in enumerate(MONTH_NAMES) if name in text), None)
    return max(years), month


def test_header_matches_spec() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        assert next(csv.reader(f)) == EXPECTED_COLUMNS


def test_no_em_dashes() -> None:
    assert EM_DASH not in CSV_PATH.read_text(encoding="utf-8")


def test_every_row_loads_into_the_decoder() -> None:
    assert not RULE_SET.warnings
    assert len(PATTERN_RULES) >= 100


@pytest.mark.parametrize("rule", RULE_SET.rules, ids=_rule_id)
def test_confidence_and_source(rule: SerialRule) -> None:
    assert rule.confidence in CONFIDENCE_LEVELS
    assert rule.source_url.startswith("http")


@pytest.mark.parametrize("rule", PATTERN_RULES, ids=_rule_id)
def test_example_matches_own_pattern(rule: SerialRule) -> None:
    assert rule.pattern is not None
    assert rule.pattern.fullmatch(rule.example_serial), rule.pattern.pattern


@pytest.mark.parametrize("rule", PATTERN_RULES, ids=_rule_id)
def test_example_decodes_to_stated_date(rule: SerialRule) -> None:
    result = decode_serial(rule.brand, rule.example_serial, rule_set=RULE_SET)
    candidates = [c for c in result.candidates if c.rule.rule_id == rule.rule_id]
    year, month = _expected_year_and_month(rule.example_decoded)
    match = next((c for c in candidates if c.year == year), None)
    assert match is not None, f"years {[c.year for c in candidates]}, expected {year}"
    if month is not None:
        assert match.month == month
