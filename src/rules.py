from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .schema import UserProfile

MODEL_NOTE = (
    "Screening scores are prioritisation signals, not official entitlement or approval probabilities. "
    "The MVP combines simplified rules with models trained on synthetic examples; always verify current official rules."
)

MEANS_TESTED_OR_PUBLIC_FUND_SENSITIVE = {
    "universal_credit", "council_tax_reduction", "rate_rebate_ni", "child_benefit",
    "pension_credit", "healthy_start", "best_start_foods_scotland", "warm_home_discount",
    "cold_weather_or_winter_heating", "winter_fuel_payment", "support_for_mortgage_interest",
    "free_school_meals",
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def household_income_reference(profile: UserProfile) -> float:
    """Non-statutory income-pressure reference used only for ranking demo examples."""
    return 19000.0 + max(profile.household_size - 1, 0) * 5200.0


def income_pressure_ratio(profile: UserProfile) -> float:
    return profile.annual_household_income / max(household_income_reference(profile), 1.0)


def _basic_low_income_score(profile: UserProfile) -> float:
    ratio = income_pressure_ratio(profile)
    if ratio <= 0.70:
        return 0.72
    if ratio <= 1.00:
        return 0.60
    if ratio <= 1.35:
        return 0.40
    if ratio <= 1.75:
        return 0.22
    return 0.08


def _nation_mismatch(profile: UserProfile, benefit: Dict[str, Any]) -> bool:
    return profile.nation not in benefit.get("nations", [])


def score_benefit(profile: UserProfile, benefit: Dict[str, Any]) -> Tuple[float, List[str]]:
    bid = benefit["id"]
    reasons: List[str] = []

    if _nation_mismatch(profile, benefit):
        return 0.01, [f"This programme/resource is not configured for {profile.nation} in this MVP."]

    low = _basic_low_income_score(profile)
    housing_burden = profile.housing_cost_burden
    debt_burden = profile.debt_payment_burden
    score = 0.04

    if bid == "universal_credit":
        score += low
        if profile.under_state_pension_age:
            score += 0.10; reasons.append("You indicated you are below State Pension age.")
        else:
            score -= 0.25; reasons.append("Universal Credit is generally for people below State Pension age; Pension Credit may be more relevant.")
        if profile.savings_and_investments <= 16000:
            score += 0.08; reasons.append("Reported savings are at or below the £16,000 Universal Credit capital ceiling.")
        else:
            score = min(score, 0.12); reasons.append("Reported savings exceed the normal £16,000 Universal Credit capital ceiling.")
        if profile.employment_status in {"unemployed", "employed_part_time", "unable_to_work", "unpaid_carer"}:
            score += 0.08; reasons.append("Employment circumstances are commonly associated with Universal Credit checks.")
        if housing_burden > 0.40:
            score += 0.06; reasons.append("Housing and essential-bill costs appear high relative to income.")

    elif bid == "council_tax_reduction":
        score += low
        if profile.monthly_council_tax_or_rates > 0:
            score += 0.12; reasons.append("You reported a Council Tax cost.")
        if profile.receives_universal_credit or profile.receives_means_tested_benefit:
            score += 0.10; reasons.append("Receiving a means-tested benefit can make local Council Tax support worth checking.")
        reasons.append("Exact Council Tax Reduction rules are set locally by your council.")

    elif bid == "rate_rebate_ni":
        score += low
        if profile.monthly_council_tax_or_rates > 0:
            score += 0.14; reasons.append("You reported domestic rates or similar local housing charges.")
        if profile.receives_universal_credit or profile.receives_means_tested_benefit:
            score += 0.12; reasons.append("Current benefit status can affect Northern Ireland rate-support routes.")
        reasons.append("Northern Ireland uses rates rather than Council Tax.")

    elif bid == "child_benefit":
        if profile.has_children:
            score += 0.82; reasons.append("You reported a child/dependent in an age range commonly relevant to Child Benefit.")
        else:
            reasons.append("No qualifying-age child was recorded in this screening profile.")
        if profile.annual_household_income > 60000:
            reasons.append("Higher income can create a tax charge even when Child Benefit can still be claimed.")

    elif bid in {"pip", "adult_disability_payment_scotland"}:
        if profile.under_state_pension_age:
            score += 0.12
        else:
            score -= 0.20; reasons.append("New working-age disability claims are generally replaced by pension-age disability routes after State Pension age.")
        if profile.long_term_health_condition:
            score += 0.30; reasons.append("A long-term health condition/disability was reported.")
        if profile.daily_living_difficulty:
            score += 0.28; reasons.append("Daily-living difficulty is a core disability-benefit screening signal.")
        if profile.mobility_difficulty:
            score += 0.22; reasons.append("Mobility difficulty is a core disability-benefit screening signal.")
        if not profile.long_term_health_condition:
            score = min(score, 0.16)
        reasons.append("Income, savings and employment do not decide entitlement to this disability benefit.")

    elif bid in {"attendance_allowance", "pension_age_disability_payment_scotland"}:
        if profile.reached_state_pension_age:
            score += 0.36; reasons.append("You indicated that you have reached State Pension age.")
        else:
            score = min(score, 0.10); reasons.append("This route is primarily for people at or above State Pension age.")
        if profile.long_term_health_condition:
            score += 0.24; reasons.append("A health condition/disability was reported.")
        if profile.daily_living_difficulty or profile.mobility_difficulty:
            score += 0.26; reasons.append("You reported care, supervision, daily-living or mobility needs.")

    elif bid in {"carers_allowance", "carer_support_payment_scotland"}:
        if profile.carer_hours_per_week >= 35:
            score += 0.52; reasons.append("You reported at least 35 hours of unpaid care per week.")
        elif profile.carer_hours_per_week > 0:
            score += 0.14; reasons.append("You provide unpaid care, but reported fewer than the typical 35-hour threshold.")
        if profile.cared_person_gets_qualifying_disability_benefit:
            score += 0.28; reasons.append("The person you care for is reported to receive a qualifying disability benefit.")
        if profile.carer_hours_per_week == 0:
            score = min(score, 0.08)

    elif bid == "new_style_jsa":
        if profile.employment_status == "unemployed" or profile.recent_job_loss:
            score += 0.46; reasons.append("Unemployment/recent job loss is a central New Style JSA signal.")
        if profile.recent_ni_contributions:
            score += 0.30; reasons.append("You reported recent National Insurance contribution history.")
        if profile.hours_worked_per_week < 16:
            score += 0.08; reasons.append("Reported weekly working hours are below the usual 16-hour limit.")
        if profile.reached_state_pension_age:
            score = min(score, 0.08); reasons.append("New Style JSA is for people below State Pension age.")
        if profile.health_limits_work:
            score -= 0.18; reasons.append("If health prevents work, New Style ESA may be more appropriate than JSA.")

    elif bid == "new_style_esa":
        if profile.health_limits_work:
            score += 0.44; reasons.append("You reported a health condition that limits your ability to work.")
        if profile.long_term_health_condition:
            score += 0.14
        if profile.recent_ni_contributions:
            score += 0.28; reasons.append("You reported recent National Insurance contributions/credits.")
        if profile.reached_state_pension_age:
            score = min(score, 0.08); reasons.append("New Style ESA is generally for people below State Pension age.")

    elif bid == "pension_credit":
        if profile.reached_state_pension_age:
            score += 0.45; reasons.append("You indicated that you have reached State Pension age.")
            score += low * 0.65
            if profile.annual_household_income < 26000:
                score += 0.08; reasons.append("Reported household income makes a Pension Credit check worthwhile.")
        else:
            score = 0.06; reasons.append("Pension Credit normally requires reaching State Pension age.")
        if profile.savings_and_investments > 10000:
            reasons.append("Savings above £10,000 can create assumed income in the Pension Credit calculation rather than a simple automatic exclusion.")

    elif bid == "tax_free_childcare":
        if profile.children_under_12 > 0:
            score += 0.40; reasons.append("You reported at least one child under 12.")
        if profile.earned_income or profile.employment_status == "maternity_parental_leave":
            score += 0.28; reasons.append("Working/returning-to-work status is relevant to Tax-Free Childcare.")
        if profile.monthly_childcare_cost > 0:
            score += 0.16; reasons.append("You reported childcare costs.")
        if profile.annual_household_income > 180000:
            score -= 0.20; reasons.append("High household income may indicate one partner is above the £100,000 individual income limit; verify carefully.")

    elif bid in {"healthy_start", "best_start_foods_scotland"}:
        if profile.pregnant_or_new_parent or profile.children_under_5 > 0:
            score += 0.48; reasons.append("Pregnancy/new-parent status or a child under 5 was reported.")
        else:
            score = min(score, 0.08)
        if profile.receives_universal_credit or profile.receives_means_tested_benefit:
            score += 0.24; reasons.append("A qualifying means-tested benefit may create an eligibility route.")
        score += low * 0.20

    elif bid == "warm_home_discount":
        if profile.receives_universal_credit or profile.receives_pension_credit or profile.receives_means_tested_benefit:
            score += 0.48; reasons.append("You reported receipt of a benefit commonly linked to Warm Home Discount eligibility checks.")
        score += low * 0.30
        if profile.monthly_energy_cost >= 100 or profile.urgent_energy_need:
            score += 0.10; reasons.append("Energy costs or an urgent energy need make the scheme particularly relevant to review.")
        reasons.append("2026/27 eligibility differs between England/Wales and Scotland; Northern Ireland is outside this scheme.")

    elif bid == "cold_weather_or_winter_heating":
        if profile.receives_pension_credit or profile.receives_universal_credit or profile.receives_means_tested_benefit:
            score += 0.54; reasons.append("A qualifying means-tested benefit was reported.")
        if profile.children_under_5 > 0 or profile.health_limits_work or profile.has_disability_need:
            score += 0.14; reasons.append("Young children or disability/limited capability can matter for some winter-support routes.")
        if profile.nation == "Scotland":
            reasons.append("Scotland uses Winter Heating Payment rather than weather-triggered Cold Weather Payments.")

    elif bid == "winter_fuel_payment":
        if profile.age >= 66 or profile.reached_state_pension_age:
            score += 0.68; reasons.append("Age/State Pension information suggests pension-age winter support is worth checking.")
        else:
            score = 0.06; reasons.append("This support is aimed at people above the current qualifying birth-date/age threshold.")
        if profile.annual_household_income > 35000 and profile.nation in {"England", "Wales", "Northern Ireland"}:
            reasons.append("For winter 2026/27, HMRC may recover the Winter Fuel Payment when the recipient's own income exceeds the published £35,000 threshold.")
        if profile.nation == "Scotland":
            reasons.append("Scotland uses a separate pension-age winter-heating payment system.")

    elif bid == "nhs_low_income_scheme":
        score += low * 0.75
        if profile.savings_and_investments <= 16000:
            score += 0.12; reasons.append("Reported capital is within the common £16,000 NHS Low Income Scheme limit for most applicants.")
        else:
            score = min(score, 0.12); reasons.append("Reported savings exceed the common £16,000 capital limit for most applicants.")
        if profile.receives_universal_credit or profile.receives_pension_credit:
            reasons.append("You may already get full help with some health costs through a qualifying benefit, depending on the detailed rules.")

    elif bid == "support_for_mortgage_interest":
        if profile.housing_tenure == "homeowner_mortgage":
            score += 0.42; reasons.append("You reported owning your home with a mortgage.")
        else:
            score = min(score, 0.08); reasons.append("SMI is for qualifying mortgage/home-improvement loan interest, not rent.")
        if profile.receives_universal_credit or profile.receives_pension_credit or profile.receives_means_tested_benefit:
            score += 0.34; reasons.append("You reported a benefit that may be relevant to SMI eligibility.")
        reasons.append("SMI is a repayable loan with interest, not a grant.")

    elif bid == "maternity_allowance":
        if profile.pregnant_or_new_parent:
            score += 0.48; reasons.append("Pregnancy/new-parent status was reported.")
        else:
            score = min(score, 0.05)
        if profile.employment_status in {"self_employed", "unemployed", "employed_part_time", "maternity_parental_leave"} or profile.recent_job_loss:
            score += 0.24; reasons.append("Employment history may make Maternity Allowance worth checking if Statutory Maternity Pay is unavailable.")

    elif bid == "free_school_meals":
        if profile.children_under_16 > 0:
            score += 0.40; reasons.append("You reported school-age children/dependants.")
        else:
            score = min(score, 0.08)
        if profile.receives_universal_credit or profile.receives_means_tested_benefit:
            score += 0.30; reasons.append("Means-tested benefit receipt can be relevant to school-meal eligibility.")
        reasons.append("School-meal rules differ by UK nation, school year and local authority.")

    elif bid == "free_debt_advice":
        if profile.total_debt > 0:
            score += 0.20; reasons.append("You reported outstanding debt.")
        if debt_burden >= 0.20:
            score += 0.28; reasons.append("Monthly debt payments are high relative to reported household income.")
        elif debt_burden >= 0.10:
            score += 0.16
        if profile.credit_profile in {"Poor", "Very poor"}:
            score += 0.16; reasons.append("You reported a weak credit profile.")
        if profile.urgent_debt_need or profile.urgent_housing_need or profile.urgent_energy_need:
            score += 0.28; reasons.append("Urgent arrears or essential-bill pressure makes free debt advice a high-priority referral.")
        if profile.total_debt == 0 and not profile.urgent_debt_need:
            score = max(score, 0.10)

    elif bid == "benefits_calculator_referral":
        score = 0.74
        reasons.append("A detailed independent benefits calculator is a useful cross-check for almost every UK household screening.")
        if profile.is_student or profile.public_funds_access == "Not sure":
            score += 0.10; reasons.append("Your situation may need specialist advice because automated calculators can be less accurate for complex cases.")

    else:
        score = 0.12

    if profile.public_funds_blocked and bid in MEANS_TESTED_OR_PUBLIC_FUND_SENSITIVE:
        score = min(score, 0.14)
        reasons.append("You indicated no recourse to public funds; many mainstream benefits may be restricted. Seek specialist welfare/immigration advice before relying on this screen.")

    if profile.public_funds_access == "Not sure" and bid in MEANS_TESTED_OR_PUBLIC_FUND_SENSITIVE:
        reasons.append("Public-funds access is uncertain, so eligibility should be checked with a qualified adviser.")

    if not reasons:
        reasons.append("The app found only a weak screening signal from the information entered.")
    return clamp(score), reasons
