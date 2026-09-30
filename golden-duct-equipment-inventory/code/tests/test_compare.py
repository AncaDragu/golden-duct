from efficiency_lookup.constants import CCMS_COMMERCIAL_GAS_STORAGE_WH, ES_COMMERCIAL_DISHWASHERS
from efficiency_lookup.lookup import EfficiencyResult, SourceHit
from efficiency_lookup.model_match import MatchQuality
from reference_lookup.compare import (
    csv_metrics,
    date_check,
    efficiency_check,
    nameplate_date_from_text,
)
from serial_decoder.decoder import NameplateDate, decode_serial


def _result(hit: SourceHit) -> EfficiencyResult:
    return EfficiencyResult(product_class="x", model="x", hits=[hit])


def test_nameplate_date_is_read_only_from_nameplate_wording() -> None:
    assert nameplate_date_from_text("Nameplate date of manufacture NOV 2012; installed under Feb 2013 permit") == (
        NameplateDate(2012, 11)
    )
    assert nameplate_date_from_text("Serial prefix 0813 = week 8 of 2013; matches Feb 2013 DBI permit") is None


def test_date_check_agrees_within_install_lag_and_flags_conflicts() -> None:
    best = decode_serial("Carrier", "4812E04427").best
    assert date_check("2013", "Nameplate date of manufacture NOV 2012", best) == "agrees"
    assert date_check("2016", "", best).startswith("conflicts")
    assert date_check("", "", best) == "fills blank: manufactured 2012"
    assert date_check("2013", "serial 4812 = week 47 of 2012", best).startswith("conflicts: basis text")


def test_csv_metrics_reads_free_text() -> None:
    assert csv_metrics("Cooling EER 11.0; gas heat 81% thermal efficiency") == {
        "EER": 11.0,
        "Thermal efficiency": 81.0,
    }
    assert csv_metrics("95.5% AFUE") == {"AFUE": 95.5}
    assert csv_metrics("13 SEER (series rating)") == {"SEER": 13.0}


def test_efficiency_check_agrees_with_series_range() -> None:
    hit = SourceHit(CCMS_COMMERCIAL_GAS_STORAGE_WH, MatchQuality("series", ""), [], {"Thermal efficiency %": (94.0, 96.0)}, {})
    text = "Not read; Phoenix series rated about 95% thermal efficiency"
    assert efficiency_check(text, _result(hit)) == "agrees on Thermal efficiency"


def test_efficiency_check_flags_listing_type_conflict() -> None:
    hit = SourceHit(
        ES_COMMERCIAL_DISHWASHERS,
        MatchQuality("exact", ""),
        ["AC"],
        {},
        {"machine type": "Under Counter - Glasswasher"},
    )
    check = efficiency_check("Unknown", _result(hit), "Commercial door-type dishwasher")
    assert check.startswith("conflicts: listing machine type")
