from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .security import minimize_profile_for_feedback, hash_minimized_profile


DEFAULT_FEEDBACK_PATH = Path(__file__).resolve().parents[1] / "data" / "feedback.jsonl"


def record_feedback(profile_dict: Dict[str, Any], benefit_id: str, rating: int, helpful: bool, comment: str = "", path: Path = DEFAULT_FEEDBACK_PATH) -> None:
    minimized = minimize_profile_for_feedback(profile_dict)
    event = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profile_hash": hash_minimized_profile(minimized),
        "profile_segments": minimized,
        "benefit_id": benefit_id,
        "rating": int(rating),
        "helpful": bool(helpful),
        "comment": str(comment)[:500],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def load_feedback_adjustments(path: Path = DEFAULT_FEEDBACK_PATH) -> Dict[str, float]:
    if not path.exists():
        return {}
    totals: Dict[str, list[float]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            bid = event.get("benefit_id")
            rating = float(event.get("rating", 3))
            helpful = 1.0 if event.get("helpful") else -1.0
            value = ((rating - 3.0) / 10.0) + 0.04 * helpful
            totals.setdefault(bid, []).append(value)
    adjustments = {}
    for bid, values in totals.items():
        # Tiny feedback adjustments keep RL-like learning from overpowering official rules.
        avg = sum(values) / max(len(values), 1)
        adjustments[bid] = max(-0.08, min(0.08, avg))
    return adjustments
