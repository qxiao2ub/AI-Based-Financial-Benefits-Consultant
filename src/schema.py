from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS",
    "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC", "PR", "GU", "VI", "AS", "MP"
]

EMPLOYMENT_STATUSES = [
    "employed_full_time",
    "employed_part_time",
    "self_employed",
    "unemployed",
    "retired",
    "student",
    "unable_to_work",
]


@dataclass
class UserProfile:
    age: int
    state: str
    zip_code: str
    household_size: int
    dependents_under_18: int
    children_under_5: int
    annual_income: float
    employment_status: str
    recent_job_loss: bool
    has_recent_work_history: bool
    is_student: bool
    is_veteran_or_service_member: bool
    has_disability_or_chronic_illness: bool
    is_pregnant_or_postpartum: bool
    has_health_insurance: bool
    monthly_rent_or_mortgage: float
    monthly_utilities: float
    total_debt: float
    monthly_debt_payments: float
    credit_score: int
    urgent_food_need: bool
    urgent_housing_need: bool
    urgent_utility_need: bool

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["state"] = str(data["state"]).upper().strip()
        data["zip_code"] = str(data["zip_code"]).strip()[:10]
        return data

    @property
    def senior(self) -> bool:
        return self.age >= 60

    @property
    def earned_income(self) -> bool:
        return self.employment_status in {"employed_full_time", "employed_part_time", "self_employed"} and self.annual_income > 0

    @property
    def housing_cost_burden(self) -> float:
        annual_housing = 12 * (self.monthly_rent_or_mortgage + self.monthly_utilities)
        return annual_housing / max(self.annual_income, 1)

    @property
    def debt_payment_burden(self) -> float:
        return (12 * self.monthly_debt_payments) / max(self.annual_income, 1)


def profile_from_dict(data: Dict[str, Any]) -> UserProfile:
    return UserProfile(**data)
