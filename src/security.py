from __future__ import annotations

import hashlib
import re
from typing import Dict, Any


ZIP_RE = re.compile(r"[^0-9A-Za-z-]")


def sanitize_zip_code(zip_code: str) -> str:
    return ZIP_RE.sub("", str(zip_code))[:10]


def minimize_profile_for_feedback(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only coarse, non-identifying features for feedback analytics."""
    return {
        "state": str(profile_dict.get("state", "")).upper()[:2],
        "age_band": int(profile_dict.get("age", 0)) // 10 * 10,
        "household_size": min(int(profile_dict.get("household_size", 0)), 8),
        "income_band": int(float(profile_dict.get("annual_income", 0)) // 10000 * 10000),
        "employment_status": profile_dict.get("employment_status", "unknown"),
    }


def hash_minimized_profile(minimized_profile: Dict[str, Any], salt: str = "mvp-local-salt") -> str:
    payload = "|".join(f"{k}={minimized_profile[k]}" for k in sorted(minimized_profile))
    return hashlib.sha256((salt + payload).encode("utf-8")).hexdigest()[:16]
