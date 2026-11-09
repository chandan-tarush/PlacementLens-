"""Evidence-aware calculations. Empty values mean unavailable, never zero."""
from __future__ import annotations
import numpy as np
import pandas as pd

def ctc(df): return df.loc[(df.status == "Placed") & (df.salary_type.fillna("CTC").str.upper() == "CTC") & df.salary_lpa.notna()].copy()
def metrics(df):
    placed=df[df.status=="Placed"]; salaries=ctc(df).salary_lpa
    eligible=df.eligible.dropna() if "eligible" in df else pd.Series(dtype=bool)
    denominator=int(eligible.sum()) if not eligible.empty else None
    placed_students=placed.student_id.nunique() if placed.student_id.notna().any() else len(placed)
    return {"records":len(df),"placed":placed_students,"eligible":denominator,"placement_rate":(placed_students/denominator*100 if denominator else None),"offers":pd.to_numeric(placed.offers,errors="coerce").sum(min_count=1),"recruiters":placed.company.nunique(),"median":salaries.median() if not salaries.empty else None,"mean":salaries.mean() if not salaries.empty else None,"salary_count":len(salaries)}
def grouped(df, by, value="salary_lpa"):
    d=ctc(df).dropna(subset=[by]); return d.groupby(by,dropna=True).agg(records=("student_id","size"),median=(value,"median"),average=(value,"mean"),offers=("offers","sum")).reset_index().sort_values("records",ascending=False)
def outliers(df):
    d=ctc(df); s=d.salary_lpa
    if len(s)<4:return d.iloc[0:0]
    q1,q3=s.quantile([.25,.75]); return d[(s<q1-1.5*(q3-q1))|(s>q3+1.5*(q3-q1))]
def coverage(df):
    labels={"Eligible":df.eligible.sum() if df.eligible.notna().any() else np.nan,"Registered":df.registered.sum() if df.registered.notna().any() else np.nan,"Placed":(df.status=="Placed").sum(),"Unplaced":(df.status=="Unplaced").sum(),"Opted out":df.opted_out.sum() if df.opted_out.notna().any() else np.nan}
    return pd.DataFrame({"Group":labels.keys(),"Students":labels.values()}).dropna()
def trend(df):
    rows=[]
    for year,part in df.dropna(subset=["year"]).groupby("year"):
        m=metrics(part); rows.append({"year":int(year),"placement_rate":m["placement_rate"],"median":m["median"],"recruiters":m["recruiters"],"offers":m["offers"]})
    return pd.DataFrame(rows).sort_values("year") if rows else pd.DataFrame()
def evidence(df):
    total=max(len(df),1); fields=["institution","year","status","company","role","salary_lpa","city","skills"]
    return pd.DataFrame({"field":fields,"coverage":[round(df[x].notna().mean()*100,1) for x in fields],"missing":[int(df[x].isna().sum()) for x in fields],"records":len(df)})
