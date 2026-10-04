from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .security import hash_minimized_profile, minimize_profile_for_feedback

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
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_feedback_adjustments(path: Path = DEFAULT_FEEDBACK_PATH) -> Dict[str, float]:
    if not path.exists():
        return {}
    totals: Dict[str, list[float]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
            except Exception:
                continue
            bid = event.get("benefit_id")
            if not bid:
                continue
            rating = float(event.get("rating", 3))
            helpful = 1.0 if event.get("helpful") else -1.0
            totals.setdefault(bid, []).append(((rating - 3.0) / 12.0) + 0.03 * helpful)
    return {bid: max(-0.06, min(0.06, sum(vals) / max(len(vals), 1))) for bid, vals in totals.items()}
