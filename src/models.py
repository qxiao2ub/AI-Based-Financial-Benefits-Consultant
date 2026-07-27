from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .rules import score_benefit
from .schema import UserProfile, US_STATES, EMPLOYMENT_STATUSES


NUMERIC_FEATURES = [
    "age", "household_size", "dependents_under_18", "children_under_5", "annual_income",
    "monthly_rent_or_mortgage", "monthly_utilities", "total_debt", "monthly_debt_payments", "credit_score",
    "housing_cost_burden", "debt_payment_burden"
]
CATEGORICAL_FEATURES = ["state", "employment_status"]
BOOLEAN_FEATURES = [
    "recent_job_loss", "has_recent_work_history", "is_student", "is_veteran_or_service_member",
    "has_disability_or_chronic_illness", "is_pregnant_or_postpartum", "has_health_insurance",
    "urgent_food_need", "urgent_housing_need", "urgent_utility_need", "senior", "earned_income"
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES


@dataclass
class TrainedModels:
    benefit_ids: List[str]
    supervised_model: Pipeline
    neural_model: Pipeline


def profile_to_features(profile: UserProfile) -> pd.DataFrame:
    data = profile.to_dict()
    data["senior"] = profile.senior
    data["earned_income"] = profile.earned_income
    data["housing_cost_burden"] = profile.housing_cost_burden
    data["debt_payment_burden"] = profile.debt_payment_burden
    return pd.DataFrame([{k: data[k] for k in ALL_FEATURES}])


def _row_to_profile(row: pd.Series) -> UserProfile:
    return UserProfile(
        age=int(row["age"]),
        state=str(row["state"]),
        zip_code="00000",
        household_size=int(row["household_size"]),
        dependents_under_18=int(row["dependents_under_18"]),
        children_under_5=int(row["children_under_5"]),
        annual_income=float(row["annual_income"]),
        employment_status=str(row["employment_status"]),
        recent_job_loss=bool(row["recent_job_loss"]),
        has_recent_work_history=bool(row["has_recent_work_history"]),
        is_student=bool(row["is_student"]),
        is_veteran_or_service_member=bool(row["is_veteran_or_service_member"]),
        has_disability_or_chronic_illness=bool(row["has_disability_or_chronic_illness"]),
        is_pregnant_or_postpartum=bool(row["is_pregnant_or_postpartum"]),
        has_health_insurance=bool(row["has_health_insurance"]),
        monthly_rent_or_mortgage=float(row["monthly_rent_or_mortgage"]),
        monthly_utilities=float(row["monthly_utilities"]),
        total_debt=float(row["total_debt"]),
        monthly_debt_payments=float(row["monthly_debt_payments"]),
        credit_score=int(row["credit_score"]),
        urgent_food_need=bool(row["urgent_food_need"]),
        urgent_housing_need=bool(row["urgent_housing_need"]),
        urgent_utility_need=bool(row["urgent_utility_need"]),
    )


def generate_synthetic_profiles(n: int = 900, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    household_size = rng.integers(1, 7, size=n)
    age = rng.integers(18, 82, size=n)
    employment_status = rng.choice(EMPLOYMENT_STATUSES, size=n, p=[0.37, 0.15, 0.09, 0.14, 0.11, 0.08, 0.06])
    base_income = rng.lognormal(mean=10.35, sigma=0.75, size=n)
    income_multiplier = np.ones(n)
    income_multiplier[employment_status == "unemployed"] = rng.uniform(0.05, 0.55, size=(employment_status == "unemployed").sum())
    income_multiplier[employment_status == "retired"] = rng.uniform(0.25, 0.9, size=(employment_status == "retired").sum())
    income_multiplier[employment_status == "student"] = rng.uniform(0.05, 0.65, size=(employment_status == "student").sum())
    income_multiplier[employment_status == "unable_to_work"] = rng.uniform(0.05, 0.6, size=(employment_status == "unable_to_work").sum())
    annual_income = np.clip(base_income * income_multiplier + rng.normal(0, 3000, n), 0, 220000).round(0)

    dependents_under_18 = np.minimum(rng.poisson(1.0, size=n), np.maximum(household_size - 1, 0))
    children_under_5 = np.minimum(dependents_under_18, rng.binomial(np.maximum(dependents_under_18, 1), 0.35))
    monthly_rent = np.clip(rng.normal(1150 + 110 * household_size, 520, size=n), 0, 5000).round(0)
    monthly_utilities = np.clip(rng.normal(180 + 25 * household_size, 85, size=n), 0, 900).round(0)
    total_debt = np.clip(rng.lognormal(mean=9.2, sigma=1.0, size=n) - 4000, 0, 180000).round(0)
    monthly_debt_payments = np.clip(total_debt * rng.uniform(0.005, 0.03, size=n), 0, 4500).round(0)
    credit_score = np.clip(rng.normal(675 - (monthly_debt_payments / 80), 75, size=n), 300, 850).round(0).astype(int)
    recent_job_loss = (employment_status == "unemployed") & rng.choice([True, False], size=n, p=[0.65, 0.35])

    df = pd.DataFrame({
        "age": age,
        "state": rng.choice(US_STATES[:51], size=n),
        "household_size": household_size,
        "dependents_under_18": dependents_under_18,
        "children_under_5": children_under_5,
        "annual_income": annual_income,
        "employment_status": employment_status,
        "recent_job_loss": recent_job_loss,
        "has_recent_work_history": rng.choice([True, False], size=n, p=[0.72, 0.28]),
        "is_student": (employment_status == "student") | rng.choice([True, False], size=n, p=[0.08, 0.92]),
        "is_veteran_or_service_member": rng.choice([True, False], size=n, p=[0.08, 0.92]),
        "has_disability_or_chronic_illness": rng.choice([True, False], size=n, p=[0.16, 0.84]),
        "is_pregnant_or_postpartum": rng.choice([True, False], size=n, p=[0.05, 0.95]),
        "has_health_insurance": rng.choice([True, False], size=n, p=[0.76, 0.24]),
        "monthly_rent_or_mortgage": monthly_rent,
        "monthly_utilities": monthly_utilities,
        "total_debt": total_debt,
        "monthly_debt_payments": monthly_debt_payments,
        "credit_score": credit_score,
        "urgent_food_need": rng.choice([True, False], size=n, p=[0.17, 0.83]),
        "urgent_housing_need": rng.choice([True, False], size=n, p=[0.13, 0.87]),
        "urgent_utility_need": rng.choice([True, False], size=n, p=[0.14, 0.86]),
    })
    df["senior"] = df["age"] >= 60
    df["earned_income"] = df["employment_status"].isin(["employed_full_time", "employed_part_time", "self_employed"]) & (df["annual_income"] > 0)
    df["housing_cost_burden"] = 12 * (df["monthly_rent_or_mortgage"] + df["monthly_utilities"]) / np.maximum(df["annual_income"], 1)
    df["debt_payment_burden"] = 12 * df["monthly_debt_payments"] / np.maximum(df["annual_income"], 1)
    return df[ALL_FEATURES]


def make_training_labels(X: pd.DataFrame, catalog: List[Dict[str, Any]], random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    labels = {benefit["id"]: [] for benefit in catalog}
    for _, row in X.iterrows():
        profile = _row_to_profile(row)
        for benefit in catalog:
            base_score, _ = score_benefit(profile, benefit)
            noisy_score = base_score + rng.normal(0, 0.07)
            labels[benefit["id"]].append(int(noisy_score >= 0.52))
    return pd.DataFrame(labels)


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("bool", "passthrough", BOOLEAN_FEATURES),
        ]
    )


def train_models(catalog: List[Dict[str, Any]], n: int = 900, random_state: int = 42) -> TrainedModels:
    X = generate_synthetic_profiles(n=n, random_state=random_state)
    Y = make_training_labels(X, catalog, random_state=random_state)
    benefit_ids = [b["id"] for b in catalog]

    supervised = Pipeline(steps=[
        ("preprocess", _preprocessor()),
        ("model", MultiOutputClassifier(RandomForestClassifier(
            n_estimators=90,
            max_depth=9,
            min_samples_leaf=4,
            random_state=random_state,
            class_weight="balanced_subsample",
        )))
    ])
    supervised.fit(X, Y[benefit_ids])

    neural = Pipeline(steps=[
        ("preprocess", _preprocessor()),
        ("model", MultiOutputClassifier(MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            alpha=0.001,
            learning_rate_init=0.002,
            max_iter=160,
            early_stopping=True,
            random_state=random_state,
        )))
    ])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        neural.fit(X, Y[benefit_ids])

    return TrainedModels(benefit_ids=benefit_ids, supervised_model=supervised, neural_model=neural)


def predict_probabilities(model: Pipeline, X: pd.DataFrame, benefit_ids: List[str]) -> Dict[str, float]:
    proba_list = model.predict_proba(X)
    estimators = model.named_steps["model"].estimators_
    output = {}
    for bid, arr, estimator in zip(benefit_ids, proba_list, estimators):
        classes = list(estimator.classes_)
        if 1 in classes:
            output[bid] = float(arr[0, classes.index(1)])
        else:
            output[bid] = 0.0
    return output
