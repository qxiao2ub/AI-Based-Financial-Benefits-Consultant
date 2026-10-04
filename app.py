from __future__ import annotations

import io
import json
from datetime import date

import pandas as pd
import streamlit as st

from src.catalog import load_catalog
from src.engine import evaluate_profile, results_to_table
from src.feedback import record_feedback
from src.ingestion import fetch_and_parse_page
from src.schema import (
    CREDIT_PROFILES,
    EMPLOYMENT_LABELS,
    EMPLOYMENT_STATUSES,
    HOUSING_LABELS,
    HOUSING_TENURES,
    PUBLIC_FUNDS_OPTIONS,
    UK_NATIONS,
    UserProfile,
)
from src.security import sanitize_postcode
from src.ui import footer, hero, inject_css, section_header, sidebar_brand
from src.visitor_counter import increment_visitor

st.set_page_config(
    page_title="UK AI Financial Benefits Consultant",
    page_icon="🇬🇧",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "visitor_counted" not in st.session_state:
    count, counter_source = increment_visitor()
    st.session_state.visitor_counted = True
    st.session_state.visitor_count = max(1, int(count))
    st.session_state.counter_source = counter_source

visitor_count = max(1, int(st.session_state.get("visitor_count", 1)))
counter_source = st.session_state.get("counter_source", "session")

sidebar_brand(visitor_count, counter_source)
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Check benefits", "Results", "Sissie AI advisor", "Feedback", "Sources & parser", "About"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.caption("Privacy-first MVP: do not enter National Insurance numbers, bank logins, exact account numbers, passwords or identity documents into this app.")

hero(visitor_count)


def money(v: float) -> str:
    return f"£{v:,.0f}"


def make_profile() -> UserProfile:
    child16 = int(st.session_state.form_child16)
    child12 = min(int(st.session_state.form_child12), child16)
    child5 = min(int(st.session_state.form_child5), child12)
    dep20 = max(int(st.session_state.form_dep20), child16)
    return UserProfile(
        age=int(st.session_state.form_age),
        nation=st.session_state.form_nation,
        postcode=sanitize_postcode(st.session_state.form_postcode),
        household_size=int(st.session_state.form_household_size),
        partner_in_household=bool(st.session_state.form_partner),
        dependents_under_20=dep20,
        children_under_16=child16,
        children_under_12=child12,
        children_under_5=child5,
        annual_household_income=float(st.session_state.form_income),
        savings_and_investments=float(st.session_state.form_savings),
        employment_status=st.session_state.form_employment,
        hours_worked_per_week=float(st.session_state.form_hours),
        recent_job_loss=bool(st.session_state.form_job_loss),
        recent_ni_contributions=bool(st.session_state.form_ni),
        is_student=bool(st.session_state.form_student),
        reached_state_pension_age=bool(st.session_state.form_pension_age),
        long_term_health_condition=bool(st.session_state.form_health),
        daily_living_difficulty=bool(st.session_state.form_daily),
        mobility_difficulty=bool(st.session_state.form_mobility),
        health_limits_work=bool(st.session_state.form_work_limit),
        pregnant_or_new_parent=bool(st.session_state.form_parent),
        carer_hours_per_week=float(st.session_state.form_carer_hours),
        cared_person_gets_qualifying_disability_benefit=bool(st.session_state.form_cared_benefit),
        receives_universal_credit=bool(st.session_state.form_uc),
        receives_pension_credit=bool(st.session_state.form_pc),
        receives_means_tested_benefit=bool(st.session_state.form_means),
        housing_tenure=st.session_state.form_housing,
        monthly_rent_or_mortgage=float(st.session_state.form_rent),
        monthly_council_tax_or_rates=float(st.session_state.form_council),
        monthly_energy_cost=float(st.session_state.form_energy),
        monthly_childcare_cost=float(st.session_state.form_childcare),
        total_debt=float(st.session_state.form_debt),
        monthly_debt_payments=float(st.session_state.form_debt_pay),
        credit_profile=st.session_state.form_credit,
        public_funds_access=st.session_state.form_public_funds,
        urgent_food_need=bool(st.session_state.form_food_need),
        urgent_housing_need=bool(st.session_state.form_housing_need),
        urgent_energy_need=bool(st.session_state.form_energy_need),
        urgent_debt_need=bool(st.session_state.form_debt_need),
    )


def render_results() -> None:
    results = st.session_state.get("results")
    profile = st.session_state.get("profile")
    if not results or not profile:
        st.info("Run a benefits check first. Go to **Check benefits** and submit the profile.")
        return

    st.subheader("Ranked UK benefit and support matches")
    st.caption(f"Profile nation: {profile.nation} · Results generated {date.today().isoformat()} · Percentages are screening priorities, not official approval odds.")

    table = pd.DataFrame(results_to_table(results))
    st.dataframe(table, use_container_width=True, hide_index=True)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    st.download_button("Download results as CSV", csv_bytes, "uk_benefits_screening_results.csv", "text/csv")

    chart_df = pd.DataFrame({"Support": [r["benefit"]["short_name"] for r in results[:8]], "Screening match": [round(r["final_score"]*100,1) for r in results[:8]]}).set_index("Support")
    st.bar_chart(chart_df, y="Screening match", horizontal=True)

    if "saved_ids" not in st.session_state:
        st.session_state.saved_ids = []

    for idx, result in enumerate(results, start=1):
        benefit = result["benefit"]
        score = round(result["final_score"]*100)
        c1, c2 = st.columns([5,1])
        with c1:
            st.markdown(
                f"<div class='result-card'><div class='section-kicker'>#{idx} · {' / '.join(benefit['category'][:2])}</div>"
                f"<div style='display:flex;justify-content:space-between;gap:1rem;align-items:end'><div><div class='step-title'>{benefit['name']}</div>"
                f"<div style='color:#60717d'>{benefit['summary']}</div></div><div><div class='score'>{score}%</div><div class='score-caption'>screening match</div></div></div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            saved = benefit["id"] in st.session_state.saved_ids
            if st.button("Saved ✓" if saved else "Save", key=f"save_{benefit['id']}", use_container_width=True):
                if saved:
                    st.session_state.saved_ids.remove(benefit["id"])
                else:
                    st.session_state.saved_ids.append(benefit["id"])
                st.rerun()

        with st.expander(f"Why {benefit['short_name']} ranked here · application steps"):
            st.write(result["advisor_message"])
            st.progress(float(result["final_score"]))
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("**Why it matched**")
                for reason in result["reasons"]:
                    st.write(f"• {reason}")
                st.markdown("**Documents to prepare**")
                for doc in result["documents"]:
                    st.write(f"• {doc}")
            with c4:
                st.markdown("**Suggested next steps**")
                for step in result["checklist"]:
                    st.write(f"• {step}")
                st.link_button("Open official/source guidance ↗", result["source_url"], use_container_width=True)
                st.caption(f"Source verified in catalog: {benefit.get('last_verified','')} · {benefit.get('notes','')}")
            with st.expander("AI model signals"):
                st.write(f"Rule signal: {result['rule_score']*100:.1f}%")
                st.write(f"Supervised ML signal: {result['ml_probability']*100:.1f}%")
                st.write(f"Neural-network signal: {result['neural_probability']*100:.1f}%")
                st.caption(result["important_model_note"])


if page == "Home":
    st.markdown(
        """
<div class="agent">
  <div class="agent-orb">AI</div>
  <div><strong style="color:#12344D;font-size:1.05rem">Meet Sissie AI</strong><br/>
  <span style="color:#60717d">A UK-focused screening character that combines transparent rules, supervised machine learning, a neural-network model and a feedback loop to prioritise benefits and application guidance.</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.write("")
    a,b,c = st.columns(3)
    a.metric("UK nations covered", "4")
    b.metric("Benefits & support routes", len(load_catalog()))
    c.metric("Visible cumulative visitors", f"{visitor_count:,}")

    st.subheader("How the prototype works")
    cols = st.columns(4)
    cards = [
        ("1. Intake", "Household, work, income, savings, housing, childcare, debt, caring and health signals."),
        ("2. AI screening", "Rule engine + supervised Random Forest + neural-network model trained on synthetic examples."),
        ("3. UK source routing", "Nation-aware links to GOV.UK, NHS, mygov.scot, nidirect and trusted guidance."),
        ("4. Feedback learning", "Users can rate recommendations; local feedback can make small bounded ranking adjustments."),
    ]
    for col,(title,text) in zip(cols,cards):
        with col:
            st.markdown(f"<div class='card'><strong style='color:#12344D'>{title}</strong><div style='margin-top:.4rem;color:#60717d'>{text}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='notice'><strong>Important:</strong> this app does not decide entitlement and does not submit applications. For detailed calculations, use a benefits calculator listed by GOV.UK and verify each programme with the responsible authority.</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("Start UK benefits check", type="primary"):
        st.session_state._nav_hint = "Check benefits"
        st.info("Choose **Check benefits** from the left navigation to begin.")

elif page == "Check benefits":
    st.subheader("Tell Sissie AI about the household")
    st.caption("Do not enter names, National Insurance numbers, bank credentials, passwords or full identity-document numbers.")

    with st.form("uk_benefits_profile_form"):
        section_header("Step 1 of 4", "Household & location", "Use approximate, non-identifying information. Nation matters because some benefits are devolved.")
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.number_input("Age", 18, 100, 35, 1, key="form_age")
        with c2:
            st.selectbox("UK nation", UK_NATIONS, key="form_nation")
        with c3:
            st.text_input("Postcode / district (optional)", "", key="form_postcode", help="Used only as an in-session location hint. Do not enter a street address.")
        with c4:
            st.number_input("Household size", 1, 12, 2, 1, key="form_household_size")
        c5,c6,c7,c8,c9 = st.columns(5)
        with c5: st.checkbox("Partner in household", key="form_partner")
        with c6: st.number_input("Dependants under 20", 0, 10, 0, 1, key="form_dep20")
        with c7: st.number_input("Children under 16", 0, 10, 0, 1, key="form_child16")
        with c8: st.number_input("Children under 12", 0, 10, 0, 1, key="form_child12")
        with c9: st.number_input("Children under 5", 0, 10, 0, 1, key="form_child5")
        st.selectbox("Do you believe your immigration status allows access to public funds?", PUBLIC_FUNDS_OPTIONS, index=1, key="form_public_funds", help="If unsure, choose Not sure. This app does not provide immigration advice.")

        section_header("Step 2 of 4", "Employment, income & benefits", "These signals affect means-tested and contribution-based support. Use household income before tax as an estimate.")
        c10,c11,c12,c13 = st.columns(4)
        with c10: st.number_input("Annual household income (£)", 0.0, 500000.0, 30000.0, 500.0, key="form_income")
        with c11: st.number_input("Savings & investments (£)", 0.0, 1000000.0, 2500.0, 250.0, key="form_savings")
        with c12: st.selectbox("Employment status", EMPLOYMENT_STATUSES, format_func=lambda x: EMPLOYMENT_LABELS[x], key="form_employment")
        with c13: st.number_input("Hours worked per week", 0.0, 90.0, 35.0, 1.0, key="form_hours")
        c14,c15,c16,c17 = st.columns(4)
        with c14: st.checkbox("Recent job loss / major hours reduction", key="form_job_loss")
        with c15: st.checkbox("Paid/credited enough NI recently (best estimate)", value=True, key="form_ni")
        with c16: st.checkbox("Student", key="form_student")
        with c17: st.checkbox("Reached State Pension age", key="form_pension_age", help="Use the official State Pension age checker if unsure.")
        c18,c19,c20 = st.columns(3)
        with c18: st.checkbox("Currently receive Universal Credit", key="form_uc")
        with c19: st.checkbox("Currently receive Pension Credit", key="form_pc")
        with c20: st.checkbox("Receive another means-tested benefit", key="form_means")

        section_header("Step 3 of 4", "Health, caring & family", "These inputs route disability, carer, maternity and young-family support. They are used only for this screening session and coarse feedback segments exclude health fields.")
        c21,c22,c23,c24 = st.columns(4)
        with c21: st.checkbox("Long-term health condition/disability", key="form_health")
        with c22: st.checkbox("Difficulty with everyday tasks", key="form_daily")
        with c23: st.checkbox("Difficulty getting around / mobility", key="form_mobility")
        with c24: st.checkbox("Health limits ability to work", key="form_work_limit")
        c25,c26,c27 = st.columns(3)
        with c25: st.checkbox("Pregnant / recently had a baby", key="form_parent")
        with c26: st.number_input("Unpaid caring hours per week", 0.0, 100.0, 0.0, 1.0, key="form_carer_hours")
        with c27: st.checkbox("Person cared for gets a qualifying disability benefit", key="form_cared_benefit")

        section_header("Step 4 of 4", "Housing, bills, debt & urgent needs", "Debt and credit do not automatically determine benefit eligibility, but they help Sissie AI prioritise free debt guidance and crisis referrals.")
        c28,c29,c30,c31 = st.columns(4)
        with c28: st.selectbox("Housing tenure", HOUSING_TENURES, format_func=lambda x: HOUSING_LABELS[x], key="form_housing")
        with c29: st.number_input("Monthly rent / mortgage (£)", 0.0, 10000.0, 1100.0, 50.0, key="form_rent")
        with c30: st.number_input("Monthly Council Tax / domestic rates (£)", 0.0, 2000.0, 160.0, 10.0, key="form_council")
        with c31: st.number_input("Monthly energy cost (£)", 0.0, 2000.0, 150.0, 10.0, key="form_energy")
        c32,c33,c34,c35 = st.columns(4)
        with c32: st.number_input("Monthly childcare cost (£)", 0.0, 5000.0, 0.0, 25.0, key="form_childcare")
        with c33: st.number_input("Total debt / loans (£)", 0.0, 1000000.0, 0.0, 250.0, key="form_debt")
        with c34: st.number_input("Monthly debt repayments (£)", 0.0, 20000.0, 0.0, 25.0, key="form_debt_pay")
        with c35: st.selectbox("Credit profile", CREDIT_PROFILES, key="form_credit", help="UK agencies use different scoring scales, so this MVP uses broad categories rather than a US-style 300–850 score.")
        st.markdown("**Urgent needs**")
        c36,c37,c38,c39 = st.columns(4)
        with c36: st.checkbox("Food insecurity", key="form_food_need")
        with c37: st.checkbox("Rent/mortgage/housing crisis", key="form_housing_need")
        with c38: st.checkbox("Energy bill / disconnection crisis", key="form_energy_need")
        with c39: st.checkbox("Debt enforcement / missed priority payments", key="form_debt_need")

        submitted = st.form_submit_button("Run Sissie AI UK benefits screening", type="primary", use_container_width=True)

    if submitted:
        profile = make_profile()
        with st.spinner("Sissie AI is combining UK rules, supervised ML and neural-network signals..."):
            results = evaluate_profile(profile, top_n=12)
        st.session_state.profile = profile
        st.session_state.results = results
        st.success("Screening complete. Open **Results** from the left navigation.")
        top = results[0] if results else None
        if top:
            st.metric("Top screening match", top["benefit"]["short_name"], f"{top['final_score']*100:.0f}%")

elif page == "Results":
    render_results()

elif page == "Sissie AI advisor":
    results = st.session_state.get("results")
    profile = st.session_state.get("profile")
    if not results or not profile:
        st.info("Run a benefits check first to unlock personalised application guidance.")
    else:
        st.subheader("Sissie AI application coach")
        saved_ids = st.session_state.get("saved_ids", [])
        preferred = [r for r in results if r["benefit"]["id"] in saved_ids] or results
        names = [r["benefit"]["name"] for r in preferred]
        choice = st.selectbox("Choose a benefit/support route", names)
        result = next(r for r in preferred if r["benefit"]["name"] == choice)
        benefit = result["benefit"]
        st.markdown(f"<div class='agent'><div class='agent-orb'>AI</div><div><strong>{benefit['name']}</strong><br><span style='color:#60717d'>{result['advisor_message']}</span></div></div>", unsafe_allow_html=True)
        st.write("")
        c1,c2,c3 = st.columns(3)
        c1.metric("Screening match", f"{result['final_score']*100:.0f}%")
        c2.metric("Nation", profile.nation)
        c3.metric("Source checked", benefit.get("last_verified", ""))
        st.markdown("### Application plan")
        for i, step in enumerate(result["checklist"], start=1):
            st.write(f"**{i}.** {step}")
        st.markdown("### Evidence checklist")
        for doc in result["documents"]:
            st.checkbox(doc, key=f"doc_{benefit['id']}_{doc}")
        st.link_button("Open official/source guidance", result["source_url"], type="primary")
        st.warning("Do not send personal documents to this prototype. Upload evidence only to the official service or a trusted adviser when you decide to apply.")

elif page == "Feedback":
    st.subheader("Feedback learning loop")
    st.write("Feedback is stored as a local JSONL event in the running app instance. It makes only a small bounded adjustment to future rankings so user feedback cannot override official-rule signals.")
    results = st.session_state.get("results")
    profile = st.session_state.get("profile")
    if not results or not profile:
        st.info("Run a benefits check first so feedback can be attached to a recommendation.")
    else:
        options = {r["benefit"]["name"]: r["benefit"]["id"] for r in results}
        name = st.selectbox("Recommendation", list(options))
        c1,c2 = st.columns(2)
        with c1: rating = st.slider("How useful was this recommendation?", 1, 5, 4)
        with c2: helpful = st.checkbox("Helpful", value=True)
        comment = st.text_area("Optional comments", max_chars=500)
        if st.button("Save feedback", type="primary"):
            record_feedback(profile.to_dict(), options[name], rating, helpful, comment)
            st.success("Feedback saved locally. Re-run the screening to allow the bounded feedback signal to participate in ranking.")

elif page == "Sources & parser":
    st.subheader("UK source intelligence & parser")
    st.write("The catalog routes users to official or government-backed sources. The parser can fetch one allow-listed public page on demand and extract readable text for research/prototyping.")
    catalog = load_catalog()
    source_df = pd.DataFrame([
        {"Benefit/support": b["name"], "Nations": ", ".join(b["nations"]), "Source": b["source_url"], "Verified": b.get("last_verified", "")}
        for b in catalog
    ])
    st.dataframe(source_df, use_container_width=True, hide_index=True)
    choice = st.selectbox("Choose a source to parse", [b["name"] for b in catalog])
    benefit = next(b for b in catalog if b["name"] == choice)
    if st.button("Fetch and parse selected source"):
        with st.spinner("Fetching public guidance page..."):
            try:
                parsed = fetch_and_parse_page(benefit["source_url"])
                st.success(parsed.title)
                st.text_area("Parsed excerpt", parsed.text[:7000], height=360)
            except Exception as exc:
                st.error(f"Source fetch failed: {exc}")
    st.caption("Production systems should add provenance records, page-change monitoring, terms/robots review, caching and human validation before using scraped text to change eligibility logic.")

elif page == "About":
    st.subheader("Product, AI architecture & governance")
    st.markdown("**Author:** Sissie Ma  \n**Advisor:** Dr. Qingyang Xiao")
    st.markdown("""
### AI pipeline
- **Transparent screening rules:** nation-aware heuristics capture obvious programme conditions and route users to the correct UK authority.
- **Supervised machine learning:** a Random Forest multi-output classifier is trained on synthetic profiles labelled from the screening logic. It demonstrates the ML pipeline without claiming government training data.
- **Neural network:** an MLP neural network learns a second nonlinear signal from the same synthetic prototype dataset.
- **Feedback / reinforcement-learning-style loop:** user ratings create small, bounded local ranking adjustments. This is a prototype reward signal, not autonomous policy learning.
- **Source parser:** allow-listed UK public pages can be fetched and parsed on demand for research. Parsed text is not automatically promoted into eligibility rules.

### Safety and privacy design
The app intentionally avoids names, National Insurance numbers, bank logins, full account details and uploaded identity documents. Health and caring inputs are used only for in-session screening; coarse feedback records do not store health fields or postcode. A production service would still need a formal privacy impact assessment, security review, accessibility testing, data-retention controls, model monitoring and expert benefits/legal review.

### Copyright
Copyright © 2026 Sissie Ma. All rights reserved. Advisor: Dr. Qingyang Xiao. This repository is supplied as a proprietary educational/research prototype unless the author chooses another licence.
""")
    st.markdown("<div class='notice'><strong>Not official advice:</strong> benefit rules change and can be complex. The app is a discovery and preparation tool only. Always verify through GOV.UK, mygov.scot, nidirect, the NHS, your council or a qualified benefits adviser.</div>", unsafe_allow_html=True)

footer(visitor_count)
