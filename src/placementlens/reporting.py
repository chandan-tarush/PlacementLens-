"""Simple evidence-labelled local exports."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from .analysis import metrics

ROOT=Path(__file__).resolve().parents[2]
def report_pdf(df, version_id, title="PlacementLens evidence report"):
    """Create a PDF when ReportLab is installed; the app stays usable without it."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("PDF export needs ReportLab. Install requirements.txt in the active Python environment.") from exc
    folder=ROOT/"data"/"reports"; folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"placementlens_{datetime.now():%Y%m%d_%H%M%S}.pdf"; c=canvas.Canvas(str(path),pagesize=A4); width,height=A4
    c.setFillColor(colors.HexColor("#07111F"));c.rect(0,0,width,height,fill=1,stroke=0);c.setFillColor(colors.HexColor("#19D3C5"));c.setFont("Helvetica-Bold",20);c.drawString(48,height-60,"PlacementLens")
    c.setFillColor(colors.white);c.setFont("Helvetica-Bold",15);c.drawString(48,height-90,title);c.setFont("Helvetica",9);c.setFillColor(colors.HexColor("#B9C6D2"));c.drawString(48,height-110,"Local analytical report. Figures are calculated from the selected dataset and are not official rankings.")
    y=height-150; m=metrics(df)
    for label,key in [("Records","records"),("Placed students","placed"),("Eligible students","eligible"),("Placement rate","placement_rate"),("Median CTC (LPA)","median"),("Recruiters","recruiters")]:
        value=m[key]; display="Unavailable" if value is None else (f"{value:.1f}%" if key=="placement_rate" else f"{value:.2f}" if key=="median" else str(value));c.setFillColor(colors.HexColor("#19D3C5"));c.setFont("Helvetica-Bold",10);c.drawString(52,y,label);c.setFillColor(colors.white);c.drawRightString(350,y,display);y-=25
    c.setFillColor(colors.HexColor("#B9C6D2"));c.setFont("Helvetica",9);c.drawString(48,y-15,"Evidence notes: missing data is excluded from relevant calculations; offers are not treated as placed students.");c.drawString(48,y-32,f"Dataset version: {version_id} | Generated: {datetime.now():%Y-%m-%d %H:%M}");c.save();return path
