# Architecture

`app.py` supplies shared navigation. `database.py` persists versions and related history in SQLite. `ingestion.py` handles import, mapping, normalisation and validation. `analysis.py` contains evidence-aware calculations. `pages.py` presents the sixteen connected Streamlit pages and `reporting.py` produces local PDFs.

Workflow: Import -> Preview -> Map -> Normalise -> Validate -> Save immutable version -> Analyse -> Visualise -> Compare -> Export.
