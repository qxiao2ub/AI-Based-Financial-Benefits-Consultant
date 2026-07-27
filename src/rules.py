from __future__ import annotations

from typing import Dict, Any, Tuple, List

from .schema import UserProfile


DEMO_FPL_NOTE = (
    "This MVP uses a simplified poverty-guideline estimate for ranking only. "
    "Production must use current official federal poverty guidelines and state-specific program rules."
)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def estimated_fpl_for_demo(profile: UserProfile) -> float:
    # A deliberately isolated placeholder so production teams can replace it with official ASPE/HHS data.
    # It is close enough for a software demo, but not an official eligibility threshold.
    base = 15650.0
    add_per_person = 5500.0
    fpl = base + max(profile.household_size - 1, 0) * add_per_person
    if profile.state == "AK":
        fpl *= 1.25
    elif profile.state == "HI":
        fpl *= 1.15
    return fpl


def income_ratio_to_demo_fpl(profile: UserProfile) -> float:
    return profile.annual_income / max(estimated_fpl_for_demo(profile), 1.0)


def score_benefit(profile: UserProfile, benefit: Dict[str, Any]) -> Tuple[float, List[str]]:
    bid = benefit["id"]
    ratio = income_ratio_to_demo_fpl(profile)
    housing_burden = profile.housing_cost_burden
    debt_burden = profile.debt_payment_burden
    reasons: List[str] = []
    score = 0.05

    if bid == "snap":
        if ratio <= 1.30:
            score += 0.55; reasons.append("Household income appears near a common SNAP screening range.")
        elif ratio <= 1.80:
            score += 0.25; reasons.append("Income is moderately close to common SNAP screening ranges.")
        if profile.dependents_under_18 > 0 or profile.senior or profile.has_disability_or_chronic_illness:
            score += 0.12; reasons.append("Household composition may trigger additional SNAP considerations.")
        if housing_burden > 0.35:
            score += 0.10; reasons.append("Housing and utility burden may matter for food-assistance budgeting.")
        if profile.urgent_food_need:
            score += 0.12; reasons.append("Urgent food need suggests local emergency food referrals should be prioritized.")

    elif bid == "medicaid_chip":
        if ratio <= 1.38:
            score += 0.45; reasons.append("Income is near a common Medicaid expansion screening range.")
        elif ratio <= 2.20 and profile.dependents_under_18 > 0:
            score += 0.28; reasons.append("Children in the household may qualify under CHIP or child Medicaid rules.")
        if not profile.has_health_insurance:
            score += 0.18; reasons.append("No current health insurance increases the value of checking Medicaid/CHIP.")
        if profile.has_disability_or_chronic_illness or profile.is_pregnant_or_postpartum:
            score += 0.15; reasons.append("Disability, illness, pregnancy, or postpartum status can affect health-benefit pathways.")

    elif bid == "housing_voucher":
        if ratio <= 0.80:
            score += 0.42; reasons.append("Income appears low relative to household size.")
        elif ratio <= 1.20:
            score += 0.18; reasons.append("Income may be near some local housing-assistance screening ranges.")
        if housing_burden > 0.40:
            score += 0.25; reasons.append("High rent/utility burden is a strong housing-stability signal.")
        if profile.urgent_housing_need:
            score += 0.18; reasons.append("Urgent housing need suggests applying and contacting local crisis resources.")
        if profile.senior or profile.has_disability_or_chronic_illness or profile.dependents_under_18 > 0:
            score += 0.08; reasons.append("Some local housing programs prioritize seniors, disabled people, or families.")

    elif bid == "liheap":
        if ratio <= 1.50:
            score += 0.42; reasons.append("Income appears near common energy-assistance screening ranges.")
        elif ratio <= 2.00:
            score += 0.18; reasons.append("Income may still be worth checking for state energy-assistance rules.")
        if profile.monthly_utilities >= 150 or profile.housing_cost_burden > 0.35:
            score += 0.18; reasons.append("Utility cost burden appears meaningful.")
        if profile.urgent_utility_need:
            score += 0.22; reasons.append("Utility crisis or shutoff risk can trigger crisis-assistance pathways.")
        if profile.senior or profile.has_disability_or_chronic_illness or profile.children_under_5 > 0:
            score += 0.08; reasons.append("Vulnerable household members may affect prioritization in some programs.")

    elif bid == "wic":
        if profile.is_pregnant_or_postpartum or profile.children_under_5 > 0:
            score += 0.45; reasons.append("Pregnancy, postpartum status, infant, or child under 5 is a core WIC category.")
        if ratio <= 1.85:
            score += 0.32; reasons.append("Income appears near a common WIC screening range.")
        if profile.has_health_insurance is False:
            score += 0.05; reasons.append("Health and nutrition referrals may be useful alongside WIC screening.")

    elif bid == "tanf":
        if profile.dependents_under_18 > 0:
            score += 0.35; reasons.append("TANF generally focuses on families with children.")
        if ratio <= 1.00:
            score += 0.30; reasons.append("Income appears low relative to household size.")
        if profile.employment_status in {"unemployed", "employed_part_time", "unable_to_work"}:
            score += 0.15; reasons.append("Employment status may make cash assistance or work-support services worth checking.")
        if profile.urgent_housing_need or profile.urgent_food_need:
            score += 0.08; reasons.append("Urgent basic-needs pressure can make TANF screening relevant.")

    elif bid == "unemployment":
        if profile.employment_status == "unemployed" and profile.recent_job_loss:
            score += 0.50; reasons.append("Recent job loss is a central unemployment-insurance signal.")
        if profile.has_recent_work_history:
            score += 0.25; reasons.append("Recent work history is important for wage eligibility checks.")
        if profile.employment_status in {"employed_part_time", "self_employed"} and profile.recent_job_loss:
            score += 0.12; reasons.append("Reduced work or self-employment history may still be worth checking with the state agency.")

    elif bid == "student_aid":
        if profile.is_student or profile.employment_status == "student":
            score += 0.55; reasons.append("Student status is the primary Federal Student Aid signal.")
        if ratio <= 2.50:
            score += 0.18; reasons.append("Income can affect need-based aid calculations.")
        if profile.dependents_under_18 > 0 or profile.age >= 24:
            score += 0.08; reasons.append("Dependency status and household situation can affect aid calculations.")

    elif bid == "va_benefits":
        if profile.is_veteran_or_service_member:
            score += 0.75; reasons.append("Veteran or service-member status is the core VA benefits signal.")
        if profile.has_disability_or_chronic_illness and profile.is_veteran_or_service_member:
            score += 0.10; reasons.append("A service-connected or other disability may change VA benefit options.")

    elif bid == "eitc":
        if profile.earned_income:
            score += 0.36; reasons.append("Earned income is required for EITC screening.")
        if ratio <= 3.00:
            score += 0.20; reasons.append("Income appears within a broad range where EITC may be relevant.")
        if profile.dependents_under_18 > 0:
            score += 0.15; reasons.append("Qualifying children can significantly affect EITC eligibility and amount.")
        if profile.age >= 25:
            score += 0.05; reasons.append("Age may matter for workers without qualifying children.")

    elif bid == "child_care":
        if profile.children_under_5 > 0 or profile.dependents_under_18 > 0:
            score += 0.35; reasons.append("Children in the household make child-care assistance worth checking.")
        if profile.employment_status in {"employed_full_time", "employed_part_time", "self_employed", "student"} or profile.is_student:
            score += 0.25; reasons.append("Work, school, or training activity is often part of child-care subsidy screening.")
        if ratio <= 2.50:
            score += 0.18; reasons.append("Income appears near a range where child-care subsidies may be relevant.")

    elif bid == "nonprofit_credit_counseling":
        if debt_burden >= 0.20:
            score += 0.35; reasons.append("Monthly debt payments appear high relative to income.")
        if profile.total_debt >= 10000:
            score += 0.16; reasons.append("Total debt balance suggests a counseling review may be useful.")
        if 300 <= profile.credit_score < 640:
            score += 0.18; reasons.append("Credit score suggests credit-building or debt-management guidance may help.")
        if profile.annual_income <= 0 and profile.total_debt > 0:
            score += 0.10; reasons.append("Debt with little or no income may require urgent budgeting and counseling support.")

    elif bid == "local_211":
        score += 0.25; reasons.append("211 is broadly useful for local, fast-changing human-service referrals.")
        if profile.urgent_food_need or profile.urgent_housing_need or profile.urgent_utility_need:
            score += 0.40; reasons.append("Urgent basic-needs flags make local 211 referral especially important.")
        if ratio <= 2.00 or housing_burden > 0.35:
            score += 0.14; reasons.append("Financial pressure suggests local resource navigation may help.")

    if not reasons:
        reasons.append("The profile has limited direct signals for this program, but it may still be worth reviewing official rules.")

    return clamp(score), reasons
