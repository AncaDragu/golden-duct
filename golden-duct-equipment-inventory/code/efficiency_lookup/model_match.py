"""Match an inventory model number against certification-listing model patterns.

Listings use '*' for any single character (a trailing '*' also allows any
suffix) and '(6,9)' for "one of these characters".
"""

import re
from dataclasses import dataclass

from efficiency_lookup.constants import UNREAD_MODEL_MARKERS

ANY_CHAR = None  # token meaning "any single character"
MIN_PARTIAL_MODEL_LENGTH = 6
MIN_NEAR_MODEL_LENGTH = 8

QUALITY_SCORES = {"exact": 4, "listing prefix": 3, "partial model": 2, "near": 1, "series": 0}


@dataclass(frozen=True)
class MatchQuality:
    level: str  # a key of QUALITY_SCORES
    detail: str

    @property
    def score(self) -> int:
        return QUALITY_SCORES[self.level]


@dataclass(frozen=True)
class ListingPattern:
    tokens: tuple[frozenset[str] | None, ...]
    open_ended: bool


def clean_model(raw: str) -> str | None:
    """First model-like token, or None when the field says the model was not read."""
    text = raw.split("(")[0].strip()
    if not text or any(marker in text.lower() for marker in UNREAD_MODEL_MARKERS):
        return None
    for token in re.split(r"[\s,;]+", text):
        token = token.strip(".")
        looks_like_model = any(c.isdigit() for c in token) or (token.isupper() and len(token) >= 2)
        if looks_like_model and re.fullmatch(r"[A-Za-z0-9\-/]+", token):
            return token.upper()
    return None


def parse_listing(listing: str) -> ListingPattern:
    text = listing.strip().upper()
    open_ended = text.endswith("*")
    tokens: list[frozenset[str] | None] = []
    for alternatives, char in re.findall(r"\(([A-Z0-9,]+)\)|(.)", text):
        if alternatives:
            tokens.append(frozenset(alternatives.split(",")))
        elif char == "*":
            tokens.append(ANY_CHAR)
        else:
            tokens.append(frozenset(char))
    while open_ended and tokens and tokens[-1] is ANY_CHAR:
        tokens.pop()
    return ListingPattern(tuple(tokens), open_ended)


def _mismatch_positions(model: str, tokens: tuple[frozenset[str] | None, ...]) -> list[int]:
    return [
        i
        for i, (char, token) in enumerate(zip(model, tokens))
        if token is not ANY_CHAR and char not in token
    ]


def match_quality(model: str, listing: str) -> MatchQuality | None:
    pattern = parse_listing(listing)
    tokens = pattern.tokens
    mismatches = _mismatch_positions(model, tokens)
    if not mismatches:
        if len(model) == len(tokens) or (len(model) > len(tokens) and pattern.open_ended):
            return MatchQuality("exact", f"model matches listing {listing}")
        if len(model) > len(tokens):
            return MatchQuality("listing prefix", f"listing {listing} covers the first {len(tokens)} characters")
        if len(model) >= MIN_PARTIAL_MODEL_LENGTH:
            return MatchQuality("partial model", f"model read is shorter than listing {listing}; leading characters agree")
        return None
    if len(mismatches) == 1 and len(model) >= MIN_NEAR_MODEL_LENGTH and abs(len(model) - len(tokens)) <= 1:
        i = mismatches[0]
        return MatchQuality(
            "near", f"1 character differs from listing {listing}: position {i + 1} reads '{model[i]}'"
        )
    return None
