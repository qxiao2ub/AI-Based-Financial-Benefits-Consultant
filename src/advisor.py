from __future__ import annotations

from typing import Any, Dict, List


def generate_advisor_message(result: Dict[str, Any]) -> str:
    benefit = result["benefit"]
    pct = round(result["final_score"] * 100)
    reasons = result.get("reasons", [])[:3]
    reason_text = " ".join(reasons)
    return (
        f"Sissie AI gives {benefit['name']} a {pct}% screening match for this profile. "
        f"This percentage is a prioritisation score, not a government approval probability. {reason_text}"
    )


def checklist_for_benefit(benefit: Dict[str, Any]) -> List[str]:
    steps = list(benefit.get("next_steps", []))
    steps.append("Re-check the current rules on the official source before you submit anything.")
    steps.append("Keep copies of forms, evidence, confirmation numbers, decision letters and deadlines.")
    return steps


def documents_for_benefit(benefit: Dict[str, Any]) -> List[str]:
    return list(benefit.get("documents", []))
