"""
pages/tab4_offre.py — Onglet 4 : L'Offre de soins.

Layout:
  - KPI row: charge moyenne, total praticiens, ×2.5 en 8 ans, SF de 0.6→41%
  - Graph principal: 100% stacked area GO/MG/SF (2016-2024)
  - Col-right or bottom: ranking "déserts" (0-5 praticiens par département)
  - Micro-guide: NaN = absence de praticien de ce type
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data.cache import DATA
from components.kpi_cards import kpi_card, kpi_row

_nat_prat = DATA["nat_prat"]
_charge = DATA["charge"]
_deserts = DATA["deserts"]
_praticiens = DATA["praticiens"]


def _fig_stacked_100():
    """100% stacked area: GO / MG / SF share over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_sf"],
        mode="lines", stackgroup="one", groupnorm="percent",
        name="Sages-femmes (SF)",
        line=dict(width=0.5, color="#27ae60"),
        fillcolor="rgba(39,174,96,0.7)",
        hovertemplate="%{x} : %{y:.1f}%<extra>SF</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_mg"],
        mode="lines", stackgroup="one",
        name="Médecins généralistes (MG)",
        line=dict(width=0.5, color="#2980b9"),
        fillcolor="rgba(41,128,185,0.7)",
        hovertemplate="%{x} : %{y:.1f}%<extra>MG</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_go"],
        mode="lines", stackgroup="one",
        name="Gynécologues-obst. (GO)",
        line=dict(width=0.5, color="#e74c3c"),
        fillcolor="rgba(231,76,60,0.6)",
        hovertemplate="%{x} : %{y:.1f}%<extra>GO</extra>",
    ))
    fig.update_layout(
        title=dict(text="Recomposition de l'offre — Part par profession (%)",
                   font=dict(size=14)),
        yaxis=dict(title="Part (%)", ticksuffix="%", range=[0, 100]),
        xaxis_title=None,
        height=420, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.12),
        hovermode="x unified",
    )
    return fig


def build_deserts_ranking(year):
    """Bar chart of departments with ≤ 5 practitioners."""
    df = _deserts[_deserts["annee"] == year].copy()
    if df.empty:
        return go.Figure().update_layout(
            title="Aucun département avec ≤ 5 praticiens cette année",
            height=250,
        )

    df = df.sort_values("total_prat", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["zone_geo"], x=df["total_prat"],
        orientation="h",
        marker_color="#e74c3c",
        text=df["total_prat"].astype(int).astype(str) + " prat.",
        textposition="outside",
        hovertemplate="<b>%{y}</b> : %{x:.0f} praticiens<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Déserts IVG — Départements ≤ 5 praticiens ({year})",
                   font=dict(size=13)),
        height=max(250, len(df) * 25),
        margin=dict(l=160, r=40, t=35, b=25),
        showlegend=False,
        xaxis=dict(title="Praticiens libéraux", dtick=1),
    )
    return fig


def layout():
    # Latest year values for KPIs
    latest = _nat_prat.iloc[-1] if not _nat_prat.empty else None
    first = _nat_prat.iloc[0] if not _nat_prat.empty else None
    latest_charge = _charge.iloc[-1] if not _charge.empty else None

    kpis = []
    if latest is not None and first is not None:
        multiplier = latest["total_prat"] / first["total_prat"] if first["total_prat"] > 0 else 0
        charge_val = f"{latest_charge['charge_moyenne']:.0f}" if latest_charge is not None else "N/A"

        kpis = kpi_row([
            kpi_card(f"{int(latest['total_prat']):,}".replace(",", " "),
                     f"Praticiens IVG {int(latest['annee'])}",
                     f"×{multiplier:.1f} depuis {int(first['annee'])}", "up"),
            kpi_card(f"{latest['pct_sf']:.0f}%",
                     f"Part sages-femmes {int(latest['annee'])}",
                     f"vs {first['pct_sf']:.0f}% en {int(first['annee'])}", "up"),
            kpi_card(charge_val,
                     f"Charge moy. IVG/praticien",
                     "Total IVG ÷ total praticiens", "neutral"),
        ])

    return html.Div([
        kpis,
        dbc.Row([
            # Left: 100% stacked practitioners
            dbc.Col([
                dcc.Graph(figure=_fig_stacked_100(), config={"displayModeBar": False}),
            ], md=7),

            # Right: deserts ranking (latest year)
            dbc.Col([
                dcc.Graph(id="deserts-ranking", config={"displayModeBar": False}),
                html.P("NaN = absence de praticien de ce type dans le département.",
                       className="micro-guide"),
            ], md=5),
        ]),
    ])
