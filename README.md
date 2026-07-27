# AI-Based Financial Benefits Consultant

This repository is a Streamlit MVP for an AI financial-benefits screening assistant. It collects a user's non-identifying household, employment, income, debt, and basic-needs information; ranks possible government and nonprofit benefit resources; and generates application checklists.

## What is included

- Streamlit web app (`app.py`)
- Structured benefit catalog (`data/benefits_catalog.json`)
- Safe source parser with an allow-list (`src/ingestion.py`)
- Rule-based eligibility screening (`src/rules.py`)
- Supervised machine-learning prototype trained on synthetic labels (`src/models.py`)
- Neural-network prototype using scikit-learn `MLPClassifier` (`src/models.py`)
- Reinforcement-learning-style feedback loop with local JSONL feedback (`src/feedback.py`)
- Advisor/checklist generation (`src/advisor.py`)
- Tests (`tests/test_engine.py`)

## Important compliance note

This MVP is not a government agency, lender, credit counselor, attorney, or financial advisor. It does not make official eligibility decisions. It uses synthetic training data and simplified screening rules. Production must replace demo thresholds and synthetic labels with official program rules, state-specific eligibility data, verified source ingestion, audit logging, human review, and privacy/security controls.

The app is designed to avoid collecting names, Social Security numbers, exact addresses, bank logins, or account credentials.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Run in Streamlit Community Cloud

1. Upload this folder to a GitHub repository.
2. Go to Streamlit Community Cloud.
3. Create a new app.
4. Select `app.py` as the entry point.
5. Deploy.

## Upload to GitHub

```bash
git init
git add .
git commit -m "Initial AI financial benefits consultant MVP"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Data-source strategy

The included catalog links to official or reputable sources such as USA.gov, Healthcare.gov, HUD, HHS, USDA, IRS, VA.gov, ChildCare.gov, 211, and NFCC. Production should add:

- source freshness timestamps;
- provenance for each extracted paragraph;
- robots.txt and terms-of-use review;
- state-specific rules and program APIs where available;
- human validation before using new source content.

## Product/copyright placeholder

Copyright (c) 2026 Sissie. All rights reserved.

This placeholder protects the code by default under copyright law, but it is not a substitute for legal advice or formal registration. For a public GitHub repo, choose a license intentionally. If no open-source license is desired, keep the repo private and retain the proprietary notice.
