from src.engine import evaluate_profile
from src.schema import UserProfile


def test_evaluate_profile_returns_ranked_results():
    profile = UserProfile(
        age=34,
        state="NY",
        zip_code="10001",
        household_size=3,
        dependents_under_18=1,
        children_under_5=1,
        annual_income=28000,
        employment_status="employed_part_time",
        recent_job_loss=False,
        has_recent_work_history=True,
        is_student=False,
        is_veteran_or_service_member=False,
        has_disability_or_chronic_illness=False,
        is_pregnant_or_postpartum=False,
        has_health_insurance=False,
        monthly_rent_or_mortgage=1500,
        monthly_utilities=250,
        total_debt=9000,
        monthly_debt_payments=350,
        credit_score=610,
        urgent_food_need=True,
        urgent_housing_need=False,
        urgent_utility_need=True,
    )
    results = evaluate_profile(profile, top_n=5)
    assert len(results) == 5
    assert results[0]["final_score"] >= results[-1]["final_score"]
    assert "advisor_message" in results[0]
