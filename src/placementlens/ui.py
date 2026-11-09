"""Shared Streamlit styling and chart helpers."""
from __future__ import annotations
import streamlit as st
import plotly.express as px

COLORS=["#19D3C5","#35BDEB","#9365E8","#36C99A","#F2B84B","#FF6B7A","#4285F4"]
def style():
    st.set_page_config(page_title="PlacementLens",page_icon="assets/placementlens-mark.png",layout="wide",initial_sidebar_state="expanded")
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    .stApp{background:#07111F;color:#EDF4FA;font-family:Manrope,Arial,sans-serif}.stSidebar{background:#081522;border-right:1px solid #19364A}.block-container{padding:1.2rem 2rem 2.5rem;max-width:1540px}.panel{background:linear-gradient(145deg,#0D1B2A,#0A1725);border:1px solid #19364A;border-radius:12px;padding:16px;margin:0 0 14px}.eyebrow{color:#19D3C5;font-size:.7rem;letter-spacing:.14em;font-weight:800;margin-bottom:5px}.title{font-size:2.05rem;font-weight:800;letter-spacing:-.055em;line-height:1.05;margin-bottom:4px}.muted{color:#9AABBC;font-size:.92rem}.topbar{display:flex;align-items:center;justify-content:space-between;background:#081522;border:1px solid #19364A;border-radius:11px;padding:10px 14px;margin-bottom:20px}.topbar strong{font-size:.9rem}.status{font-family:'DM Mono',monospace;font-size:.68rem;color:#19D3C5;background:#0C282B;border:1px solid #176158;border-radius:20px;padding:5px 9px}.micro{font-size:.72rem;color:#9AABBC}.stButton>button{background:#19D3C5;color:#031019;border:0;border-radius:7px;font-weight:800;min-height:38px;transition:background .2s ease,filter .2s ease}.stButton>button:hover{background:#57e2d7;color:#031019;filter:brightness(1.04)}.stMetric{background:#0D1B2A;border:1px solid #19364A;padding:13px;border-radius:10px}.stMetric label{font-size:.72rem!important;color:#9AABBC!important}.stMetric [data-testid='stMetricValue']{font-size:1.35rem}.stTabs [data-baseweb="tab-list"]{gap:2px;background:#081522;border:1px solid #19364A;border-radius:9px;padding:3px}.stTabs [data-baseweb="tab"]{color:#9AABBC;border-radius:6px;padding:8px 15px}.stTabs [aria-selected="true"]{color:#19D3C5!important;background:#0D2D31!important}.stDataFrame{border:1px solid #19364A;border-radius:9px}div[data-testid="stSidebar"] .stRadio label{font-size:.88rem;padding:4px 0}div[data-testid="stSidebar"] .stRadio [data-checked="true"]+div{color:#19D3C5;font-weight:700}#MainMenu,footer{visibility:hidden}@media(max-width:700px){.block-container{padding:1rem}.title{font-size:1.65rem}}
    .contextbar{display:flex;gap:1px;background:#19364A;border:1px solid #19364A;border-radius:9px;overflow:hidden;margin:0 0 14px}.contextbar span{flex:1;background:#0D1B2A;padding:8px 11px}.contextbar b{display:block;color:#9AABBC;font-size:.67rem;font-weight:600}.contextbar small{font-family:'DM Mono',monospace;color:#EDF4FA;font-size:.73rem}.stPlotlyChart{background:#0D1B2A;border:1px solid #19364A;border-radius:11px;padding:5px}.stSelectbox label,.stMultiSelect label{font-size:.72rem!important;color:#9AABBC!important}.stAlert{border-radius:9px}
    </style>""",unsafe_allow_html=True)
def header(title, subtitle, kicker="ANALYSIS"):
    st.markdown(f"<div class='eyebrow'>{kicker}</div><div class='title'>{title}</div><div class='muted'>{subtitle}</div><div style='height:18px'></div>",unsafe_allow_html=True)
def topbar(dataset_label="No dataset selected", synthetic=False):
    tag="DEMONSTRATION DATA" if synthetic else "LOCAL WORKSPACE"
    st.markdown(f"<div class='topbar'><strong>PLACEMENT<span style='color:#19D3C5'>LENS</span></strong><span class='micro'>Evidence-first placement intelligence</span><span class='status'>{tag} · {dataset_label}</span></div>",unsafe_allow_html=True)
def chart(fig):
    fig.update_layout(template="plotly_dark",paper_bgcolor="#0D1B2A",plot_bgcolor="#0D1B2A",font_color="#DDEAF4",margin=dict(l=12,r=12,t=40,b=12),colorway=COLORS,legend=dict(orientation="h",y=1.12,x=0,font=dict(size=10)),title=dict(font=dict(size=13,color="#EDF4FA"),x=.02),hoverlabel=dict(bgcolor="#081522",font_color="#EDF4FA"))
    fig.update_xaxes(showgrid=False,zeroline=False,tickfont=dict(size=10,color="#9AABBC"),title_font=dict(size=10,color="#9AABBC"))
    fig.update_yaxes(gridcolor="#19364A",zeroline=False,tickfont=dict(size=10,color="#9AABBC"),title_font=dict(size=10,color="#9AABBC"))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False,"responsive":True})
def empty_data(): st.info("Import a CSV/XLSX file or load the clearly labelled demonstration dataset to unlock this analysis.")
def kpis(items):
    cols=st.columns(len(items))
    for col,(label,value,help_text) in zip(cols,items): col.metric(label,value,help=help_text)
def context_bar(items):
    cells="".join(f"<span><b>{label}</b><small>{value}</small></span>" for label,value in items)
    st.markdown(f"<div class='contextbar'>{cells}</div>",unsafe_allow_html=True)
def bar(data,x,y,title=""):
    return px.bar(data,x=x,y=y,title=title,color=x,color_discrete_sequence=COLORS)
