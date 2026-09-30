import re

import pytest

from serial_decoder.constants import MONTH_ABBREVIATIONS
from serial_decoder.decoder import NameplateDate, decode_serial, default_rules
from serial_decoder.date_parts import week_to_month
from serial_decoder.rules import load_rules
from serial_decoder.constants import RULE_FILES

MONTH_NAMES = [m.capitalize() for m in MONTH_ABBREVIATIONS]


@pytest.mark.parametrize(
    ("make", "serial", "year", "week", "month"),
    [
        ("Carrier", "0813C35005", 2013, 8, 2),
        ("Carrier", "0813C35007", 2013, 8, 2),
        ("Carrier", "4812E04427", 2012, 48, 11),
        ("Carrier", "3014E16192", 2014, 30, 7),
        ("Carrier", "0313A43720", 2013, 3, 1),
        ("ICP (International Comfort Products, Carrier family)", "F242046717", 2024, 20, 5),
    ],
)
def test_inventory_serials_match_nameplate_dates(
    make: str, serial: str, year: int, week: int, month: int
) -> None:
    best = decode_serial(make, serial, "Packaged rooftop unit").best
    assert best is not None
    assert (best.year, best.week, best.month) == (year, week, month)
    assert best.confidence == "High"


def test_adp_coil_serial_decodes_to_february_2012() -> None:
    best = decode_serial("ADP", "7112B14424", "Evaporator coil").best
    assert best is not None
    assert (best.year, best.month) == (2012, 2)
    assert "inspectorhandbook.com/hvac/adp" in best.rule.source_url


def test_icp_make_prefers_icp_rule_over_carrier() -> None:
    best = decode_serial("ICP (International Comfort Products, Carrier family)", "F242046717").best
    assert best is not None
    assert best.brand == "ICP"


def test_brand_without_date_code_explains_why() -> None:
    result = decode_serial("Auto-Chlor", "10638", "Commercial dishwasher")
    assert result.best is None
    assert "No published serial date code" in result.reason


def test_unknown_brand_and_blank_serial() -> None:
    assert decode_serial("Acme Widgets", "12345").reason == "No serial rule for this make"
    assert decode_serial("Carrier", "").reason == "No serial recorded"


def test_bradford_white_returns_every_cycle_year_ranked_newest_first() -> None:
    result = decode_serial("Bradford White", "DG6322957", "Water heater")
    years = [c.year for c in result.candidates]
    assert years == [2007, 1987, 1967]
    assert result.best is not None and result.best.confidence == "Low"


def test_nameplate_date_picks_between_ambiguous_candidates() -> None:
    result = decode_serial(
        "Bradford White", "DG6322957", "Water heater", NameplateDate(year=1987)
    )
    assert result.best is not None and result.best.year == 1987


def test_rheem_water_heater_and_hvac_rules_rank_by_equipment_type() -> None:
    hvac = decode_serial("Rheem", "W291013412", "Packaged rooftop unit").best
    assert hvac is not None and (hvac.year, hvac.week) == (2010, 29)


def test_week_to_month_boundaries() -> None:
    assert week_to_month(2013, 1) == 1
    assert week_to_month(2012, 48) == 11
    assert week_to_month(2024, 20) == 5


def _expected_year_and_month(text: str) -> tuple[int, int | None]:
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", text)]
    month = next((i + 1 for i, name in enumerate(MONTH_NAMES) if name in text), None)
    return max(years), month


def test_every_rule_example_decodes_to_its_stated_answer() -> None:
    rule_set = load_rules([RULE_FILES[0]])
    assert not rule_set.warnings
    checked = 0
    for rule in rule_set.rules:
        if not rule.example_serial:
            continue
        result = decode_serial(rule.brand, rule.example_serial, rule_set=rule_set)
        years = {c.year for c in result.candidates if c.rule.rule_id == rule.rule_id}
        year, month = _expected_year_and_month(rule.example_decoded)
        assert year in years, f"{rule.rule_id} {rule.example_serial}"
        match = next(c for c in result.candidates if c.rule.rule_id == rule.rule_id and c.year == year)
        if month is not None:
            assert match.month == month, f"{rule.rule_id} {rule.example_serial}"
        checked += 1
    assert checked >= 25


def test_every_rule_with_a_pattern_cites_a_source() -> None:
    for rule in default_rules().rules:
        if rule.pattern is not None:
            assert rule.source_url.startswith("https://"), rule.rule_id


def test_extended_file_rules_load_and_bad_rows_are_reported(tmp_path) -> None:
    header = "brand,brand_family,aliases,equipment_types,era_start,era_end,pattern,year_rule,month_or_week_rule,example_serial,example_decoded,source_url,confidence,notes\n"
    extended = tmp_path / "serial_formats_extended.csv"
    extended.write_text(
        header
        + "Acme,Acme Corp,,hvac,2000,,^X(?P<yy>\\d{2})(?P<mm>\\d{2})\\d+$,,,X150612,Jun 2015,https://example.org,Medium,\n"
        + "Broken,Broken Co,,hvac,2000,,^(?P<yy>\\d{2,$,yy,mm,,,https://example.org,Low,\n"
    )
    rule_set = load_rules([RULE_FILES[0], extended])
    assert len(rule_set.warnings) == 1 and "Broken" not in {r.brand for r in rule_set.rules}
    best = decode_serial("Acme", "X150612", rule_set=rule_set).best
    assert best is not None and (best.year, best.month) == (2015, 6)


def test_positional_prose_and_plain_group_names_are_understood(tmp_path) -> None:
    header = "brand,brand_family,aliases,equipment_types,era_start,era_end,pattern,year_rule,month_or_week_rule,example_serial,example_decoded,source_url,confidence,notes\n"
    extended = tmp_path / "serial_formats_extended.csv"
    extended.write_text(
        header
        + 'Prose,Prose Co,,hvac,2000,,^[A-Z]{2}\\d{4}\\d+$,"positions 3-4, 2-digit year","week, positions 5-6",AB1422999,week 22 2014,https://example.org,Low,\n'
        + "Named,Named Co,,hvac,1990,,^(?P<month>\\d{2})(?P<year>\\d{4})-\\d+$,,,062011-55,Jun 2011,https://example.org,Low,\n"
    )
    rule_set = load_rules([extended])
    assert not rule_set.warnings
    prose = decode_serial("Prose", "AB1422999", rule_set=rule_set).best
    assert prose is not None and (prose.year, prose.week) == (2014, 22)
    named = decode_serial("Named", "062011-55", rule_set=rule_set).best
    assert named is not None and (named.year, named.month) == (2011, 6)
