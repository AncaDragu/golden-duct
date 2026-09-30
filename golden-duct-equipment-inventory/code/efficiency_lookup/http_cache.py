"""GET JSON with an on-disk cache so reruns cost no network calls."""

import hashlib
import json
from pathlib import Path

import requests

from efficiency_lookup.constants import CACHE_DIR, REQUEST_TIMEOUT_SECONDS, USER_AGENT

JsonValue = dict[str, object] | list[object]


def _cache_path(url: str, params: dict[str, str], cache_dir: Path) -> Path:
    key = json.dumps({"url": url, "params": sorted(params.items())})
    return cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()[:24]}.json"


def cached_get_json(url: str, params: dict[str, str], cache_dir: Path = CACHE_DIR) -> JsonValue:
    path = _cache_path(url, params, cache_dir)
    if path.exists():
        return json.loads(path.read_text())["response"]
    response = requests.get(
        url, params=params, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    payload = response.json()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"url": url, "params": params, "response": payload}))
    return payload
