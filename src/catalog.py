from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "benefits_catalog.json"


def load_catalog(path: Path = CATALOG_PATH) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
