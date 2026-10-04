from __future__ import annotations

import hashlib
import re
from typing import Any, Dict

POSTCODE_CLEAN_RE = re.compile(r"[^0-9A-Za-z ]")


def sanitize_postcode(postcode: str) -> str:
    return POSTCODE_CLEAN_RE.sub("", str(postcode)).upper().strip()[:10]


def minimize_profile_for_feedback(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Retain coarse segments only. No postcode, name, NI number or account details."""
    return {
        "nation": str(profile_dict.get("nation", ""))[:24],
        "age_band": int(profile_dict.get("age", 0)) // 10 * 10,
        "household_size": min(int(profile_dict.get("household_size", 0)), 8),
        "income_band": int(float(profile_dict.get("annual_household_income", 0)) // 5000 * 5000),
        "employment_status": profile_dict.get("employment_status", "unknown"),
    }


def hash_minimized_profile(minimized_profile: Dict[str, Any], salt: str = "uk-benefits-mvp-local-salt") -> str:
    payload = "|".join(f"{k}={minimized_profile[k]}" for k in sorted(minimized_profile))
    return hashlib.sha256((salt + payload).encode("utf-8")).hexdigest()[:16]
