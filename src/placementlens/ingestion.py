"""Import, map, normalise and validate placement tables."""
from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd

CANONICAL = ["student_id", "institution", "year", "branch", "programme", "status", "eligible", "registered",
             "opted_out", "company", "role", "salary_lpa", "salary_type", "offers", "city", "country", "skills", "source"]
ALIASES = {"student_id": ["student", "roll", "id", "roll no"], "institution": ["college", "institute", "institution"],
"year": ["year", "batch", "session"], "branch": ["branch", "department"], "programme": ["program", "course", "degree"],
"status": ["status", "placement status"], "company": ["company", "recruiter", "employer"], "role": ["role", "designation", "job title"],
"salary_lpa": ["salary", "ctc", "package", "lpa"], "salary_type": ["salary type", "compensation type"],
"offers": ["offer", "offers"], "city": ["city", "location"], "country": ["country"], "skills": ["skills", "skill"],
"eligible": ["eligible"], "registered": ["registered"], "opted_out": ["opted out", "optout"], "source": ["source", "evidence"]}

def read_file(uploaded) -> pd.DataFrame:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".csv": return pd.read_csv(uploaded)
    if suffix in {".xlsx", ".xls"}: return pd.read_excel(uploaded)
    raise ValueError("Use a CSV or Excel (.xlsx/.xls) file.")

def suggest_mapping(columns) -> dict:
    result = {}
    for col in columns:
        text = str(col).lower().replace("_", " ")
        for target, terms in ALIASES.items():
            if any(term in text for term in terms): result[str(col)] = target; break
    return result

def normalise(raw: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    df = pd.DataFrame(index=raw.index)
    reverse = {target: source for source, target in mapping.items() if target and target != "Ignore"}
    for field in CANONICAL:
        df[field] = raw[reverse[field]] if field in reverse else pd.NA
    for col in ["institution","branch","programme","company","role","city","country","skills","source","salary_type"]:
        df[col] = df[col].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA})
    df["year"] = pd.to_numeric(df["year"].astype(str).str.extract(r"(20\d{2})")[0], errors="coerce").astype("Int64")
    df["salary_lpa"] = pd.to_numeric(df["salary_lpa"].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
    df["offers"] = pd.to_numeric(df["offers"], errors="coerce")
    for col in ["eligible","registered","opted_out"]:
        df[col] = df[col].astype(str).str.lower().isin(["true","yes","1","y"]).where(df[col].notna(), pd.NA)
    status = df["status"].astype(str).str.lower()
    df["status"] = np.select([status.str.contains("place|offer|selected"), status.str.contains("unplace|not placed")], ["Placed", "Unplaced"], default=pd.NA)
    df.loc[df["salary_type"].isna() & df["salary_lpa"].notna(), "salary_type"] = "CTC"
    return df

def validate(df: pd.DataFrame) -> list[dict]:
    issues=[]
    required=["institution","year","status"]
    for field in required:
        missing=df[field].isna()
        if missing.any(): issues.append({"severity":"Warning","field":field,"message":f"{missing.sum()} records have no {field}.","row":0})
    if df.duplicated(subset=["student_id","year"], keep=False).any(): issues.append({"severity":"Warning","field":"student_id","message":"Possible duplicate student/year records retained for review.","row":0})
    bad=(df.salary_lpa.notna()) & ((df.salary_lpa <= 0) | (df.salary_lpa > 500))
    if bad.any(): issues.append({"severity":"Warning","field":"salary_lpa","message":"Salary values outside 0-500 LPA were retained and flagged.","row":0})
    mixed=df.salary_type.dropna().nunique()>1
    if mixed: issues.append({"severity":"Info","field":"salary_type","message":"More than one compensation type exists; salary views only use CTC.","row":0})
    return issues

def demo_data() -> pd.DataFrame:
    rng=np.random.default_rng(42); n=180
    companies=np.array(["Aster Labs","Vertex Systems","Northstar Analytics","Bluewave Cloud","Cedar Financial","Nexus Health"])
    roles=np.array(["Software Engineer","Data Analyst","Data Scientist","Cloud Engineer","Product Analyst","Core Engineer"])
    branches=np.array(["Computer Science","Information Technology","Electronics","Mechanical"])
    institutions=np.array(["Northbridge Institute","Harbor Technical University","Summit College of Engineering","Lakeside University"])
    years=rng.choice([2021,2022,2023,2024],n); placed=rng.random(n)<.78; salary=np.where(placed, np.clip(rng.lognormal(2.75,.42,n),4,45), np.nan)
    return pd.DataFrame({"student_id":[f"DEMO-{i:03d}" for i in range(n)],"institution":rng.choice(institutions,n),"year":years,"branch":rng.choice(branches,n),"programme":"B.Tech","status":np.where(placed,"Placed","Unplaced"),"eligible":True,"registered":rng.random(n)<.92,"opted_out":rng.random(n)<.06,"company":np.where(placed,rng.choice(companies,n),pd.NA),"role":np.where(placed,rng.choice(roles,n),pd.NA),"salary_lpa":salary,"salary_type":np.where(placed,"CTC",pd.NA),"offers":np.where(placed,rng.integers(1,3,n),pd.NA),"city":np.where(placed,rng.choice(["Bengaluru","Hyderabad","Pune","Mumbai","Chennai"],n),pd.NA),"country":np.where(placed,"India",pd.NA),"skills":rng.choice(["Python, SQL, Git","Python, Statistics, SQL","Java, DSA, Git","Cloud, Linux, Python"],n),"source":"Synthetic demonstration dataset"})
