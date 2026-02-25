"""
pages/tab3_patientes.py — Onglet 3 : Les Patientes (profil démographique).

Layout:
  - Col-left: pyramide des âges nationale (année from slider)
  - Col-right: ranking part mineures (<18) par département
  - Compact bottom: trend national part mineures (2016-2024)
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data.cache import DATA
from components.kpi_cards import kpi_card, kpi_row

_nat_age = DATA["nat_age"]
_nat_min = DATA["nat_mineures"]
_mineures = DATA["mineures"]

AGE_LABELS = ["<18", "18-19", "20-24", "25-29", "30-34", "35-39", "40+"]
PCT_COLS = ["pct_inf18", "pct_18_19", "pct_20_24", "pct_25_29",
            "pct_30_34", "pct_35_39", "pct_40plus"]
AGE_COLORS = ["#e74c3c", "#e67e22", "#f39c12", "#27ae60", "#2980b9", "#8e44ad", "#2c3e50"]


def build_pyramid(year):
    """Build horizontal bar chart as age pyramid for a given year."""
    row = _nat_age[_nat_age["annee"] == year]
    if row.empty:
        return go.Figure().update_layout(title="Données non disponibles")

    r = row.iloc[0]
    vals = [r.get(c, 0) for c in PCT_COLS]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=AGE_LABELS, x=vals,
        orientation="h",
        marker_color=AGE_COLORS,
        text=[f"{v:.1f}%" for v in vals],
        textposition="outside",
        hovertemplate="<b>%{y}</b> : %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Profil d'âge national — {year}", font=dict(size=14)),
        xaxis=dict(title="Part (%)", range=[0, max(vals) * 1.3]),
        height=380, margin=dict(l=60, r=30, t=40, b=30),
        showlegend=False,
    )
    return fig


def build_mineures_ranking(year, zone="all", n=20):
    """Build ranking of departments by share of <18 year olds."""
    df = _mineures[(_mineures["annee"] == year) & (_mineures["is_dept"])].copy()
    if df.empty:
        return go.Figure()

    # Add is_drom info
    lookup = DATA["dep_lookup"]
    df = df.merge(lookup[["dep_nom", "is_drom"]], left_on="zone_geo", right_on="dep_nom", how="left")

    if zone == "metro":
        df = df[df["is_drom"] != True]
    elif zone == "drom":
        df = df[df["is_drom"] == True]

    top = df.nlargest(n, "part_mineures")
    top = top.sort_values("part_mineures", ascending=True)

    colors = top["is_drom"].map({True: "#e67e22", False: "#e74c3c"}).fillna("#e74c3c")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["zone_geo"], x=top["part_mineures"],
        orientation="h", marker_color=colors,
        text=top["part_mineures"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b> : %{x:.1f}%<extra></extra>",
    ))

    # France average line
    fr_val = _nat_min[_nat_min["annee"] == year]["part_mineures"].values
    if len(fr_val) > 0:
        fig.add_vline(x=fr_val[0], line_dash="dash", line_color="#3498db",
                      annotation_text=f"France {fr_val[0]:.1f}%",
                      annotation_font_size=9)

    fig.update_layout(
        title=dict(text=f"Part mineures (<18 ans) — Top {n} — {year}", font=dict(size=13)),
        height=max(350, len(top) * 20),
        margin=dict(l=160, r=40, t=35, b=25),
        showlegend=False, xaxis_title="%",
    )
    return fig


def build_trend_mineures():
    """National trend of the share of <18 year olds in IVG."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_nat_min["annee"], y=_nat_min["part_mineures"],
        mode="lines+markers", line=dict(color="#e74c3c", width=2.5),
        marker=dict(size=5),
        hovertemplate="%{x} : %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Évolution nationale — Part mineures (<18 ans)", font=dict(size=13)),
        yaxis_title="%", xaxis_title=None,
        height=230, margin=dict(l=45, r=20, t=35, b=25),
        showlegend=False,
    )
    return fig


def layout():
    # Latest values for KPI
    latest = _nat_min.iloc[-1] if not _nat_min.empty else None
    first = _nat_min.iloc[0] if not _nat_min.empty else None

    kpis = []
    if latest is not None and first is not None:
        kpis = kpi_row([
            kpi_card(f"{latest['part_mineures']:.1f}%",
                     f"Part mineures {int(latest['annee'])}",
                     f"vs {first['part_mineures']:.1f}% en {int(first['annee'])}", "down"),
            kpi_card(f"{_nat_age.iloc[-1]['pct_25_29']:.0f}%",
                     f"Tranche modale (25-29 ans) {int(_nat_age.iloc[-1]['annee'])}"),
        ])

    return html.Div([
        kpis,
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="pyramid-chart", config={"displayModeBar": False}),
            ], md=6),
            dbc.Col([
                dcc.Graph(id="mineures-ranking", config={"displayModeBar": False}),
            ], md=6),
        ], className="mb-3"),

        # Compact bottom
        dcc.Graph(id="mineures-trend",
                  figure=build_trend_mineures(),
                  config={"displayModeBar": False}),
    ])
