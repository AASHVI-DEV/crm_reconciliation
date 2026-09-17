# CRM Reconciliation Pipeline

Automated integration pipeline built in Python to reconcile web-scraped healthcare facility data with a CRM REST API.

## Features
- **Scraper:** Dynamic web scraper (`scraper.py`) fetching facility records.
- **Fuzzy Matching:** RapidFuzz-based matching logic (`reconcile.py`) evaluating account similarity.
- **CHOW SOP Compliance:** Business logic to split historical revenue/AR from active accounts on Change of Ownership.
- **Human-in-the-Loop UI:** Streamlit dashboard (`app.py`) for manual proposal review and direct CRM mutations.
- **CI/CD Automation:** GitHub Actions workflow (`.github/workflows/daily_sync.yml`) running daily sync jobs.

## Setup & Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Run reconciliation engine: `python reconcile.py`
3. Launch Review UI: `streamlit run app.py`
