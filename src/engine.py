from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

from .advisor import checklist_for_benefit, documents_for_benefit, generate_advisor_message
from .catalog import load_catalog
from .feedback import load_feedback_adjustments
from .models import predict_probabilities, profile_to_features, train_models
from .rules import MODEL_NOTE, income_pressure_ratio, score_benefit
from .schema import UserProfile


def source_url_for_nation(benefit: Dict[str, Any], nation: str) -> str:
    if nation == "Northern Ireland" and benefit.get("ni_source_url"):
        return benefit["ni_source_url"]
    if nation == "Scotland" and benefit.get("scotland_source_url"):
        return benefit["scotland_source_url"]
    return benefit["source_url"]


@lru_cache(maxsize=1)
def get_runtime_objects():
    catalog = load_catalog()
    trained = train_models(catalog)
    return catalog, trained


def evaluate_profile(profile: UserProfile, top_n: int = 12) -> List[Dict[str, Any]]:
    catalog, trained = get_runtime_objects()
    X = profile_to_features(profile)
    supervised = predict_probabilities(trained.supervised_model, X, trained.benefit_ids)
    neural = predict_probabilities(trained.neural_model, X, trained.benefit_ids)
    feedback = load_feedback_adjustments()
    results: List[Dict[str, Any]] = []

    for benefit in catalog:
        if profile.nation not in benefit.get("nations", []):
            continue
        bid = benefit["id"]
        rule_score, reasons = score_benefit(profile, benefit)
        rf = supervised.get(bid, 0.0)
        nn = neural.get(bid, 0.0)
        fb = feedback.get(bid, 0.0)
        final = max(0.02, min(0.98, 0.56*rule_score + 0.25*rf + 0.14*nn + fb))
        result = {
            "benefit": benefit,
            "rule_score": rule_score,
            "ml_probability": rf,
            "neural_probability": nn,
            "feedback_boost": fb,
            "final_score": final,
            "reasons": reasons,
            "checklist": checklist_for_benefit(benefit),
            "documents": documents_for_benefit(benefit),
            "screening_income_ratio": income_pressure_ratio(profile),
            "important_model_note": MODEL_NOTE,
            "source_url": source_url_for_nation(benefit, profile.nation),
        }
        result["advisor_message"] = generate_advisor_message(result)
        results.append(result)

    results.sort(key=lambda item: item["final_score"], reverse=True)
    return results[:top_n]


def results_to_table(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "Rank": i + 1,
            "Benefit / support": r["benefit"]["name"],
            "Screening match %": round(100*r["final_score"], 1),
            "Rule signal %": round(100*r["rule_score"], 1),
            "Supervised ML %": round(100*r["ml_probability"], 1),
            "Neural network %": round(100*r["neural_probability"], 1),
            "Official/source link": r["source_url"],
        }
        for i, r in enumerate(results)
    ]
