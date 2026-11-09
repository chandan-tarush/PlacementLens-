# PlacementLens

PlacementLens is a local-first Streamlit workspace for importing, cleaning, analysing and reporting on college placement data. It is an analytical aid, not an official ranking or accreditation product.

## Run locally

1. Use Python 3.11 or later.
2. Create and activate a virtual environment (recommended).
3. Run `pip install -r requirements.txt`.
4. Run `streamlit run app.py`.

Use **Import Centre** to load CSV/XLSX data, or load the clearly labelled synthetic demonstration dataset to explore every screen. Imported data is saved as a new persistent SQLite dataset version; it is never silently overwritten.

## Expected fields

Column mapping accepts flexible labels. The canonical fields include student ID, institution, year, branch, programme, status, eligible, registered, opted out, company, role, salary (LPA), salary type, offers, city, country, skills and source.

## Data interpretation

- Missing values remain missing, not zero.
- Placement rate appears only where compatible placed and eligible values exist.
- Offers and placed students are different measures.
- Salary displays use individual records marked as CTC and retain outliers.
- Results depend on the evidence in the selected dataset version.

See [docs/methodology.md](docs/methodology.md) and [docs/limitations.md](docs/limitations.md) for detail.
