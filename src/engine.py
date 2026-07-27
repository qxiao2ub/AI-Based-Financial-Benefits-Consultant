from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Any

from .advisor import generate_advisor_message, checklist_for_benefit, documents_for_benefit
from .catalog import load_catalog
from .feedback import load_feedback_adjustments
from .models import train_models, profile_to_features, predict_probabilities
from .rules import score_benefit, DEMO_FPL_NOTE, income_ratio_to_demo_fpl
from .schema import UserProfile


@lru_cache(maxsize=1)
def get_runtime_objects():
    catalog = load_catalog()
    trained = train_models(catalog)
    return catalog, trained


def evaluate_profile(profile: UserProfile, top_n: int = 8) -> List[Dict[str, Any]]:
    catalog, trained = get_runtime_objects()
    X = profile_to_features(profile)
    supervised_probs = predict_probabilities(trained.supervised_model, X, trained.benefit_ids)
    neural_probs = predict_probabilities(trained.neural_model, X, trained.benefit_ids)
    feedback_adjustments = load_feedback_adjustments()

    results: List[Dict[str, Any]] = []
    for benefit in catalog:
        bid = benefit["id"]
        rule_score, reasons = score_benefit(profile, benefit)
        ml_probability = supervised_probs.get(bid, 0.0)
        neural_probability = neural_probs.get(bid, 0.0)
        feedback_boost = feedback_adjustments.get(bid, 0.0)
        final_score = max(0.02, min(0.98, 0.45 * rule_score + 0.35 * ml_probability + 0.15 * neural_probability + feedback_boost))
        result = {
            "benefit": benefit,
            "rule_score": rule_score,
            "ml_probability": ml_probability,
            "neural_probability": neural_probability,
            "feedback_boost": feedback_boost,
            "final_score": final_score,
            "reasons": reasons,
            "checklist": checklist_for_benefit(benefit),
            "documents": documents_for_benefit(benefit),
            "demo_fpl_ratio": income_ratio_to_demo_fpl(profile),
            "important_model_note": DEMO_FPL_NOTE,
        }
        result["advisor_message"] = generate_advisor_message(result)
        results.append(result)

    results.sort(key=lambda item: item["final_score"], reverse=True)
    return results[:top_n]


def results_to_table(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "Rank": idx + 1,
            "Benefit": r["benefit"]["name"],
            "Estimated match %": round(100 * r["final_score"], 1),
            "Rule score %": round(100 * r["rule_score"], 1),
            "ML probability %": round(100 * r["ml_probability"], 1),
            "Neural score %": round(100 * r["neural_probability"], 1),
            "Source": r["benefit"]["source_url"],
        }
        for idx, r in enumerate(results)
    ]
