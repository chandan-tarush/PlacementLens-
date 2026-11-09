"""Run with: streamlit run app.py"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))
import streamlit as st
from placementlens import database as db
from placementlens import pages
from placementlens.ui import style, topbar

style(); db.initialise()
NAV = ["Home","Import Centre","Dataset Studio","Placement Overview","Salary Reality Check","Placement Coverage","Recruiter Intelligence","Company Insights","Role Explorer","Location Insights","Skill & Course Recommendations","Institution Comparator","Trends & Stability","Evidence & Data Quality","Report Builder & History","Settings & Methodology"]
with st.sidebar:
    st.image("assets/placementlens-mark.png",width=58)
    st.markdown("**PlacementLens**")
    st.caption("COLLEGE PLACEMENT INTELLIGENCE")
    if "nav" not in st.session_state: st.session_state.nav="Home"
    choice=st.radio("Workspace",NAV,index=NAV.index(st.session_state.nav),label_visibility="collapsed")
    st.session_state.nav=choice
    versions=db.versions()
    if not versions.empty:
        ids=versions.id.astype(int).tolist(); labels=[f"v{row.id} - {row.label}" for _,row in versions.iterrows()]
        selected=st.selectbox("Current dataset",range(len(ids)),format_func=lambda x: labels[x]);version_id=ids[selected]
        is_synthetic=bool(versions.iloc[selected].is_synthetic)
        if is_synthetic: st.warning("DEMONSTRATION DATA\nSynthetic records only.")
    else: version_id=None;st.info("No dataset selected")
    st.caption("Local-first. Your data stays on this device.")
df=db.load_dataset(version_id) if version_id else __import__("pandas").DataFrame()
dataset_label=labels[selected] if version_id else "Import data to begin"
topbar(dataset_label, bool(version_id and is_synthetic))
routes={"Home":pages.home,"Import Centre":lambda d,v:pages.import_centre(),"Dataset Studio":pages.dataset_studio,"Placement Overview":pages.overview,"Salary Reality Check":pages.salary,"Placement Coverage":pages.coverage_page,"Recruiter Intelligence":pages.recruiter,"Company Insights":pages.company,"Role Explorer":pages.role,"Location Insights":pages.locations,"Skill & Course Recommendations":pages.skills,"Institution Comparator":pages.comparator,"Trends & Stability":pages.trends,"Evidence & Data Quality":pages.evidence_page,"Report Builder & History":pages.reports,"Settings & Methodology":pages.settings}
routes[choice](df,version_id)
