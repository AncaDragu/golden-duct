import pytest

from efficiency_lookup import lookup
from efficiency_lookup.constants import CCMS_CENTRAL_AC, CCMS_FURNACES
from efficiency_lookup.lookup import classify_product, lookup_efficiency
from efficiency_lookup.model_match import clean_model, match_quality


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("48ESNA6011550", "48ESNA6011550"),
        ("24ABB360A520 (product 24ABB360A0052010; partly faded)", "24ABB360A520"),
        ("Phoenix (size not read; PH100/130/160/199 x 55/80/119 gal)", None),
        ("Not read (label cracked)", None),
        ("Prestige series, outdoor (model not read)", None),
        ("AC", "AC"),
        ("", None),
    ],
)
def test_clean_model(raw: str, expected: str | None) -> None:
    assert clean_model(raw) == expected


def test_single_char_wildcards_and_alternatives_match_exactly() -> None:
    quality = match_quality("C60A245L286", "C60A245L28(6,9)")
    assert quality is not None and quality.level == "exact"
    assert match_quality("PGD460090K001K1", "PGD460***K***K1").level == "exact"


def test_trailing_wildcard_allows_any_suffix() -> None:
    assert match_quality("PGD460090K001K1", "PGD460090K**1K*").level == "exact"


def test_one_character_difference_is_a_near_match() -> None:
    quality = match_quality("PGD460090H001K1", "PGD460***K***K1")
    assert quality is not None and quality.level == "near"
    assert "position 10" in quality.detail


def test_faded_model_matches_as_partial() -> None:
    quality = match_quality("24ABB360", "24ABB360A**52010")
    assert quality is not None and quality.level == "partial model"


def test_longer_model_matches_shorter_base_listing() -> None:
    quality = match_quality("PH199-80X", "PH199-80")
    assert quality is not None and quality.level == "listing prefix"


def test_unrelated_model_does_not_match() -> None:
    assert match_quality("48ESNA6011550", "PGD460***K***K1") is None


def test_classify_product_uses_capacity_for_packaged_units() -> None:
    rtu = "Packaged rooftop unit, gas heat / DX cooling"
    assert classify_product(rtu, "57,000 Btu/h cooling (about 5 tons)") == "packaged_unit_small"
    assert classify_product(rtu, "120,000 Btu/h cooling") == "packaged_unit_large"
    assert classify_product("Passenger elevator") is None


def test_lookup_combines_cooling_and_heating_listings(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures = {
        CCMS_CENTRAL_AC.dataset: [
            {
                CCMS_CENTRAL_AC.model_field: "PGD460***K***K1",
                "Seasonal_Energy_Efficiency_Ratio_2__SEER2__in_Btu_W_h_d": 13.4,
                "Energy_Efficiency_Ratio_2__EER2__in_Btu_W_h_d": 11.05,
            }
        ],
        CCMS_FURNACES.dataset: [
            {CCMS_FURNACES.model_field: "PGD460090K**1K*", "Annual_Fuel_Utilization_Efficiency_____d": 81.0},
            {CCMS_FURNACES.model_field: "PGD460130K**1K*", "Annual_Fuel_Utilization_Efficiency_____d": 81.0},
        ],
    }
    monkeypatch.setattr(lookup, "rows_by_model_prefix", lambda source, prefix: fixtures.get(source.dataset, []))
    result = lookup_efficiency("ICP", "PGD460090K001K1", "Packaged rooftop unit", "56,000 Btu/h cooling")
    assert result.match_level == "exact"
    assert "SEER2 13.4" in result.found and "AFUE 81%" in result.found
    assert result.metrics["AFUE %"] == (81.0, 81.0)


def test_lookup_reports_missing_model_without_network() -> None:
    result = lookup_efficiency("Rheem", "Prestige series, outdoor (model not read)", "Tankless gas water heater")
    assert result.found == ""
    assert "Model number not read" in result.note
