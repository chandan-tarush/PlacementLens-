"""All PlacementLens screens, connected to the selected dataset."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from . import analysis as az
from . import database as db
from . import ingestion as ing
from . import reporting
from .ui import header, chart, kpis, empty_data, bar, context_bar

def fmt(v, suffix=""):
    return "Unavailable" if v is None or pd.isna(v) else f"{v:.1f}{suffix}"

def filters(df):
    cols=st.columns(3); result=df.copy()
    for col,field,label in zip(cols,["institution","year","branch"],["Institution","Year","Branch"]):
        values=sorted(result[field].dropna().unique().tolist()) if field in result else []
        chosen=col.multiselect(label,values)
        if chosen: result=result[result[field].isin(chosen)]
    return result

def home(df, version_id):
    header("See beyond the placement headline.","Trace outcomes to their source. Compare only what the data supports.","PLACEMENTLENS")
    a,b,c=st.columns(3)
    if a.button("Import data",use_container_width=True): st.session_state.nav="Import Centre";st.rerun()
    if b.button("Open dataset",use_container_width=True): st.session_state.nav="Dataset Studio";st.rerun()
    if c.button("Build report",use_container_width=True): st.session_state.nav="Report Builder & History";st.rerun()
    if df.empty:
        st.markdown("<div class='panel'><div class='eyebrow'>START HERE</div><b>Build a reliable placement workspace.</b><p class='muted'>Import a CSV/XLSX placement table, map its columns, then inspect the evidence quality before using comparisons.</p></div>",unsafe_allow_html=True)
        empty_data(); return
    m=az.metrics(df);kpis([("Records",m["records"],"Rows in selected version"),("Placed",m["placed"],"Distinct students if IDs are available"),("Median CTC",fmt(m["median"]," LPA"),"CTC only"),("Data source","DEMO" if "Synthetic" in str(df.source.iloc[0]) else "Imported","Selected version")])
    st.caption("Every tile below is calculated from the selected persisted dataset version. Missing values are never treated as zero.")
    left,right=st.columns([1.15,1])
    with left:
        header("Placement at a glance","Coverage uses compatible eligible and placed records.","OUTCOMES")
        chart(px.funnel(az.coverage(df),x="Students",y="Group",color="Group"))
    with right:
        header("Salary reality","Distribution uses individual CTC records; outliers remain visible.","SALARY")
        chart(px.histogram(az.ctc(df),x="salary_lpa",nbins=16,color_discrete_sequence=["#19D3C5"]))
    col1,col2=st.columns(2)
    with col1: chart(bar(az.grouped(df,"company").head(8),"company","records","Recruiter landscape"))
    with col2: chart(px.line(az.trend(df),x="year",y="placement_rate",markers=True,title="Comparable year-over-year trend"))

def import_centre():
    header("Import Placement Data","Preview, map and validate CSV or Excel records before creating a new dataset version.","IMPORT CENTRE")
    up=st.file_uploader("Choose CSV or Excel",type=["csv","xlsx","xls"])
    if st.button("Load demonstration data",help="Creates a persistent, clearly labelled synthetic dataset."):
        demo=ing.demo_data(); vid=db.save_dataset(demo,"synthetic_demo_placement_data",{},ing.validate(demo),synthetic=True,notes="Synthetic demonstration data - not real outcomes.");st.success(f"Demonstration version {vid} saved.");st.rerun()
    if not up:return
    try: raw=ing.read_file(up)
    except Exception as exc: st.error(str(exc));return
    st.dataframe(raw.head(12),use_container_width=True);suggested=ing.suggest_mapping(raw.columns)
    mapping={}
    with st.expander("Map columns",expanded=True):
        for source in raw.columns:
            options=["Ignore"]+ing.CANONICAL; default=suggested.get(str(source),"Ignore")
            mapping[str(source)]=st.selectbox(str(source),options,index=options.index(default),key=f"map_{source}")
    if st.button("Normalise, validate and save version"):
        clean=ing.normalise(raw,mapping); problems=ing.validate(clean)
        saved=Path("data/imports")/up.name; saved.parent.mkdir(exist_ok=True); saved.write_bytes(up.getvalue())
        vid=db.save_dataset(clean,up.name,mapping,problems,notes="Imported through Import Centre")
        st.success(f"Saved version {vid}: {len(clean)} records, {len(problems)} validation notices. Original file was kept.")

def dataset_studio(df, version_id):
    header("Dataset Studio","Inspect raw records, cleaning outcomes, validation notes, and persistent version history.","DATA MANAGEMENT")
    if df.empty: empty_data();return
    issues=db.issues_for(version_id);kpis([("Records",len(df),"No records are silently removed"),("Columns",len(df.columns),"Canonical fields"),("Validation notices",len(issues),"Review before interpreting"),("Version",version_id,"Persistent SQLite version")])
    tabs=st.tabs(["Clean records","Missing values","Duplicates","Validation","Corrections","Version history"])
    with tabs[0]: st.dataframe(df,use_container_width=True,height=340);st.download_button("Download cleaned CSV",df.to_csv(index=False),"placementlens_cleaned.csv","text/csv")
    with tabs[1]: st.dataframe(pd.DataFrame({"field":df.columns,"missing":df.isna().sum(),"coverage %":(1-df.isna().mean()).mul(100).round(1)}),use_container_width=True)
    with tabs[2]: st.dataframe(df[df.duplicated(["student_id","year"],keep=False)],use_container_width=True)
    with tabs[3]: st.dataframe(issues if not issues.empty else pd.DataFrame({"status":["No recorded validation notices"]}),use_container_width=True)
    with tabs[4]:
        st.markdown("<div class='panel'><b>Create a corrected child version</b><div class='muted'>Choose an explicit, reversible correction. The current version remains unchanged.</div></div>",unsafe_allow_html=True)
        action=st.selectbox("Correction",["Trim text whitespace","Standardise company capitalization","Remove exact duplicate rows"])
        if st.button("Preview correction"):
            corrected=df.copy()
            if action=="Trim text whitespace":
                for column in corrected.select_dtypes(include="string").columns: corrected[column]=corrected[column].str.strip()
            elif action=="Standardise company capitalization": corrected["company"]=corrected.company.str.strip().str.title()
            else: corrected=corrected.drop_duplicates()
            st.session_state["corrected_preview"]=corrected
            st.info(f"Preview: {len(df)-len(corrected)} row difference. Nothing has been saved yet.")
            st.dataframe(corrected.head(20),use_container_width=True)
        if "corrected_preview" in st.session_state and st.button("Save corrected version"):
            corrected=st.session_state["corrected_preview"]; new_id=db.save_dataset(corrected,f"corrected_v{version_id}_{action.lower().replace(' ','_')}",{},ing.validate(corrected),notes=f"Explicit correction from version {version_id}: {action}")
            del st.session_state["corrected_preview"];st.success(f"Saved immutable corrected version {new_id}.")
    with tabs[5]: st.dataframe(db.versions(),use_container_width=True)

def overview(df, version_id):
    header("Placement Overview","A source-aware overview of student outcomes, salaries, employers and branches.","ANALYSIS")
    if df.empty:empty_data();return
    d=filters(df);m=az.metrics(d);kpis([("Placed",m["placed"],"Students, not offers"),("Placement rate",fmt(m["placement_rate"],"%"),"Only shown with eligible records"),("Median CTC",fmt(m["median"]," LPA"),"Individual CTC records"),("Recruiters",m["recruiters"],"Unique company names")])
    context_bar([("SCOPE","SELECTED RECORDS"),("SALARY DEFINITION","CTC ONLY"),("OUTLIER POLICY","SHOWN, NOT REMOVED"),("VERSION",f"v{version_id}")])
    a,b=st.columns([1.2,1]);
    with a: chart(px.histogram(az.ctc(d),x="salary_lpa",color="branch",title="Salary distribution (CTC, LPA)"))
    with b: chart(bar(az.grouped(d,"branch"),"branch","records","Placement records by branch"))
    a,b=st.columns(2)
    with a:chart(bar(az.grouped(d,"company").head(10),"company","records","Recruiters by placed records"))
    with b:chart(px.line(az.trend(d),x="year",y="median",markers=True,title="Median CTC trend"))

def salary(df, version_id):
    header("Salary Reality Check","Mean, median, quartiles and outliers from individual CTC records. Outliers are retained.","SALARY")
    if df.empty:empty_data();return
    d=az.ctc(filters(df));s=d.salary_lpa;m=az.metrics(d);kpis([("Mean CTC",fmt(s.mean()," LPA"),"Not a typical-value substitute"),("Median CTC",fmt(s.median()," LPA"),"50th percentile"),("25th - 75th",f"{fmt(s.quantile(.25))} - {fmt(s.quantile(.75))} LPA","Middle half"),("Flagged outliers",len(az.outliers(d)),"IQR rule, not removed")])
    context_bar([("POPULATION",f"{len(d)} INDIVIDUAL CTC RECORDS"),("CURRENCY","LPA"),("OUTLIERS","VISIBLE"),("METHOD","QUARTILES + IQR")])
    a,b=st.columns([1.2,1]);
    with a:chart(px.histogram(d,x="salary_lpa",nbins=18,color="branch",title="CTC distribution"))
    with b:chart(px.box(d,y="salary_lpa",x="branch",points="all",title="Salary spread by branch"))
    st.dataframe(az.outliers(d)[["student_id","company","role","salary_lpa","salary_type"]],use_container_width=True)

def coverage_page(df, version_id):
    header("Placement Coverage","Eligible, registered, placed, unplaced and opted-out are kept distinct.","COVERAGE")
    if df.empty:empty_data();return
    d=filters(df);m=az.metrics(d);kpis([("Eligible",m["eligible"] or "Unavailable","Required denominator"),("Placed",m["placed"],"Students"),("Rate",fmt(m["placement_rate"],"%"),"Placed / eligible only"),("Offers",fmt(m["offers"]),"Not counted as students")])
    context_bar([("NUMERATOR","PLACED STUDENTS"),("DENOMINATOR","ELIGIBLE STUDENTS"),("OFFER LOGIC","SEPARATE"),("MISSING DATA","NOT ZERO")])
    a,b=st.columns(2)
    with a:chart(px.funnel(az.coverage(d),x="Students",y="Group",color="Group",title="Student coverage"))
    with b:chart(px.bar(d[d.status.notna()].groupby(["branch","status"]).size().reset_index(name="records"),x="branch",y="records",color="status",barmode="group",title="Outcomes by branch"))

def recruiter(df, version_id):
    header("Recruiter Intelligence","Recruiter activity is based on recorded placement rows and company names.","RECRUITERS")
    if df.empty:empty_data();return
    d=filters(df);g=az.grouped(d,"company");kpis([("Recruiters",g.company.nunique(),"Unique recorded companies"),("Offers",fmt(az.metrics(d)["offers"]),"May exceed placed students"),("Top recruiter",g.iloc[0].company if not g.empty else "Unavailable","By placement records"),("Historical years",d.year.nunique(),"For trend context")])
    context_bar([("UNIT","PLACEMENT ROWS"),("NORMALISATION","SOURCE LABELS RETAINED"),("REPEAT HIRING","YEAR VIEW"),("VERSION",f"v{version_id}")])
    a,b=st.columns([1.25,1]);
    with a:st.dataframe(g.head(20),use_container_width=True)
    with b:chart(bar(g.head(12),"company","records","Recruiter activity"))
    chart(px.line(d[d.company.notna()].groupby(["year","company"]).size().reset_index(name="records"),x="year",y="records",color="company",title="Historical activity by recruiter"))

def company(df, version_id):
    header("Company Insights","Inspect roles, salaries, branches and coverage for a selected employer.","COMPANY")
    if df.empty:empty_data();return
    choices=sorted(df.company.dropna().unique());company_name=st.selectbox("Company",choices) if choices else None
    d=az.ctc(df[df.company==company_name]) if company_name else df.iloc[0:0];m=az.metrics(d);kpis([("Placement records",len(d),"Recorded rows"),("Median CTC",fmt(m["median"]," LPA"),"CTC only"),("Roles",d.role.nunique(),"Distinct role labels"),("Branches",d.branch.nunique(),"Distinct branches")])
    context_bar([("COMPANY",company_name or "UNAVAILABLE"),("SCOPE","RECORDED OFFERS"),("PAY VIEW","CTC ONLY"),("SOURCE","SELECTED VERSION")])
    a,b=st.columns(2)
    with a:chart(bar(az.grouped(d,"role"),"role","records","Roles offered"))
    with b:chart(px.box(d,x="branch",y="salary_lpa",points="all",title="Salary by branch"))

def role(df, version_id):
    header("Role Explorer","Explore recorded role outcomes, skills, employers and salary ranges.","ROLES")
    if df.empty:empty_data();return
    choices=sorted(df.role.dropna().unique());role=st.selectbox("Role",choices) if choices else None;d=az.ctc(df[df.role==role]) if role else df.iloc[0:0]
    m=az.metrics(d);kpis([("Records",len(d),"Individual placement rows"),("Median CTC",fmt(m["median"]," LPA"),"CTC"),("Companies",d.company.nunique(),"Recorded employers"),("Cities",d.city.nunique(),"Recorded locations")])
    context_bar([("ROLE",role or "UNAVAILABLE"),("SCOPE","PLACED RECORDS"),("PAY VIEW","CTC"),("SKILLS","SOURCE-REPORTED")])
    a,b=st.columns(2)
    with a:chart(bar(az.grouped(d,"company"),"company","records","Hiring companies"))
    with b:chart(px.histogram(d,x="salary_lpa",color="branch",title="Salary distribution"))
    st.markdown("**Observed skills:** " + ", ".join(sorted({x.strip() for value in d.skills.dropna() for x in value.split(",")})))

def locations(df, version_id):
    header("Location Insights","Compare recorded hiring cities and countries; no geographic claims are inferred from missing data.","LOCATIONS")
    if df.empty:empty_data();return
    d=az.ctc(filters(df));g=az.grouped(d,"city");kpis([("Cities",d.city.nunique(),"Recorded only"),("Countries",d.country.nunique(),"Recorded only"),("International rows",int((d.country.fillna("India")!="India").sum()),"Based on country field"),("Top city",g.iloc[0].city if not g.empty else "Unavailable","By records")])
    context_bar([("GEOGRAPHY","SOURCE-REPORTED"),("COUNTRY LOGIC","NO INFERENCE"),("PAY VIEW","CTC"),("VERSION",f"v{version_id}")])
    a,b=st.columns(2)
    with a:chart(bar(g,"city","records","Hiring activity by city"))
    with b:chart(px.scatter(d,x="city",y="salary_lpa",color="country",hover_data=["company","role"],title="CTC by location"))

def skills(df, version_id):
    header("Skill & Course Recommendations","Rule-based recommendations from skills attached to recorded placement rows - not forecasts.","SKILLS")
    if df.empty:empty_data();return
    d=az.ctc(filters(df));rows=[]
    for _,r in d.dropna(subset=["skills"]).iterrows():
        for skill in r.skills.split(","): rows.append({"skill":skill.strip(),"salary_lpa":r.salary_lpa,"role":r.role})
    skills_df=pd.DataFrame(rows)
    if skills_df.empty:st.info("No skills field is available in this dataset.");return
    g=skills_df.groupby("skill").agg(mentions=("skill","size"),median_ctc=("salary_lpa","median")).reset_index().sort_values("mentions",ascending=False);kpis([("Observed skills",len(g),"Unique skill labels"),("Most common",g.iloc[0].skill,"By placements"),("Highest median",g.sort_values("median_ctc",ascending=False).iloc[0].skill,"Small samples can mislead"),("Method","Rule-based","No forecast")])
    context_bar([("SKILL SOURCE","PLACEMENT RECORDS"),("RANKING","MENTIONS"),("RECOMMENDATION","RULE-BASED"),("FORECASTS","NOT PRODUCED")])
    a,b=st.columns(2)
    with a:chart(bar(g.head(12),"skill","mentions","In-demand skills by recorded mentions"))
    with b:chart(px.scatter(g,x="mentions",y="median_ctc",text="skill",title="Skill frequency and median CTC"))
    st.info("Learning suggestion: prioritise skills with repeated employer demand, then validate against curriculum needs and sample size.")

def comparator(df, version_id):
    header("Institution Comparator","Compare up to four institutions using compatible values from the selected records.","COMPARISON")
    if df.empty:empty_data();return
    opts=sorted(df.institution.dropna().unique());chosen=st.multiselect("Institutions (up to four)",opts,default=opts[:min(4,len(opts))],max_selections=4)
    records=[]
    for name in chosen:
        m=az.metrics(df[df.institution==name]);records.append({"institution":name,"placement rate":m["placement_rate"],"median CTC":m["median"],"recruiters":m["recruiters"],"placed":m["placed"],"eligible":m["eligible"]})
    comp=pd.DataFrame(records);st.dataframe(comp,use_container_width=True)
    if not comp.empty:
        a,b=st.columns(2)
        with a:chart(px.bar(comp,x="institution",y="median CTC",color="institution",title="Median CTC (compatible CTC records)"))
        with b:chart(px.bar(comp,x="institution",y="placement rate",color="institution",title="Placement rate (only where eligible is known)"))
    st.caption("Blank metrics are intentionally unavailable when compatible source fields do not exist.")

def trends(df, version_id):
    header("Trends & Stability","Historical descriptions only. PlacementLens does not create unsupported forecasts.","TRENDS")
    if df.empty:empty_data();return
    t=az.trend(filters(df));
    if t.empty:st.info("A year field is needed for historical trends.");return
    kpis([("Years",len(t),"Comparable years"),("Latest rate",fmt(t.iloc[-1].placement_rate,"%"),"When denominator exists"),("Latest median",fmt(t.iloc[-1].median," LPA"),"CTC only"),("Latest recruiters",fmt(t.iloc[-1].recruiters),"Unique recorded companies")])
    a,b=st.columns(2)
    with a:chart(px.line(t,x="year",y="placement_rate",markers=True,title="Placement rate"))
    with b:chart(px.line(t,x="year",y="median",markers=True,title="Median CTC"))
    chart(px.line(t,x="year",y=["recruiters","offers"],markers=True,title="Recruiters and offers (separate concepts)"))

def evidence_page(df, version_id):
    header("Evidence & Data Quality","Show what supports an insight, what is missing, and where comparison is limited.","EVIDENCE")
    if df.empty:empty_data();return
    e=az.evidence(df);issues=db.issues_for(version_id);kpis([("Records",len(df),"Dataset version"),("Average coverage",f"{e.coverage.mean():.1f}%","Selected analytical fields"),("Validation notices",len(issues),"Not silently repaired"),("Source label",str(df.source.dropna().iloc[0]) if df.source.notna().any() else "Unavailable","Record source")])
    a,b=st.columns(2)
    with a:chart(px.bar(e,x="field",y="coverage",color="field",title="Field completeness (%)"))
    with b:st.dataframe(issues if not issues.empty else pd.DataFrame({"status":["No notices recorded"]}),use_container_width=True)
    claims=db.source_claims(version_id)
    with st.expander("Source register and verification notes",expanded=True):
        st.dataframe(claims if not claims.empty else pd.DataFrame({"status":["No source claims logged for this version yet."]}),use_container_width=True)
        x,y,z=st.columns([1,2,1]);field=x.selectbox("Field",list(df.columns));note=y.text_input("Evidence note",placeholder="e.g. Official placement report, page 12");reliability=z.selectbox("Reliability",["Unverified","Reported","Verified","Conflicting"])
        if st.button("Add source claim"):
            if note.strip(): db.add_source_claim(version_id,field,note.strip(),reliability);st.success("Source claim added.");st.rerun()
            else: st.error("Add a short evidence note before saving.")
    st.markdown("**Methodology:** calculations use the selected persisted version. Missing values stay missing; CTC is not mixed with other compensation types; outliers are shown, not removed.")

def reports(df, version_id):
    header("Report Builder & History","Create a local evidence-labelled PDF or download the selected data as CSV.","REPORTS")
    if df.empty:empty_data();return
    title=st.text_input("Report title","PlacementLens evidence report")
    a,b=st.columns(2)
    if a.button("Generate PDF report",use_container_width=True):
        try:
            path=reporting.report_pdf(df,version_id,title);db.log_report(version_id,path.name,str(path),"PDF");st.success("Local PDF report created.");st.download_button("Download report",path.read_bytes(),path.name,"application/pdf")
        except RuntimeError as exc: st.error(str(exc))
    b.download_button("Download selected CSV",df.to_csv(index=False),"placementlens_export.csv","text/csv",use_container_width=True)
    history=db.report_history();st.dataframe(history if not history.empty else pd.DataFrame({"status":["No reports created yet"]}),use_container_width=True)

def settings(df, version_id):
    header("Settings & Methodology","Local workspace preferences and the definitions used throughout PlacementLens.","SYSTEM")
    st.selectbox("Currency display",["INR (LPA)","Local source units"]);st.selectbox("Default view",["Placement Overview","Dataset Studio","Evidence & Data Quality"]);st.toggle("Show percentages",True)
    st.subheader("Metric definitions")
    st.markdown("- **Placement rate:** placed students divided by eligible students only when both fields are compatible.\n- **Median CTC:** midpoint of individual CTC records; no aggregate salary is converted into records.\n- **Offers:** a count of offers and never a substitute for placed students.\n- **Comparisons:** blank/unavailable values mean the source does not support a compatible calculation.")
    st.subheader("Limitations")
    st.write("This local analytical tool depends on imported evidence. It is not an official ranking, accreditation system, or forecasting service.")
