# UK AI Financial Benefits Consultant

**Author:** Sissie Ma  
**Advisor:** Dr. Qingyang Xiao

A UK-focused Streamlit prototype that screens a user's household, employment, income, savings, housing, childcare, debt, caring and health circumstances, then ranks benefits and trusted support routes with transparent reasons and application checklists.

The uploaded React/TanStack UI was migrated into a Streamlit-native interface with the same design language: navy/coral/teal palette, large editorial headings, step-based intake cards, ranked match cards, saved recommendations, guidance panels, source parsing, feedback and visible cumulative visitor count.

## UK coverage

The app routes users by **England, Scotland, Wales, and Northern Ireland**. The catalog includes or routes to support such as:

- Universal Credit
- Council Tax Reduction / Northern Ireland rate support
- Child Benefit
- Personal Independence Payment (PIP)
- Adult Disability Payment (Scotland)
- Attendance Allowance / Pension Age Disability Payment (Scotland)
- Carer's Allowance / Carer Support Payment (Scotland)
- New Style Jobseeker's Allowance
- New Style Employment and Support Allowance
- Pension Credit
- Tax-Free Childcare
- Healthy Start / Best Start Foods (Scotland)
- Warm Home Discount
- Cold Weather Payment / Winter Heating Payment (Scotland)
- Winter Fuel / pension-age winter support
- NHS Low Income Scheme
- Support for Mortgage Interest
- Maternity Allowance
- Free School Meals / devolved school-meal support
- Free debt-advice referral via MoneyHelper
- Independent benefits-calculator referral via GOV.UK

The source catalog is in `data/benefits_catalog.json` and records a `last_verified` date.

## AI pipeline

This is an explainable **MVP**, not an official eligibility engine.

1. **Transparent rule screening** – nation-aware heuristics identify strong/weak programme signals.
2. **Supervised machine learning** – a multi-output Random Forest is trained on synthetic profiles labelled from the screening rules.
3. **Neural network** – a multi-output `MLPClassifier` learns a second nonlinear signal from synthetic data.
4. **Feedback / reinforcement-learning-style loop** – user ratings are stored in local JSONL and can make only a small bounded ranking adjustment.
5. **Application advisor** – Sissie AI turns ranked results into reasons, document checklists and next steps.
6. **Source parser** – on-demand parser for allow-listed public UK guidance pages (GOV.UK, NHS, mygov.scot, nidirect and selected government-backed/advice sources).

The displayed percentages are **screening priorities**, not probabilities of DWP/HMRC/council/NHS approval.

## Visitor counter — no app database

The app increments the visitor count once per Streamlit browser session. The visible count is shown in the **header, sidebar and footer on every app view**.

- The app itself does **not** create or manage a database.
- It uses a lightweight hosted counter endpoint so the cumulative total is not intentionally reset by ordinary Streamlit redeploys.
- If that endpoint is temporarily unavailable, the app falls back to `data/visitor_counter.txt` and displays at least `1`, never `0`.
- The local fallback can reset when Streamlit replaces its ephemeral container; therefore the hosted counter is the persistence layer for the all-time visible total.
- A new browser session/reload may count as another visit. This is a visit counter, not identity tracking or an audited unique-person analytics system.

Counter code: `src/visitor_counter.py`.

## Privacy and governance

This prototype intentionally does **not** ask users to enter:

- names;
- National Insurance numbers;
- bank logins or passwords;
- full account numbers;
- uploaded identity documents.

Health/caring inputs stay in the in-memory screening profile. The feedback file stores only coarse segments and excludes postcode and health fields.

A production service should add a privacy impact assessment, formal consent/retention policy, encryption, authentication/authorisation, accessibility testing, source-change monitoring, expert welfare-rights review, model monitoring, incident response and legal/compliance review.

## Run locally

Recommended local environment: **Python 3.12.13**.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload **all files and folders from this repository root**.
3. Commit and push to the `main` branch.
4. In Streamlit Community Cloud, create a new app.
5. Select your GitHub repository and branch.
6. Set the main file path to `app.py`.
7. Open **Advanced settings** and select Python **3.12**. Streamlit Community Cloud currently defaults to Python 3.12 and lets you choose a supported version during deployment.
8. Deploy.

No app secrets are required for the default prototype.

## GitHub upload commands

```bash
git init
git add .
git commit -m "UK AI Financial Benefits Consultant by Sissie Ma"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

## Testing

```bash
python -m compileall app.py src tests
pytest -q
```

## Important legal / benefits disclaimer

This software is not the UK Government, DWP, HMRC, an NHS body, a local authority, Social Security Scotland, or the Department for Communities in Northern Ireland. It does not make official eligibility decisions and does not submit claims. Benefit rules, rates, thresholds and devolved arrangements can change. Always verify the current official source before acting.

For a detailed calculation, GOV.UK lists independent benefits calculators including entitledto, Turn2us and Policy in Practice. Complex cases — especially immigration/public-funds issues, students, residential care, prisoners, appeals and overlapping benefits — should be checked with a qualified adviser.

## Copyright

Copyright © 2026 Sissie Ma. All rights reserved.  
Advisor: Dr. Qingyang Xiao.

See `LICENSE`.
