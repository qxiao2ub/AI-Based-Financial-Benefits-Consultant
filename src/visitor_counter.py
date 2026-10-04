from __future__ import annotations

from pathlib import Path
from typing import Tuple

import requests

COUNTER_BASE = "https://countapi.mileshilliard.com/api/v1"
DEFAULT_COUNTER_KEY = "sissie-ma-uk-ai-financial-benefits-consultant-v1"
LOCAL_COUNTER_FILE = Path(__file__).resolve().parents[1] / "data" / "visitor_counter.txt"


def _local_increment() -> int:
    """Fallback only. It survives reruns in the current instance, but Streamlit Cloud may replace local disk on redeploy."""
    try:
        current = int(LOCAL_COUNTER_FILE.read_text(encoding="utf-8").strip()) if LOCAL_COUNTER_FILE.exists() else 0
    except Exception:
        current = 0
    current = max(0, current) + 1
    LOCAL_COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        LOCAL_COUNTER_FILE.write_text(str(current), encoding="utf-8")
    except Exception:
        pass
    return max(1, current)


def increment_visitor(counter_key: str = DEFAULT_COUNTER_KEY, timeout: float = 3.5) -> Tuple[int, str]:
    """Increment a hosted key-value counter once per Streamlit session.

    The app itself uses no database. A hosted counter service holds the cumulative total so
    Streamlit redeploys do not intentionally reset the displayed count to zero.
    """
    key = "".join(c for c in counter_key if c.isalnum() or c in "-_.")[:120] or DEFAULT_COUNTER_KEY
    try:
        response = requests.get(f"{COUNTER_BASE}/hit/{key}", timeout=timeout)
        response.raise_for_status()
        value = int(response.json().get("value", 0))
        if value > 0:
            return value, "persistent counter API"
    except Exception:
        pass
    return _local_increment(), "local fallback"
