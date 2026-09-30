"""Sources, field names and product classes for the efficiency lookup.

Sources (all free, no key):
- ENERGY STAR certified-product datasets, Socrata SODA API:
  https://data.energystar.gov (dataset ids below; catalog at
  https://data.energystar.gov/api/catalog/v1?domains=data.energystar.gov)
- DOE Compliance Certification Database (CCMS). The public search page
  https://www.regulations.doe.gov/certification-data/ is backed by a Solr
  endpoint the page itself calls. It needs a browser User-Agent.

Not used: the AHRI Directory (https://www.ahridirectory.org). Its terms forbid
use in software and the data API is a paid subscription. CEC MAEDbS keeps
archived models but has no API, only a manual Excel export.

Both ENERGY STAR and CCMS list only models that are currently certified, so
discontinued models (most equipment older than about 5 years) drop out.
"""

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_DIR / "cache" / "efficiency_lookup"

ENERGY_STAR_BASE_URL = "https://data.energystar.gov/resource"
CCMS_SOLR_URL = "https://www.regulations.doe.gov/certification-data/solr/ccms/select"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 60
MAX_ROWS = 5000

# Characters of the cleaned model used as the database search prefix. Long
# enough to be selective, short enough to survive a faded suffix.
SEARCH_PREFIX_LENGTH = 4

ENERGY_STAR_LABEL = "ENERGY STAR"
CCMS_LABEL = "DOE CCMS"


@dataclass(frozen=True)
class Source:
    """One searchable product list and the rated values to report from it."""

    label: str  # ENERGY_STAR_LABEL or CCMS_LABEL
    dataset: str  # ENERGY STAR dataset id or CCMS Product_Group_s value
    model_field: str
    metrics: dict[str, str]  # display name -> field
    percent_metrics: frozenset[str] = field(default_factory=frozenset)
    # Multipliers that put a field on the same scale as the nameplate (0.95 -> 95%).
    scales: dict[str, float] = field(default_factory=dict)
    # Listings that rate a matched pair, not this component alone (indoor coils).
    pairing_only: bool = False
    title: str = ""  # readable dataset name for ENERGY STAR ids


CCMS_CENTRAL_AC = Source(
    label=CCMS_LABEL,
    dataset="Air Conditioners and Heat Pumps - Central",
    model_field="Individual_Model_Number_Covered_by_Basic_Model__Outdoor_Unit_or_Package_Unit__m",
    metrics={
        "SEER2": "Seasonal_Energy_Efficiency_Ratio_2__SEER2__in_Btu_W_h_d",
        "EER2": "Energy_Efficiency_Ratio_2__EER2__in_Btu_W_h_d",
        "Cooling Btu/h": "Cooling_Capacity__Btu_h__d",
    },
)
CCMS_CENTRAL_AC_INDOOR = Source(
    label=CCMS_LABEL,
    dataset="Air Conditioners and Heat Pumps - Central",
    model_field="Individual_Model_Number__Indoor_Unit___If_Applicable_m",
    metrics={
        "SEER2": "Seasonal_Energy_Efficiency_Ratio_2__SEER2__in_Btu_W_h_d",
    },
    pairing_only=True,
)
CCMS_COMMERCIAL_PACKAGE = Source(
    label=CCMS_LABEL,
    dataset="Air Conditioners and Heat Pumps - Commercial Package",
    model_field="Individual_Model_Number_Covered_by_Basic_Model_m",
    metrics={
        "IEER": "Integrated_Energy_Efficiency_Ratio__IEER__Btu_Wh___if_Applicable_d",
        "Cooling Btu/h": "Rated_Cooling_Capacity__Btu_hour__d",
    },
)
CCMS_FURNACES = Source(
    label=CCMS_LABEL,
    dataset="Furnaces",
    model_field="Individual_Model_Number_Covered_by_Basic_Model_m",
    metrics={
        "AFUE %": "Annual_Fuel_Utilization_Efficiency_____d",
        "Input Btu/h": "Input_Capacity__BTU_Hour__d",
    },
    percent_metrics=frozenset({"AFUE %"}),
)
CCMS_COMMERCIAL_GAS_STORAGE_WH = Source(
    label=CCMS_LABEL,
    dataset="Water Heaters and Boilers - Commercial Gas and Oil Fired Storage Water Heaters",
    model_field="Individual_Model_Number_Covered_by_Basic_Model_m",
    metrics={
        "Thermal efficiency %": "Thermal_Efficiency_____d",
        "Standby loss Btu/h": "Standby_Loss__Btu_hour__d",
        "Input Btu/h": "Input__Btu_hour__d",
        "Gallons": "Measured_or_Rated_Storage_Volume__gallons___As_Applicable__d",
    },
    percent_metrics=frozenset({"Thermal efficiency %"}),
)
ES_LIGHT_COMMERCIAL_HVAC = Source(
    label=ENERGY_STAR_LABEL,
    dataset="e4mh-a2u3",
    title="Light Commercial HVAC",
    model_field="model_number",
    metrics={
        "SEER2": "seer2_rating_btu_wh",
        "EER2": "eer2_rating_btu_wh",
        "IEER": "ieer_rating",
        "Cooling kBtu/h": "cooling_capacity_kbtu_h",
    },
)
ES_FURNACES = Source(
    label=ENERGY_STAR_LABEL,
    dataset="i97v-e8au",
    title="Furnaces",
    model_field="model_number",
    metrics={"AFUE %": "efficiency_afue"},
    percent_metrics=frozenset({"AFUE %"}),
)
ES_COMMERCIAL_WATER_HEATERS = Source(
    label=ENERGY_STAR_LABEL,
    dataset="xmq6-bm79",
    title="Commercial Water Heaters",
    model_field="model_number",
    metrics={
        "Thermal efficiency %": "thermal_efficiency_te",
        "Standby loss Btu/h": "standby_loss",
    },
    percent_metrics=frozenset({"Thermal efficiency %"}),
    scales={"Thermal efficiency %": 100.0},
)
ES_GAS_WATER_HEATERS = Source(
    label=ENERGY_STAR_LABEL,
    dataset="6sbi-yuk2",
    title="Gas Water Heaters",
    model_field="model_number",
    metrics={"UEF": "uniform_energy_factor_uef"},
)
ES_COMMERCIAL_REFRIGERATION = Source(
    label=ENERGY_STAR_LABEL,
    dataset="wati-2tfp",
    title="Commercial Refrigerators and Freezers",
    model_field="model_number",
    metrics={"kWh/day": "reported_daily_energy_consumption_kwh_day", "cu ft": "total_volume_cu_ft"},
)
ES_COMMERCIAL_DISHWASHERS = Source(
    label=ENERGY_STAR_LABEL,
    dataset="pk8q-dim8",
    title="Commercial Dishwashers",
    model_field="model_number",
    metrics={
        "machine type": "machine_type",
        "sanitizing": "sanitation_method",
        "gal/rack": "water_use_gallons_per_rack_gpr",
        "idle kW": "idle_energy_rate_for_low_temp_kw",
    },
)
ES_ICE_MACHINES = Source(
    label=ENERGY_STAR_LABEL,
    dataset="nak5-fsjf",
    title="Commercial Ice Machines",
    model_field="model_number",
    metrics={"kWh/100 lb": "energy_use_kwh_100_lbs_ice", "lb/day": "harvest_rate_lbs_ice_day"},
)
ES_COMMERCIAL_OVENS = Source(
    label=ENERGY_STAR_LABEL,
    dataset="c8av-ccf7",
    title="Commercial Ovens",
    model_field="model_number",
    metrics={
        "convection cooking efficiency %": "convection_mode_cooking_energy_efficiency",
        "fuel": "heat_source_fuel_type",
    },
)

# Product class -> sources to search, most authoritative first.
SOURCES_BY_PRODUCT_CLASS: dict[str, list[Source]] = {
    "packaged_unit_small": [CCMS_CENTRAL_AC, CCMS_FURNACES, ES_LIGHT_COMMERCIAL_HVAC],
    "packaged_unit_large": [CCMS_COMMERCIAL_PACKAGE, ES_LIGHT_COMMERCIAL_HVAC],
    "split_condenser": [CCMS_CENTRAL_AC, ES_LIGHT_COMMERCIAL_HVAC],
    "evaporator_coil": [CCMS_CENTRAL_AC_INDOOR],
    "gas_furnace": [CCMS_FURNACES, ES_FURNACES],
    "commercial_gas_water_heater": [CCMS_COMMERCIAL_GAS_STORAGE_WH, ES_COMMERCIAL_WATER_HEATERS],
    "tankless_water_heater": [ES_GAS_WATER_HEATERS],
    "commercial_refrigerator": [ES_COMMERCIAL_REFRIGERATION],
    "commercial_dishwasher": [ES_COMMERCIAL_DISHWASHERS],
    "ice_machine": [ES_ICE_MACHINES],
    "commercial_oven": [ES_COMMERCIAL_OVENS],
}

# Inventory equipment_type keywords -> product class, checked in order.
PRODUCT_CLASS_KEYWORDS: list[tuple[str, str]] = [
    ("evaporator coil", "evaporator_coil"),
    ("rooftop", "packaged_unit_small"),
    ("condensing unit", "split_condenser"),
    ("furnace", "gas_furnace"),
    ("tankless", "tankless_water_heater"),
    ("water heater", "commercial_gas_water_heater"),
    ("reach-in refrigerator", "commercial_refrigerator"),
    ("dishwasher", "commercial_dishwasher"),
    ("ice machine", "ice_machine"),
    ("oven", "commercial_oven"),
]

# Units at or above this cooling capacity are commercial package equipment.
COMMERCIAL_PACKAGE_MIN_BTU_H = 65_000

# Text that marks a model field as unread rather than a model number.
UNREAD_MODEL_MARKERS = ("not read", "unknown", "model not", "n/a")


@dataclass(frozen=True)
class SeriesFallback:
    """A series-level lookup for when the exact model was not read."""

    brand_keyword: str
    text_keyword: str  # must appear in the model or equipment_type text
    source: Source
    model_regex: str  # models in the series
    extra_filter: dict[str, str] = field(default_factory=dict)  # field -> required value


SERIES_FALLBACKS: list[SeriesFallback] = [
    SeriesFallback(
        brand_keyword="htp",
        text_keyword="phoenix",
        source=CCMS_COMMERCIAL_GAS_STORAGE_WH,
        model_regex=r"^PH\d{3}-\d{2,3}$",
    ),
    SeriesFallback(
        brand_keyword="true",
        text_keyword="3-door glass",
        source=ES_COMMERCIAL_REFRIGERATION,
        model_regex=r"^.+$",
        extra_filter={
            "product_type": "Vertical Transparent Door Refrigerator",
            "number_of_transparent_doors": "3",
        },
    ),
]

# ENERGY STAR brand field for series fallbacks.
ENERGY_STAR_BRAND_FIELD = "brand_name"
CCMS_BRAND_FIELD = "Brand_Name_s__s"
CCMS_PRODUCT_GROUP_FIELD = "Product_Group_s"
