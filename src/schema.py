from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

UK_NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]

EMPLOYMENT_STATUSES = [
    "employed_full_time",
    "employed_part_time",
    "self_employed",
    "unemployed",
    "retired",
    "student",
    "unable_to_work",
    "unpaid_carer",
    "maternity_parental_leave",
]

EMPLOYMENT_LABELS = {
    "employed_full_time": "Employed full-time",
    "employed_part_time": "Employed part-time",
    "self_employed": "Self-employed",
    "unemployed": "Unemployed / looking for work",
    "retired": "Retired",
    "student": "Student",
    "unable_to_work": "Unable to work because of health/disability",
    "unpaid_carer": "Unpaid carer",
    "maternity_parental_leave": "Maternity / parental leave",
}

HOUSING_TENURES = [
    "private_renter",
    "social_renter",
    "homeowner_mortgage",
    "homeowner_outright",
    "living_with_family",
    "temporary_or_homeless",
    "care_home",
]

HOUSING_LABELS = {
    "private_renter": "Private renter",
    "social_renter": "Council / housing-association renter",
    "homeowner_mortgage": "Homeowner with mortgage",
    "homeowner_outright": "Homeowner without mortgage",
    "living_with_family": "Living with family / friends",
    "temporary_or_homeless": "Temporary accommodation / homeless",
    "care_home": "Care home / residential care",
}

CREDIT_PROFILES = ["Not sure", "Excellent", "Good", "Fair", "Poor", "Very poor"]
PUBLIC_FUNDS_OPTIONS = ["Yes", "Not sure", "No / no recourse to public funds"]


@dataclass
class UserProfile:
    age: int
    nation: str
    postcode: str
    household_size: int
    partner_in_household: bool
    dependents_under_20: int
    children_under_16: int
    children_under_12: int
    children_under_5: int
    annual_household_income: float
    savings_and_investments: float
    employment_status: str
    hours_worked_per_week: float
    recent_job_loss: bool
    recent_ni_contributions: bool
    is_student: bool
    reached_state_pension_age: bool
    long_term_health_condition: bool
    daily_living_difficulty: bool
    mobility_difficulty: bool
    health_limits_work: bool
    pregnant_or_new_parent: bool
    carer_hours_per_week: float
    cared_person_gets_qualifying_disability_benefit: bool
    receives_universal_credit: bool
    receives_pension_credit: bool
    receives_means_tested_benefit: bool
    housing_tenure: str
    monthly_rent_or_mortgage: float
    monthly_council_tax_or_rates: float
    monthly_energy_cost: float
    monthly_childcare_cost: float
    total_debt: float
    monthly_debt_payments: float
    credit_profile: str
    public_funds_access: str
    urgent_food_need: bool
    urgent_housing_need: bool
    urgent_energy_need: bool
    urgent_debt_need: bool

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["nation"] = str(data["nation"]).strip()
        data["postcode"] = str(data["postcode"]).upper().strip()[:10]
        return data

    @property
    def earned_income(self) -> bool:
        return self.employment_status in {"employed_full_time", "employed_part_time", "self_employed"} and self.annual_household_income > 0

    @property
    def under_state_pension_age(self) -> bool:
        return not self.reached_state_pension_age

    @property
    def housing_cost_burden(self) -> float:
        annual = 12 * (self.monthly_rent_or_mortgage + self.monthly_council_tax_or_rates + self.monthly_energy_cost)
        return annual / max(self.annual_household_income, 1)

    @property
    def debt_payment_burden(self) -> float:
        return 12 * self.monthly_debt_payments / max(self.annual_household_income, 1)

    @property
    def has_children(self) -> bool:
        return self.children_under_16 > 0 or self.dependents_under_20 > 0

    @property
    def has_disability_need(self) -> bool:
        return self.long_term_health_condition and (self.daily_living_difficulty or self.mobility_difficulty)

    @property
    def public_funds_blocked(self) -> bool:
        return self.public_funds_access.startswith("No")


def profile_from_dict(data: Dict[str, Any]) -> UserProfile:
    return UserProfile(**data)
