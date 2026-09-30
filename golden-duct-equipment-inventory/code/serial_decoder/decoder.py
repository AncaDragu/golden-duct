"""Decode a manufacture date from make + serial using the rule files.

Every rule that matches is returned as a ranked candidate. Ranking uses, in
order: how early the brand appears in the make text, agreement with a date
printed on the nameplate, equipment-type fit, rule confidence, a single
(unambiguous) year, and finally the newer year.
"""

from dataclasses import dataclass, field
from functools import lru_cache

from serial_decoder.brand_match import brand_position, equipment_tags, type_matches
from serial_decoder.constants import CONFIDENCE_BY_SCORE, CONFIDENCE_ORDER
from serial_decoder.date_parts import Period, candidate_years, resolve_period
from serial_decoder.rules import RuleSet, SerialRule, load_rules


@dataclass(frozen=True)
class NameplateDate:
    year: int | None = None
    month: int | None = None


@dataclass(frozen=True)
class DecodeCandidate:
    brand: str
    year: int
    month: int | None
    week: int | None
    day: int | None
    rule: SerialRule
    confidence: str
    brand_rank: int
    type_match: bool | None
    nameplate_match: bool | None
    other_years: tuple[int, ...]

    @property
    def date_text(self) -> str:
        if self.month is None:
            return f"{self.year} (year only)"
        text = f"{self.year}-{self.month:02d}"
        if self.day:
            text += f"-{self.day:02d}"
        if self.week:
            text += f" (week {self.week})"
        return text

    @property
    def rule_text(self) -> str:
        return (
            f"{self.rule.brand} {self.rule.era_start}-{self.rule.era_end}: "
            f"year {self.rule.year_rule}, period {self.rule.month_or_week_rule}"
        )


@dataclass
class DecodeResult:
    make: str
    serial: str
    candidates: list[DecodeCandidate] = field(default_factory=list)
    reason: str = ""

    @property
    def best(self) -> DecodeCandidate | None:
        return self.candidates[0] if self.candidates else None


@lru_cache(maxsize=1)
def default_rules() -> RuleSet:
    return load_rules()


def serial_variants(serial: str) -> list[str]:
    compact = "".join(serial.upper().split())
    stripped = compact.replace("-", "").replace(".", "")
    return list(dict.fromkeys([compact, stripped]))


def _nameplate_match(year: int, period: Period, nameplate: NameplateDate | None) -> bool | None:
    if nameplate is None or nameplate.year is None:
        return None
    if year != nameplate.year:
        return False
    if nameplate.month is None or period.month is None:
        return True
    return abs(period.month - nameplate.month) <= 1


def _adjusted_confidence(rule: SerialRule, ambiguous: bool, type_match: bool | None) -> str:
    score = CONFIDENCE_ORDER.get(rule.confidence, 0)
    score -= int(ambiguous) + int(type_match is False)
    return CONFIDENCE_BY_SCORE[max(score, 0)]


def _candidates_for_rule(
    rule: SerialRule,
    serial: str,
    brand_rank: int,
    tags: set[str],
    nameplate: NameplateDate | None,
) -> list[DecodeCandidate]:
    if rule.pattern is None:
        return []
    for variant in serial_variants(serial):
        match = rule.pattern.search(variant)
        if match:
            break
    else:
        return []
    dated = [(y, resolve_period(rule, match, y)) for y in candidate_years(rule, match)]
    valid = [(y, p) for y, p in dated if p is not None]
    type_match = type_matches(rule, tags)
    confidence = _adjusted_confidence(rule, len(valid) > 1, type_match)
    return [
        DecodeCandidate(
            brand=rule.brand,
            year=year,
            month=period.month,
            week=period.week,
            day=period.day,
            rule=rule,
            confidence=confidence,
            brand_rank=brand_rank,
            type_match=type_match,
            nameplate_match=_nameplate_match(year, period, nameplate),
            other_years=tuple(y for y, _ in valid if y != year),
        )
        for year, period in valid
    ]


def _rank_key(candidate: DecodeCandidate) -> tuple[int, int, int, int, int, int]:
    return (
        candidate.brand_rank,
        -int(candidate.nameplate_match is True) + int(candidate.nameplate_match is False),
        -int(candidate.type_match is True) + int(candidate.type_match is False),
        -CONFIDENCE_ORDER.get(candidate.confidence, 0),
        len(candidate.other_years),
        -candidate.year,
    )


def _brand_rules(make: str, rule_set: RuleSet) -> list[tuple[int, SerialRule]]:
    ranked = [(brand_position(make, rule), rule) for rule in rule_set.rules]
    return [(pos, rule) for pos, rule in ranked if pos is not None]


def _no_candidate_reason(brand_rules: list[tuple[int, SerialRule]]) -> str:
    if not brand_rules:
        return "No serial rule for this make"
    patternless = [rule for _, rule in brand_rules if rule.pattern is None]
    if len(patternless) == len(brand_rules):
        return patternless[0].notes or "No published date code for this make"
    brands = sorted({rule.brand for _, rule in brand_rules})
    return f"Serial does not match any known {', '.join(brands)} format"


def decode_serial(
    make: str,
    serial: str,
    equipment_type: str = "",
    nameplate: NameplateDate | None = None,
    rule_set: RuleSet | None = None,
) -> DecodeResult:
    result = DecodeResult(make=make, serial=serial)
    brand_rules = _brand_rules(make, rule_set or default_rules())
    if not serial.strip():
        result.reason = "No serial recorded"
        return result
    tags = equipment_tags(equipment_type)
    for position, rule in brand_rules:
        result.candidates.extend(_candidates_for_rule(rule, serial, position, tags, nameplate))
    result.candidates.sort(key=_rank_key)
    if not result.candidates:
        result.reason = _no_candidate_reason(brand_rules)
    return result
