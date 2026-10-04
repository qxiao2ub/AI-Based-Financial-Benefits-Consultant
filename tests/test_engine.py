from src.engine import evaluate_profile
from src.schema import UserProfile


def sample_profile(nation="England"):
    return UserProfile(
        age=34, nation=nation, postcode="SW1A", household_size=3, partner_in_household=True,
        dependents_under_20=1, children_under_16=1, children_under_12=1, children_under_5=1,
        annual_household_income=26000, savings_and_investments=2500, employment_status="employed_part_time",
        hours_worked_per_week=22, recent_job_loss=False, recent_ni_contributions=True, is_student=False,
        reached_state_pension_age=False, long_term_health_condition=False, daily_living_difficulty=False,
        mobility_difficulty=False, health_limits_work=False, pregnant_or_new_parent=False, carer_hours_per_week=0,
        cared_person_gets_qualifying_disability_benefit=False, receives_universal_credit=True,
        receives_pension_credit=False, receives_means_tested_benefit=True, housing_tenure="private_renter",
        monthly_rent_or_mortgage=1200, monthly_council_tax_or_rates=165, monthly_energy_cost=150,
        monthly_childcare_cost=350, total_debt=9000, monthly_debt_payments=250, credit_profile="Fair",
        public_funds_access="Yes", urgent_food_need=False, urgent_housing_need=False, urgent_energy_need=True,
        urgent_debt_need=False,
    )


def test_engine_returns_ranked_results():
    results = evaluate_profile(sample_profile(), top_n=8)
    assert len(results) == 8
    assert results[0]["final_score"] >= results[-1]["final_score"]
    assert all("source_url" in r for r in results)


def test_scotland_uses_scottish_disability_route():
    p = sample_profile("Scotland")
    p.long_term_health_condition = True
    p.daily_living_difficulty = True
    results = evaluate_profile(p, top_n=25)
    ids = {r["benefit"]["id"] for r in results}
    assert "adult_disability_payment_scotland" in ids
    assert "pip" not in ids
