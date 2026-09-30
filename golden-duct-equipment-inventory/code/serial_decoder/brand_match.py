"""Match free-text make strings (as written in the inventory) to rule brands."""

import re

from serial_decoder.constants import EQUIPMENT_TYPE_KEYWORDS, WILDCARD_EQUIPMENT_TAGS
from serial_decoder.rules import SerialRule


def normalize_name(text: str) -> str:
    """Lower-case, drop periods (A.O. -> ao), turn other punctuation into spaces."""
    text = text.lower().replace(".", "").replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def brand_position(make: str, rule: SerialRule) -> int | None:
    """Where the earliest of the rule's brand names appears in the make text.

    Earlier means more relevant: "ICP (..., Carrier family)" is ICP first.
    """
    haystack = f" {normalize_name(make)} "
    positions = [
        haystack.find(f" {normalize_name(name)} ")
        for name in rule.names
        if normalize_name(name)
    ]
    found = [p for p in positions if p >= 0]
    return min(found) if found else None


def equipment_tags(equipment_type: str) -> set[str]:
    text = equipment_type.lower()
    return {
        tag
        for tag, keywords in EQUIPMENT_TYPE_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    }


def type_matches(rule: SerialRule, tags: set[str]) -> bool | None:
    """True/False when both sides are known, None when either side is open."""
    rule_tags = set(rule.equipment_types)
    if not tags or not rule_tags or rule_tags & WILDCARD_EQUIPMENT_TAGS:
        return None
    return bool(rule_tags & tags)
