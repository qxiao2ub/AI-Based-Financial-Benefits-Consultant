from __future__ import annotations

from typing import Dict, Any, List


def generate_advisor_message(result: Dict[str, Any]) -> str:
    benefit = result["benefit"]
    pct = round(result["final_score"] * 100)
    reasons = result.get("reasons", [])[:3]
    reason_text = " ".join(reasons)
    return (
        f"Sissie AI estimates a {pct}% match for {benefit['name']}. "
        f"This is a screening score, not an official decision. {reason_text}"
    )


def checklist_for_benefit(benefit: Dict[str, Any]) -> List[str]:
    steps = list(benefit.get("next_steps", []))
    steps.append("Before submitting, verify the latest rules directly with the agency or program provider.")
    steps.append("Save confirmation numbers, screenshots, letters, deadlines, and contact names.")
    return steps


def documents_for_benefit(benefit: Dict[str, Any]) -> List[str]:
    return list(benefit.get("documents", []))
