"""Fetch candidate listings from ENERGY STAR and DOE CCMS (cached)."""

from efficiency_lookup.constants import (
    CCMS_BRAND_FIELD,
    CCMS_LABEL,
    CCMS_PRODUCT_GROUP_FIELD,
    CCMS_SOLR_URL,
    ENERGY_STAR_BASE_URL,
    ENERGY_STAR_BRAND_FIELD,
    MAX_ROWS,
    Source,
)
from efficiency_lookup.http_cache import cached_get_json

Row = dict[str, object]


def _soql_literal(value: str) -> str:
    return value.replace("'", "''")


def _energy_star_rows(source: Source, where: str) -> list[Row]:
    url = f"{ENERGY_STAR_BASE_URL}/{source.dataset}.json"
    payload = cached_get_json(url, {"$where": where, "$limit": str(MAX_ROWS)})
    return payload if isinstance(payload, list) else []


def _ccms_rows(source: Source, filter_query: str) -> list[Row]:
    params = {
        "q": f'{CCMS_PRODUCT_GROUP_FIELD}:"{source.dataset}"',
        "fq": filter_query,
        "rows": str(MAX_ROWS),
        "wt": "json",
    }
    payload = cached_get_json(CCMS_SOLR_URL, params)
    response = payload.get("response", {}) if isinstance(payload, dict) else {}
    return list(response.get("docs", []))


def rows_by_model_prefix(source: Source, prefix: str) -> list[Row]:
    if source.label == CCMS_LABEL:
        return _ccms_rows(source, f"{source.model_field}:{prefix}*")
    where = f"upper({source.model_field}) like '{_soql_literal(prefix.upper())}%'"
    return _energy_star_rows(source, where)


def rows_by_brand(source: Source, brand: str, extra_filter: dict[str, str]) -> list[Row]:
    if source.label == CCMS_LABEL:
        rows = _ccms_rows(source, f'{CCMS_BRAND_FIELD}:"{brand.upper()}"')
    else:
        where = f"upper({ENERGY_STAR_BRAND_FIELD}) like '%{_soql_literal(brand.upper())}%'"
        rows = _energy_star_rows(source, where)
    return [r for r in rows if all(str(r.get(k, "")) == v for k, v in extra_filter.items())]
