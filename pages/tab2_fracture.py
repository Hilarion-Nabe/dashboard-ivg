"""
pages/tab2_fracture.py — Onglet 2 : La Fracture (territoires).

Layout:
  - Col-left: carte choroplèthe taux de recours (année from slider)
  - Col-right: ranking top/bottom or deserts KPI
  - Micro-guide: "Cliquez sur un département pour voir son profil"
  - Drill-down triggered via clickData callback in app.py
"""

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.cache import DATA

_dep2023 = DATA["dep_2023"]
_dep_year = DATA["dep_year"]
_geojson = DATA["geojson"]
_deserts = DATA["deserts"]
_dep_lookup = DATA["dep_lookup"]

# Available years for the choropleth (dep_year covers 2016-2022, dep_2023 gives 2023)
_YEARS_MAP = sorted(_dep_year["annee"].unique()) + [2023]


def _build_choropleth(year, zone="all"):
    """Build choropleth for a given year."""
    if year == 2023:
        df = _dep2023[["dep_code", "dep_nom", "taux_2023", "is_drom"]].copy()
        df = df.rename(columns={"taux_2023": "taux_recours"})
    else:
        df = _dep_year[_dep_year["annee"] == year][
            ["dep_code", "dep_nom", "taux_recours", "is_drom"]
        ].copy()

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Pas de données départementales pour {year}<br><br>"
                 f"<span style='font-size:12px;color:gray'>"
                 f"La carte couvre 2016–2023.<br>Les feuilles nationales (âge, mineures, praticiens) couvrent 2016–2024.</span>",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#2c3e50"),
            align="center",
        )
        fig.update_layout(
            height=480, margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            plot_bgcolor="white",
        )
        return fig

    # Zone filter
    if zone == "metro":
        df = df[~df["is_drom"]]
    elif zone == "drom":
        df = df[df["is_drom"]]

    # Build choropleth using Plotly Express
    fig = px.choropleth_mapbox(
        df,
        geojson=_geojson,
        locations="dep_code",
        color="taux_recours",
        featureidkey="id",
        hover_name="dep_nom",
        hover_data={"taux_recours": ":.1f", "dep_code": False},
        color_continuous_scale="Blues",
        range_color=[df["taux_recours"].quantile(0.05), df["taux_recours"].quantile(0.95)],
        labels={"taux_recours": "Taux ‰"},
        mapbox_style="white-bg",
    )

    # Center on France or DROM
    if zone == "drom":
        fig.update_layout(mapbox=dict(center=dict(lat=-15, lon=-55), zoom=2.5))
    else:
        fig.update_layout(mapbox=dict(center=dict(lat=46.6, lon=2.5), zoom=4.8))

    fig.update_layout(
        title=dict(text=f"Taux de recours ‰ — {year}", font=dict(size=14)),
        height=480, margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="‰", thickness=15, len=0.6),
    )
    return fig


def _build_ranking(year, zone="all", n=15):
    """Build top/bottom ranking bar chart for a given year."""
    if year == 2023:
        df = _dep2023[["dep_code", "dep_nom", "taux_2023", "is_drom"]].copy()
        df = df.rename(columns={"taux_2023": "taux_recours"})
    else:
        df = _dep_year[_dep_year["annee"] == year][
            ["dep_code", "dep_nom", "taux_recours", "is_drom"]
        ].copy()

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"Pas de données pour {year}",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(height=350, xaxis=dict(visible=False), yaxis=dict(visible=False),
                          plot_bgcolor="white")
        return fig

    if zone == "metro":
        df = df[~df["is_drom"]]
    elif zone == "drom":
        df = df[df["is_drom"]]

    # Top N + Bottom N
    top = df.nlargest(n, "taux_recours")
    bottom = df.nsmallest(n, "taux_recours")
    display = pd.concat([top, bottom]).drop_duplicates(subset=["dep_code"])
    display = display.sort_values("taux_recours", ascending=True)

    colors = display["is_drom"].map({True: "#e67e22", False: "#3498db"})
    mediane = df["taux_recours"].median()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=display["dep_nom"], x=display["taux_recours"],
        orientation="h", marker_color=colors,
        text=display["taux_recours"].apply(lambda v: f"{v:.1f} ‰"),
        textposition="outside",
        hovertemplate="<b>%{y}</b> : %{x:.1f} ‰<extra></extra>",
        customdata=display["dep_code"],
    ))
    fig.add_vline(x=mediane, line_dash="dash", line_color="#e74c3c", line_width=1,
                  annotation_text=f"Méd. {mediane:.1f}", annotation_font_size=9)

    fig.update_layout(
        title=dict(text=f"Top/Bottom {n} — {year}", font=dict(size=13)),
        height=max(350, len(display) * 18),
        margin=dict(l=150, r=40, t=35, b=25),
        showlegend=False,
        xaxis_title="Taux ‰",
    )
    return fig


def layout():
    return html.Div([
        dbc.Row([
            # Left: Choropleth map
            dbc.Col([
                html.Div("Taux de recours par département", className="section-title"),
                html.Div("‰ femmes 15-49 ans · cliquez sur un département", className="section-subtitle"),
                dcc.Graph(id="map-choropleth", config={"displayModeBar": False}),
                html.P("Cliquez sur un département pour voir son profil.", className="micro-guide"),
            ], md=7),

            # Right: Ranking
            dbc.Col([
                html.Div("Classement", className="section-title"),
                html.Div("Top/Bottom 15 départements", className="section-subtitle"),
                dcc.Graph(id="ranking-chart", config={"displayModeBar": False}),
            ], md=5),
        ]),
    ])
