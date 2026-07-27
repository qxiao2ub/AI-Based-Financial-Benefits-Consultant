from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any


@lru_cache(maxsize=1)
def load_catalog(path: str | None = None) -> List[Dict[str, Any]]:
    catalog_path = Path(path) if path else Path(__file__).resolve().parents[1] / "data" / "benefits_catalog.json"
    with catalog_path.open("r", encoding="utf-8") as f:
        catalog = json.load(f)
    if not isinstance(catalog, list):
        raise ValueError("Benefit catalog must be a list of benefit dictionaries.")
    return catalog


def catalog_by_id(catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {item["id"]: item for item in catalog}
