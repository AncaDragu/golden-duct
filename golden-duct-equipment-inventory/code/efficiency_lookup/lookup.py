"""Look up rated efficiency for an inventory row by make + model."""

import re
from dataclasses import dataclass, field

from efficiency_lookup.constants import (
    COMMERCIAL_PACKAGE_MIN_BTU_H,
    PRODUCT_CLASS_KEYWORDS,
    SEARCH_PREFIX_LENGTH,
    SERIES_FALLBACKS,
    SOURCES_BY_PRODUCT_CLASS,
    SeriesFallback,
    Source,
)
from efficiency_lookup.model_match import MatchQuality, clean_model, match_quality
from efficiency_lookup.sources import Row, rows_by_brand, rows_by_model_prefix

MetricRange = tuple[float, float]
MAX_LISTINGS_SHOWN = 3


@dataclass
class SourceHit:
    source: Source
    quality: MatchQuality
    listings: list[str]
    metrics: dict[str, MetricRange]
    text_metrics: dict[str, str]

    @property
    def summary(self) -> str:
        parts = [_format_metric(self.source, k, v) for k, v in self.metrics.items()]
        parts += [f"{k} {v}" for k, v in self.text_metrics.items()]
        return "; ".join(parts)

    @property
    def source_text(self) -> str:
        name = f"{self.source.title} ({self.source.dataset})" if self.source.title else self.source.dataset
        return f"{self.source.label}: {name}"


@dataclass
class EfficiencyResult:
    product_class: str | None
    model: str | None
    hits: list[SourceHit] = field(default_factory=list)
    note: str = ""

    @property
    def rated_hits(self) -> list[SourceHit]:
        return [h for h in self.hits if not h.source.pairing_only]

    @property
    def found(self) -> str:
        return " | ".join(h.summary for h in self.rated_hits if h.summary)

    @property
    def source_text(self) -> str:
        return " | ".join(h.source_text for h in self.rated_hits)

    @property
    def match_level(self) -> str:
        levels = [h.quality.level for h in self.hits]
        return max(levels, key=lambda lvl: MatchQuality(lvl, "").score) if levels else "none"

    @property
    def match_detail(self) -> str:
        return " | ".join(h.quality.detail for h in self.hits)

    @property
    def metrics(self) -> dict[str, MetricRange]:
        merged: dict[str, MetricRange] = {}
        for hit in self.rated_hits:
            merged.update(hit.metrics)
        return merged


def _format_number(value: float) -> str:
    return f"{value:,.0f}" if value >= 1000 else f"{value:g}"


def _format_metric(source: Source, name: str, value_range: MetricRange) -> str:
    low, high = value_range
    unit = "%" if name in source.percent_metrics else ""
    label = name.replace(" %", "")
    value = _format_number(low) if low == high else f"{_format_number(low)}-{_format_number(high)}"
    return f"{label} {value}{unit}"


def _numeric(value: object) -> float | None:
    try:
        return float(str(value))
    except ValueError:
        return None


def summarize_metrics(source: Source, rows: list[Row]) -> tuple[dict[str, MetricRange], dict[str, str]]:
    numeric: dict[str, MetricRange] = {}
    text: dict[str, str] = {}
    for name, field_name in source.metrics.items():
        values = [r.get(field_name) for r in rows if r.get(field_name) not in (None, "")]
        numbers = [n * source.scales.get(name, 1.0) for n in map(_numeric, values) if n is not None]
        if numbers:
            numeric[name] = (min(numbers), max(numbers))
        elif values:
            text[name] = " / ".join(sorted({str(v) for v in values}))
    return numeric, text


def classify_product(equipment_type: str, capacity: str = "") -> str | None:
    text = equipment_type.lower()
    for keyword, product_class in PRODUCT_CLASS_KEYWORDS:
        if keyword in text:
            if product_class == "packaged_unit_small" and _cooling_btu_h(capacity) >= COMMERCIAL_PACKAGE_MIN_BTU_H:
                return "packaged_unit_large"
            return product_class
    return None


def _cooling_btu_h(capacity: str) -> float:
    match = re.search(r"([\d,]+)\s*Btu/h cooling", capacity)
    return float(match.group(1).replace(",", "")) if match else 0.0


def _best_hit(source: Source, model: str) -> SourceHit | None:
    rows = rows_by_model_prefix(source, model[:SEARCH_PREFIX_LENGTH])
    scored = [(match_quality(model, str(r.get(source.model_field, ""))), r) for r in rows]
    scored = [(q, r) for q, r in scored if q is not None]
    if not scored:
        return None
    top = max(q.score for q, _ in scored)
    best = [(q, r) for q, r in scored if q.score == top]
    listings = sorted({str(r.get(source.model_field)) for _, r in best})
    numeric, text = summarize_metrics(source, [r for _, r in best])
    return SourceHit(source, best[0][0], listings[:MAX_LISTINGS_SHOWN], numeric, text)


def _series_fallback(make: str, context: str) -> SeriesFallback | None:
    make_text, context_text = make.lower(), context.lower()
    return next(
        (s for s in SERIES_FALLBACKS if s.brand_keyword in make_text and s.text_keyword in context_text),
        None,
    )


def _series_hit(fallback: SeriesFallback) -> SourceHit | None:
    rows = rows_by_brand(fallback.source, fallback.brand_keyword, fallback.extra_filter)
    rows = [r for r in rows if re.match(fallback.model_regex, str(r.get(fallback.source.model_field, "")))]
    if not rows:
        return None
    numeric, text = summarize_metrics(fallback.source, rows)
    detail = f"series only: {len(rows)} certified {fallback.text_keyword} models, range shown; exact model not read"
    listings = sorted({str(r.get(fallback.source.model_field)) for r in rows})
    return SourceHit(fallback.source, MatchQuality("series", detail), listings[:MAX_LISTINGS_SHOWN], numeric, text)


def lookup_efficiency(make: str, model_text: str, equipment_type: str, capacity: str = "") -> EfficiencyResult:
    product_class = classify_product(equipment_type, capacity)
    model = clean_model(model_text or "")
    result = EfficiencyResult(product_class=product_class, model=model)
    if product_class is None:
        result.note = "No public certification dataset covers this equipment type"
        return result
    if model is None:
        fallback = _series_fallback(make, f"{model_text} {equipment_type}")
        hit = _series_hit(fallback) if fallback else None
        result.hits = [hit] if hit else []
        result.note = "Model number not read" + ("; series range used" if hit else "; no lookup possible")
        return result
    result.hits = [h for s in SOURCES_BY_PRODUCT_CLASS[product_class] if (h := _best_hit(s, model))]
    if not result.hits:
        result.note = "No listing matches; ENERGY STAR and CCMS drop discontinued models"
    elif not result.rated_hits:
        pairings = "; ".join(h.summary for h in result.hits)
        result.note = (
            "Listed only in pairings with current outdoor units "
            f"({pairings}); no rating applies to this system"
        )
    return result
