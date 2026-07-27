from __future__ import annotations

import pandas as pd
import streamlit as st

from src.engine import evaluate_profile, results_to_table
from src.feedback import record_feedback
from src.schema import UserProfile, US_STATES, EMPLOYMENT_STATUSES
from src.security import sanitize_zip_code


st.set_page_config(
    page_title="AI Financial Benefits Consultant",
    page_icon="💸",
    layout="wide",
)

st.title("AI-Based Financial Benefits Consultant")
st.caption("Sissie AI screens benefits and local resources. It does not make official government decisions.")

st.warning(
    "Prototype notice: This app uses synthetic training data and simplified screening rules. "
    "It ranks likely benefit matches for discussion and planning only. Always verify current rules with official agencies."
)

with st.sidebar:
    st.header("Privacy and safety")
    st.write(
        "This MVP does not require names, Social Security numbers, or bank credentials. "
        "Feedback stores only coarse, hashed profile segments for local learning."
    )
    st.write("Recommended production additions: encryption, consent logs, source freshness checks, audit trails, and human escalation.")

with st.form("benefits_profile_form"):
    st.subheader("1. Demographic and household details")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        age = st.number_input("Age", min_value=18, max_value=100, value=35, step=1)
    with c2:
        state = st.selectbox("State / territory", US_STATES, index=US_STATES.index("NY") if "NY" in US_STATES else 0)
    with c3:
        zip_code = st.text_input("ZIP code", value="10001")
    with c4:
        household_size = st.number_input("Household size", min_value=1, max_value=12, value=3, step=1)

    c5, c6, c7 = st.columns(3)
    with c5:
        dependents_under_18 = st.number_input("Dependents under 18", min_value=0, max_value=10, value=1, step=1)
    with c6:
        children_under_5 = st.number_input("Children under 5", min_value=0, max_value=10, value=0, step=1)
    with c7:
        is_pregnant_or_postpartum = st.checkbox("Pregnant or recently postpartum")

    st.subheader("2. Employment and income")
    c8, c9, c10, c11 = st.columns(4)
    with c8:
        annual_income = st.number_input("Annual household income", min_value=0.0, max_value=500000.0, value=32000.0, step=1000.0)
    with c9:
        employment_status = st.selectbox("Employment status", EMPLOYMENT_STATUSES, index=EMPLOYMENT_STATUSES.index("employed_part_time"))
    with c10:
        recent_job_loss = st.checkbox("Recent job loss or major hours reduction")
    with c11:
        has_recent_work_history = st.checkbox("Recent work history", value=True)

    c12, c13, c14, c15 = st.columns(4)
    with c12:
        is_student = st.checkbox("Student or training program")
    with c13:
        is_veteran_or_service_member = st.checkbox("Veteran or service member")
    with c14:
        has_disability_or_chronic_illness = st.checkbox("Disability or chronic illness")
    with c15:
        has_health_insurance = st.checkbox("Currently has health insurance", value=False)

    st.subheader("3. Financial situation")
    c16, c17, c18, c19 = st.columns(4)
    with c16:
        monthly_rent_or_mortgage = st.number_input("Monthly rent or mortgage", min_value=0.0, max_value=10000.0, value=1450.0, step=50.0)
    with c17:
        monthly_utilities = st.number_input("Monthly utilities", min_value=0.0, max_value=3000.0, value=250.0, step=25.0)
    with c18:
        total_debt = st.number_input("Total debt", min_value=0.0, max_value=500000.0, value=12000.0, step=500.0)
    with c19:
        monthly_debt_payments = st.number_input("Monthly debt payments", min_value=0.0, max_value=10000.0, value=420.0, step=25.0)

    c20, c21, c22, c23 = st.columns(4)
    with c20:
        credit_score = st.number_input("Credit score", min_value=300, max_value=850, value=620, step=1)
    with c21:
        urgent_food_need = st.checkbox("Urgent food need")
    with c22:
        urgent_housing_need = st.checkbox("Urgent housing/rent need")
    with c23:
        urgent_utility_need = st.checkbox("Urgent utility shutoff/bill need")

    submitted = st.form_submit_button("Rank possible benefits")

if submitted:
    profile = UserProfile(
        age=int(age),
        state=state,
        zip_code=sanitize_zip_code(zip_code),
        household_size=int(household_size),
        dependents_under_18=int(dependents_under_18),
        children_under_5=int(children_under_5),
        annual_income=float(annual_income),
        employment_status=employment_status,
        recent_job_loss=bool(recent_job_loss),
        has_recent_work_history=bool(has_recent_work_history),
        is_student=bool(is_student),
        is_veteran_or_service_member=bool(is_veteran_or_service_member),
        has_disability_or_chronic_illness=bool(has_disability_or_chronic_illness),
        is_pregnant_or_postpartum=bool(is_pregnant_or_postpartum),
        has_health_insurance=bool(has_health_insurance),
        monthly_rent_or_mortgage=float(monthly_rent_or_mortgage),
        monthly_utilities=float(monthly_utilities),
        total_debt=float(total_debt),
        monthly_debt_payments=float(monthly_debt_payments),
        credit_score=int(credit_score),
        urgent_food_need=bool(urgent_food_need),
        urgent_housing_need=bool(urgent_housing_need),
        urgent_utility_need=bool(urgent_utility_need),
    )

    with st.spinner("Training demo AI brain and ranking matches..."):
        results = evaluate_profile(profile, top_n=8)
        table = pd.DataFrame(results_to_table(results))

    st.subheader("Ranked benefit matches")
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Advisor guidance")
    for idx, result in enumerate(results, start=1):
        benefit = result["benefit"]
        with st.expander(f"#{idx}: {benefit['name']} - estimated match {round(result['final_score'] * 100)}%", expanded=(idx <= 3)):
            st.write(result["advisor_message"])
            st.progress(result["final_score"])
            st.markdown("**Why this ranked here**")
            for reason in result["reasons"]:
                st.write(f"- {reason}")
            st.markdown("**Suggested next steps**")
            for step in result["checklist"]:
                st.write(f"- {step}")
            st.markdown("**Documents to gather**")
            for doc in result["documents"]:
                st.write(f"- {doc}")
            st.markdown(f"**Official/source link:** {benefit['source_url']}")
            st.caption(benefit.get("notes", ""))

    st.subheader("Feedback loop for reinforcement learning prototype")
    st.write("Your feedback nudges future rankings slightly without storing your name or exact profile.")
    benefit_options = {r["benefit"]["name"]: r["benefit"]["id"] for r in results}
    fb_col1, fb_col2, fb_col3 = st.columns([2, 1, 1])
    with fb_col1:
        feedback_name = st.selectbox("Which recommendation are you rating?", list(benefit_options.keys()))
    with fb_col2:
        rating = st.slider("Rating", 1, 5, 4)
    with fb_col3:
        helpful = st.checkbox("Helpful", value=True)
    comment = st.text_area("Optional feedback", max_chars=500)
    if st.button("Save feedback locally"):
        record_feedback(profile.to_dict(), benefit_options[feedback_name], rating, helpful, comment)
        st.success("Feedback saved to the local JSONL file. Re-run the ranking to include the small feedback adjustment.")

else:
    st.info("Complete the form and click 'Rank possible benefits' to run the AI screening pipeline.")
