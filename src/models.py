from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Dict, List

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
from .schema import CREDIT_PROFILES, EMPLOYMENT_STATUSES, HOUSING_TENURES, PUBLIC_FUNDS_OPTIONS, UK_NATIONS, UserProfile

NUMERIC_FEATURES = [
    "age", "household_size", "dependents_under_20", "children_under_16", "children_under_12", "children_under_5",
    "annual_household_income", "savings_and_investments", "hours_worked_per_week", "carer_hours_per_week",
    "monthly_rent_or_mortgage", "monthly_council_tax_or_rates", "monthly_energy_cost", "monthly_childcare_cost",
    "total_debt", "monthly_debt_payments", "housing_cost_burden", "debt_payment_burden",
]
CATEGORICAL_FEATURES = ["nation", "employment_status", "housing_tenure", "credit_profile", "public_funds_access"]
BOOLEAN_FEATURES = [
    "partner_in_household", "recent_job_loss", "recent_ni_contributions", "is_student", "reached_state_pension_age",
    "long_term_health_condition", "daily_living_difficulty", "mobility_difficulty", "health_limits_work",
    "pregnant_or_new_parent", "cared_person_gets_qualifying_disability_benefit", "receives_universal_credit",
    "receives_pension_credit", "receives_means_tested_benefit", "urgent_food_need", "urgent_housing_need",
    "urgent_energy_need", "urgent_debt_need", "earned_income",
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES


@dataclass
class TrainedModels:
    benefit_ids: List[str]
    supervised_model: Pipeline
    neural_model: Pipeline


def profile_to_features(profile: UserProfile) -> pd.DataFrame:
    data = profile.to_dict()
    data["earned_income"] = profile.earned_income
    data["housing_cost_burden"] = profile.housing_cost_burden
    data["debt_payment_burden"] = profile.debt_payment_burden
    return pd.DataFrame([{k: data[k] for k in ALL_FEATURES}])


def _row_to_profile(row: pd.Series) -> UserProfile:
    return UserProfile(
        age=int(row["age"]), nation=str(row["nation"]), postcode="SW1A 1AA",
        household_size=int(row["household_size"]), partner_in_household=bool(row["partner_in_household"]),
        dependents_under_20=int(row["dependents_under_20"]), children_under_16=int(row["children_under_16"]),
        children_under_12=int(row["children_under_12"]), children_under_5=int(row["children_under_5"]),
        annual_household_income=float(row["annual_household_income"]), savings_and_investments=float(row["savings_and_investments"]),
        employment_status=str(row["employment_status"]), hours_worked_per_week=float(row["hours_worked_per_week"]),
        recent_job_loss=bool(row["recent_job_loss"]), recent_ni_contributions=bool(row["recent_ni_contributions"]),
        is_student=bool(row["is_student"]), reached_state_pension_age=bool(row["reached_state_pension_age"]),
        long_term_health_condition=bool(row["long_term_health_condition"]), daily_living_difficulty=bool(row["daily_living_difficulty"]),
        mobility_difficulty=bool(row["mobility_difficulty"]), health_limits_work=bool(row["health_limits_work"]),
        pregnant_or_new_parent=bool(row["pregnant_or_new_parent"]), carer_hours_per_week=float(row["carer_hours_per_week"]),
        cared_person_gets_qualifying_disability_benefit=bool(row["cared_person_gets_qualifying_disability_benefit"]),
        receives_universal_credit=bool(row["receives_universal_credit"]), receives_pension_credit=bool(row["receives_pension_credit"]),
        receives_means_tested_benefit=bool(row["receives_means_tested_benefit"]), housing_tenure=str(row["housing_tenure"]),
        monthly_rent_or_mortgage=float(row["monthly_rent_or_mortgage"]), monthly_council_tax_or_rates=float(row["monthly_council_tax_or_rates"]),
        monthly_energy_cost=float(row["monthly_energy_cost"]), monthly_childcare_cost=float(row["monthly_childcare_cost"]),
        total_debt=float(row["total_debt"]), monthly_debt_payments=float(row["monthly_debt_payments"]),
        credit_profile=str(row["credit_profile"]), public_funds_access=str(row["public_funds_access"]),
        urgent_food_need=bool(row["urgent_food_need"]), urgent_housing_need=bool(row["urgent_housing_need"]),
        urgent_energy_need=bool(row["urgent_energy_need"]), urgent_debt_need=bool(row["urgent_debt_need"]),
    )


def generate_synthetic_profiles(n: int = 650, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    age = rng.integers(18, 91, size=n)
    household_size = rng.integers(1, 7, size=n)
    children_under_16 = np.minimum(rng.poisson(0.9, size=n), np.maximum(household_size - 1, 0))
    children_under_12 = np.minimum(children_under_16, rng.binomial(np.maximum(children_under_16, 1), 0.75))
    children_under_5 = np.minimum(children_under_12, rng.binomial(np.maximum(children_under_12, 1), 0.42))
    dependents_under_20 = np.minimum(np.maximum(children_under_16, rng.poisson(1.0, size=n)), np.maximum(household_size - 1, 0))
    employment = rng.choice(EMPLOYMENT_STATUSES, size=n, p=[0.30,0.16,0.10,0.12,0.11,0.07,0.05,0.05,0.04])
    base_income = rng.lognormal(mean=10.15, sigma=0.70, size=n)
    multipliers = np.ones(n)
    multipliers[employment == "unemployed"] = rng.uniform(0.08, 0.45, size=(employment == "unemployed").sum())
    multipliers[employment == "retired"] = rng.uniform(0.30, 0.75, size=(employment == "retired").sum())
    multipliers[employment == "student"] = rng.uniform(0.05, 0.45, size=(employment == "student").sum())
    multipliers[employment == "unable_to_work"] = rng.uniform(0.05, 0.45, size=(employment == "unable_to_work").sum())
    annual_income = np.clip(base_income * multipliers + rng.normal(0, 2200, n), 0, 180000).round(0)
    reached_pension = (age >= 67) | ((age >= 65) & rng.choice([True, False], size=n, p=[0.42,0.58]))
    long_term = rng.choice([True, False], size=n, p=[0.23, 0.77])
    daily = long_term & rng.choice([True, False], size=n, p=[0.58,0.42])
    mobility = long_term & rng.choice([True, False], size=n, p=[0.43,0.57])
    health_limits = long_term & rng.choice([True, False], size=n, p=[0.48,0.52])
    partner = (household_size >= 2) & rng.choice([True, False], size=n, p=[0.64,0.36])
    housing = rng.choice(HOUSING_TENURES, size=n, p=[0.33,0.18,0.25,0.10,0.08,0.04,0.02])
    rent = np.clip(rng.normal(880 + 120*household_size, 480, size=n), 0, 3600).round(0)
    rent[np.isin(housing, ["homeowner_outright","living_with_family","care_home"])] *= 0.15
    savings = np.clip(rng.lognormal(mean=8.4, sigma=1.25, size=n)-2500, 0, 150000).round(0)
    total_debt = np.clip(rng.lognormal(mean=8.9, sigma=1.05, size=n)-3500, 0, 160000).round(0)
    debt_pay = np.clip(total_debt * rng.uniform(0.006,0.03,size=n),0,3500).round(0)
    hours = np.zeros(n)
    hours[employment == "employed_full_time"] = rng.uniform(30,48,size=(employment == "employed_full_time").sum())
    hours[employment == "employed_part_time"] = rng.uniform(5,29,size=(employment == "employed_part_time").sum())
    hours[employment == "self_employed"] = rng.uniform(5,55,size=(employment == "self_employed").sum())
    hours[employment == "maternity_parental_leave"] = rng.uniform(0,20,size=(employment == "maternity_parental_leave").sum())
    carer_hours = np.where(employment == "unpaid_carer", rng.uniform(35,70,size=n), rng.choice([0,10,20,35,45], size=n, p=[0.76,0.08,0.06,0.06,0.04]))
    receives_uc = (annual_income < (18000 + 4000*household_size)) & (savings <= 16000) & rng.choice([True,False],size=n,p=[0.54,0.46])
    receives_pc = reached_pension & (annual_income < 23000) & rng.choice([True,False],size=n,p=[0.48,0.52])
    means = receives_uc | receives_pc | ((annual_income < 24000) & rng.choice([True,False],size=n,p=[0.22,0.78]))
    pregnant = (age < 48) & rng.choice([True,False],size=n,p=[0.07,0.93])
    recent_job_loss = (employment == "unemployed") & rng.choice([True,False],size=n,p=[0.70,0.30])
    ni = rng.choice([True,False],size=n,p=[0.72,0.28])
    ni[age < 21] = rng.choice([True,False],size=(age < 21).sum(),p=[0.28,0.72])
    df = pd.DataFrame({
        "age": age, "nation": rng.choice(UK_NATIONS,size=n,p=[0.70,0.10,0.10,0.10]), "household_size": household_size,
        "dependents_under_20": dependents_under_20, "children_under_16": children_under_16, "children_under_12": children_under_12,
        "children_under_5": children_under_5, "annual_household_income": annual_income, "savings_and_investments": savings,
        "employment_status": employment, "hours_worked_per_week": hours.round(1), "recent_job_loss": recent_job_loss,
        "recent_ni_contributions": ni, "is_student": (employment == "student"), "reached_state_pension_age": reached_pension,
        "long_term_health_condition": long_term, "daily_living_difficulty": daily, "mobility_difficulty": mobility,
        "health_limits_work": health_limits, "pregnant_or_new_parent": pregnant, "carer_hours_per_week": carer_hours.round(1),
        "cared_person_gets_qualifying_disability_benefit": (carer_hours >= 35) & rng.choice([True,False],size=n,p=[0.72,0.28]),
        "receives_universal_credit": receives_uc, "receives_pension_credit": receives_pc, "receives_means_tested_benefit": means,
        "housing_tenure": housing, "monthly_rent_or_mortgage": rent, "monthly_council_tax_or_rates": np.clip(rng.normal(165,70,size=n),0,500).round(0),
        "monthly_energy_cost": np.clip(rng.normal(145,60,size=n),0,600).round(0), "monthly_childcare_cost": np.where(children_under_12>0,np.clip(rng.normal(420,390,size=n),0,2200),0).round(0),
        "total_debt": total_debt, "monthly_debt_payments": debt_pay, "credit_profile": rng.choice(CREDIT_PROFILES,size=n,p=[0.13,0.10,0.20,0.25,0.20,0.12]),
        "public_funds_access": rng.choice(PUBLIC_FUNDS_OPTIONS,size=n,p=[0.80,0.15,0.05]), "urgent_food_need": rng.choice([True,False],size=n,p=[0.12,0.88]),
        "urgent_housing_need": rng.choice([True,False],size=n,p=[0.10,0.90]), "urgent_energy_need": rng.choice([True,False],size=n,p=[0.13,0.87]),
        "urgent_debt_need": rng.choice([True,False],size=n,p=[0.15,0.85]), "partner_in_household": partner,
    })
    df["earned_income"] = df["employment_status"].isin(["employed_full_time","employed_part_time","self_employed"]) & (df["annual_household_income"] > 0)
    df["housing_cost_burden"] = 12*(df["monthly_rent_or_mortgage"]+df["monthly_council_tax_or_rates"]+df["monthly_energy_cost"])/np.maximum(df["annual_household_income"],1)
    df["debt_payment_burden"] = 12*df["monthly_debt_payments"]/np.maximum(df["annual_household_income"],1)
    return df[ALL_FEATURES]


def make_training_labels(X: pd.DataFrame, catalog: List[Dict[str, Any]], random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    labels = {b["id"]: [] for b in catalog}
    for _, row in X.iterrows():
        profile = _row_to_profile(row)
        for benefit in catalog:
            rule_score, _ = score_benefit(profile, benefit)
            noisy = rule_score + rng.normal(0, 0.055)
            labels[benefit["id"]].append(int(noisy >= 0.48))
    return pd.DataFrame(labels)


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ("bool", "passthrough", BOOLEAN_FEATURES),
    ])


def train_models(catalog: List[Dict[str, Any]], n: int = 650, random_state: int = 42) -> TrainedModels:
    X = generate_synthetic_profiles(n=n, random_state=random_state)
    Y = make_training_labels(X, catalog, random_state=random_state)
    benefit_ids = [b["id"] for b in catalog]

    supervised = Pipeline([
        ("preprocess", _preprocessor()),
        ("model", MultiOutputClassifier(RandomForestClassifier(
            n_estimators=60, max_depth=8, min_samples_leaf=4, random_state=random_state, class_weight="balanced_subsample", n_jobs=-1
        ))),
    ])
    supervised.fit(X, Y[benefit_ids])

    neural = Pipeline([
        ("preprocess", _preprocessor()),
        ("model", MultiOutputClassifier(MLPClassifier(
            hidden_layer_sizes=(48,24), activation="relu", alpha=0.002, learning_rate_init=0.0025,
            max_iter=110, early_stopping=True, random_state=random_state,
        ))),
    ])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        neural.fit(X, Y[benefit_ids])
    return TrainedModels(benefit_ids, supervised, neural)


def predict_probabilities(model: Pipeline, X: pd.DataFrame, benefit_ids: List[str]) -> Dict[str, float]:
    proba_list = model.predict_proba(X)
    estimators = model.named_steps["model"].estimators_
    output: Dict[str, float] = {}
    for bid, arr, estimator in zip(benefit_ids, proba_list, estimators):
        classes = list(estimator.classes_)
        output[bid] = float(arr[0, classes.index(1)]) if 1 in classes else 0.0
    return output
