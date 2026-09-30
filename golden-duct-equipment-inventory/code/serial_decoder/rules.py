"""Load serial-format rules from the research CSV files.

Rule grammar (one row per format, columns as in research/serial_formats.csv):

- pattern: a Python regex matched against the serial after upper-casing and
  removing spaces (hyphens and periods are kept). Date parts are best given
  as named groups: yyyy, yy, y (last digit of year), y1/y2 (split year
  digits), yl (year letter), ww (week), mm (month), ml (month letter or
  code), mw (month if <= 12 else week), dd (day of month), doy (day of year).
  The plain names year, month, week and day are also accepted.
- year_rule: "yyyy", "yy", "y", "concat:y1,y2", or
  "letter:A=2009,B=2010,...;cycle=20" (cycle optional: the letter repeats
  every N years). Positional prose such as "positions 3-4" also works.
  Blank or unrecognised text falls back to the named groups present.
- month_or_week_rule: "ww", "mm", "mw", "doy", "letters:ABCDEFGHJKLM"
  (the letter's position is the month), "none", or prose such as
  "week, positions 1-2". Blank falls back to the named groups present.
- era_start / era_end: years the format was in use. Blank end means current.

A row with a blank pattern records a brand with no published date code; the
notes column says why.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from serial_decoder.constants import CURRENT_YEAR, DEFAULT_ERA_START, RULE_FILES

DEFAULT_MONTH_LETTERS = "ABCDEFGHJKLM"
YEAR_KEYWORDS = ("yyyy", "yy", "y")
PERIOD_KEYWORDS = ("ww", "mm", "mw", "doy", "none")
GROUP_SYNONYMS = {"year": "year", "month": "mm", "week": "ww", "day": "dd"}
POSITION_RE = re.compile(
    r"(?:pos|positions?|chars?|characters?|digits?)\s*(\d+)(?:\s*(?:-|to|and|&|through)\s*(\d+))?",
    re.IGNORECASE,
)
PERIOD_WORDS = [("day of year", "doy"), ("julian", "doy"), ("week", "ww"), ("month", "mm")]


@dataclass(frozen=True)
class ValueSource:
    """Where a date part comes from: named regex groups or 1-based positions."""

    groups: tuple[str, ...] = ()
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True)
class YearSpec:
    kind: str  # yyyy, yy, y, letter, auto (decided by digit count)
    source: ValueSource
    letter_table: tuple[tuple[str, int], ...] = ()
    cycle: int | None = None


@dataclass(frozen=True)
class PeriodSpec:
    kind: str  # ww, mm, mw, doy, letters, none
    source: ValueSource
    letters: str = ""


@dataclass(frozen=True)
class SerialRule:
    rule_id: str
    brand: str
    brand_family: str
    aliases: tuple[str, ...]
    equipment_types: tuple[str, ...]
    era_start: int
    era_end: int
    pattern: re.Pattern[str] | None
    year: YearSpec | None
    period: PeriodSpec
    year_rule: str
    month_or_week_rule: str
    example_serial: str
    example_decoded: str
    source_url: str
    confidence: str
    notes: str

    @property
    def names(self) -> tuple[str, ...]:
        return (self.brand, *self.aliases)


@dataclass
class RuleSet:
    rules: list[SerialRule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _split_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


def _parse_year(value: str, default: int) -> int:
    match = re.search(r"\d{4}", value or "")
    return int(match.group()) if match else default


def _positions(text: str) -> ValueSource | None:
    match = POSITION_RE.search(text)
    if not match:
        return None
    start = int(match.group(1))
    return ValueSource(start=start, end=int(match.group(2) or start))


def _group_names(pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.groupindex)


def _letter_year_spec(text: str, groups: set[str]) -> YearSpec:
    body, _, options = text.removeprefix("letter:").partition(";")
    table = []
    for pair in body.split(","):
        letter, _, year = pair.partition("=")
        table.append((letter.strip().upper(), int(year)))
    cycle = re.search(r"cycle\s*=\s*(\d+)", options)
    group = "yl" if "yl" in groups else "year"
    return YearSpec("letter", ValueSource((group,)), tuple(table), int(cycle.group(1)) if cycle else None)


def _year_from_groups(groups: set[str]) -> YearSpec | None:
    for name in YEAR_KEYWORDS:
        if name in groups:
            return YearSpec(name, ValueSource((name,)))
    if {"y1", "y2"} <= groups:
        return YearSpec("yy", ValueSource(("y1", "y2")))
    if "year" in groups:
        return YearSpec("auto", ValueSource(("year",)))
    return None


def parse_year_rule(text: str, pattern: re.Pattern[str]) -> YearSpec | None:
    groups = _group_names(pattern)
    rule = text.strip()
    if rule.lower() in YEAR_KEYWORDS and rule.lower() in groups:
        return YearSpec(rule.lower(), ValueSource((rule.lower(),)))
    if rule.startswith("concat:"):
        names = tuple(n.strip() for n in rule.removeprefix("concat:").split(","))
        return YearSpec("yy", ValueSource(names))
    if rule.startswith("letter:"):
        return _letter_year_spec(rule, groups)
    from_groups = _year_from_groups(groups)
    if from_groups:
        return from_groups
    source = _positions(rule)
    return YearSpec("auto", source) if source else None


def _period_kind_from_words(text: str) -> str | None:
    lowered = text.lower()
    return next((kind for word, kind in PERIOD_WORDS if word in lowered), None)


def _period_from_groups(groups: set[str]) -> PeriodSpec:
    for name in ("ww", "mm", "mw", "doy"):
        if name in groups:
            return PeriodSpec(name, ValueSource((name,)))
    for synonym, name in (("week", "ww"), ("month", "mm")):
        if synonym in groups:
            return PeriodSpec(name, ValueSource((synonym,)))
    if "ml" in groups:
        return PeriodSpec("letters", ValueSource(("ml",)), DEFAULT_MONTH_LETTERS)
    return PeriodSpec("none", ValueSource())


def parse_period_rule(text: str, pattern: re.Pattern[str]) -> PeriodSpec:
    groups = _group_names(pattern)
    rule = text.strip()
    if rule.startswith("letters:"):
        group = "ml" if "ml" in groups else "month"
        return PeriodSpec("letters", ValueSource((group,)), rule.removeprefix("letters:").strip().upper())
    if rule.lower() == "none":
        return PeriodSpec("none", ValueSource())
    if rule.lower() in PERIOD_KEYWORDS and rule.lower() in groups:
        return PeriodSpec(rule.lower(), ValueSource((rule.lower(),)))
    from_groups = _period_from_groups(groups)
    if from_groups.kind != "none" or not rule:
        return from_groups
    source = _positions(rule)
    kind = _period_kind_from_words(rule)
    return PeriodSpec(kind, source) if source and kind else from_groups


def _row_to_rule(row: dict[str, str], rule_id: str) -> SerialRule:
    raw_pattern = (row.get("pattern") or "").strip()
    pattern = re.compile(raw_pattern) if raw_pattern else None
    year_rule = (row.get("year_rule") or "").strip()
    period_rule = (row.get("month_or_week_rule") or "").strip()
    year = parse_year_rule(year_rule, pattern) if pattern else None
    if pattern is not None and year is None:
        raise ValueError(f"cannot read year_rule {year_rule!r}")
    return SerialRule(
        rule_id=rule_id,
        brand=(row.get("brand") or "").strip(),
        brand_family=(row.get("brand_family") or "").strip(),
        aliases=_split_list(row.get("aliases") or ""),
        equipment_types=_split_list((row.get("equipment_types") or "").lower()),
        era_start=_parse_year(row.get("era_start", ""), DEFAULT_ERA_START),
        era_end=_parse_year(row.get("era_end", ""), CURRENT_YEAR),
        pattern=pattern,
        year=year,
        period=parse_period_rule(period_rule, pattern) if pattern else PeriodSpec("none", ValueSource()),
        year_rule=year_rule,
        month_or_week_rule=period_rule,
        example_serial=(row.get("example_serial") or "").strip(),
        example_decoded=(row.get("example_decoded") or "").strip(),
        source_url=(row.get("source_url") or "").strip(),
        confidence=(row.get("confidence") or "").strip(),
        notes=(row.get("notes") or "").strip(),
    )


def load_rule_file(path: Path, rule_set: RuleSet) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            rule_id = f"{path.stem}:{line_number}"
            try:
                rule = _row_to_rule(row, rule_id)
            except (re.error, ValueError) as exc:
                rule_set.warnings.append(f"{rule_id} ({row.get('brand', '')}) skipped: {exc}")
                continue
            if rule.brand:
                rule_set.rules.append(rule)


def load_rules(paths: list[Path] | None = None) -> RuleSet:
    rule_set = RuleSet()
    for path in paths or RULE_FILES:
        if path.exists():
            load_rule_file(path, rule_set)
    return rule_set
