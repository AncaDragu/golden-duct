"""Turn a serial-rule match into candidate years and a month, week and day."""

import re
from dataclasses import dataclass
from datetime import date, timedelta

from serial_decoder.constants import MAX_DAY_OF_YEAR, MAX_WEEK
from serial_decoder.rules import PeriodSpec, SerialRule, ValueSource, YearSpec

DAY_GROUPS = ("dd", "day")
YEAR_KIND_BY_WIDTH = {4: "yyyy", 2: "yy", 1: "y"}


@dataclass(frozen=True)
class Period:
    month: int | None
    week: int | None
    day: int | None


def week_to_month(year: int, week: int) -> int:
    # Mid-week day of the given week, so week 1 lands in January.
    return (date(year, 1, 1) + timedelta(days=(week - 1) * 7 + 3)).month


def extract(source: ValueSource, match: re.Match[str]) -> str | None:
    if source.groups:
        parts = [match.groupdict().get(name) for name in source.groups]
        return "".join(parts) if all(parts) else None
    if source.start is None or source.end is None:
        return None
    value = match.string[source.start - 1 : source.end]
    return value if len(value) == source.end - source.start + 1 else None


def _in_era(years: list[int], rule: SerialRule) -> list[int]:
    return [y for y in years if rule.era_start <= y <= rule.era_end]


def _years_ending_with(suffix: int, modulus: int, rule: SerialRule) -> list[int]:
    return [y for y in range(rule.era_start, rule.era_end + 1) if y % modulus == suffix]


def _letter_years(spec: YearSpec, letter: str, rule: SerialRule) -> list[int]:
    table = dict(spec.letter_table)
    if letter.upper() not in table:
        return []
    years = [table[letter.upper()]]
    while spec.cycle and years[-1] + spec.cycle <= rule.era_end:
        years.append(years[-1] + spec.cycle)
    return years


def _numeric_years(kind: str, value: str, rule: SerialRule) -> list[int]:
    if not value.isdigit():
        return []
    if kind == "auto":
        kind = YEAR_KIND_BY_WIDTH.get(len(value), "")
    if kind == "yyyy":
        return [int(value)]
    if kind == "yy":
        return _years_ending_with(int(value), 100, rule)
    if kind == "y":
        return _years_ending_with(int(value), 10, rule)
    return []


def candidate_years(rule: SerialRule, match: re.Match[str]) -> list[int]:
    """All years in the rule era consistent with the match, newest first."""
    spec = rule.year
    value = extract(spec.source, match) if spec else None
    if spec is None or value is None:
        return []
    if spec.kind == "letter":
        years = _letter_years(spec, value, rule)
    else:
        years = _numeric_years(spec.kind, value, rule)
    return sorted(set(_in_era(years, rule)), reverse=True)


def _period_from_week(year: int, week: int) -> Period | None:
    if not 1 <= week <= MAX_WEEK:
        return None
    return Period(month=week_to_month(year, week), week=week, day=None)


def _period_from_day_of_year(year: int, day_of_year: int) -> Period | None:
    if not 1 <= day_of_year <= MAX_DAY_OF_YEAR:
        return None
    day = date(year, 1, 1) + timedelta(days=day_of_year - 1)
    return Period(month=day.month, week=None, day=day.day) if day.year == year else None


def _month_period(month: int) -> Period | None:
    return Period(month, None, None) if 1 <= month <= 12 else None


def _numeric_period(kind: str, number: int, year: int) -> Period | None:
    if kind == "ww":
        return _period_from_week(year, number)
    if kind == "doy":
        return _period_from_day_of_year(year, number)
    if kind == "mw":
        return _month_period(number) or _period_from_week(year, number)
    return _month_period(number)


def _base_period(spec: PeriodSpec, match: re.Match[str], year: int) -> Period | None:
    if spec.kind == "none":
        return Period(None, None, None)
    value = extract(spec.source, match)
    if value is None:
        return None
    if spec.kind == "letters":
        position = spec.letters.find(value.upper())
        return Period(position + 1, None, None) if position >= 0 else None
    return _numeric_period(spec.kind, int(value), year) if value.isdigit() else None


def _day_is_valid(year: int, month: int | None, day: int) -> bool:
    if month is None:
        return 1 <= day <= 31
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def resolve_period(rule: SerialRule, match: re.Match[str], year: int) -> Period | None:
    """Month/week/day for one candidate year, or None if the match is not a real date."""
    period = _base_period(rule.period, match, year)
    day_text = next((match.groupdict().get(g) for g in DAY_GROUPS if match.groupdict().get(g)), None)
    if period is None or day_text is None or not day_text.isdigit():
        return period
    day = int(day_text)
    if not _day_is_valid(year, period.month, day):
        return None
    return Period(period.month, period.week, day)
