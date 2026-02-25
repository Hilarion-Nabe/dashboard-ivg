"""
pages/tab1_constat.py — Onglet 1 : Le Constat (urgence nationale).

Layout:
  - Row KPI cards (Total IVG, Taux ‰, ICA, Part médicamenteux)
  - Row: col-left = trend total IVG 1990-2023 | col-right = stacked area modalités
  - Row compact: taux + ICA double axe
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data.cache import DATA
from components.kpi_cards import kpi_card, kpi_row

# ── Pre-build static figures (no callback needed for this tab) ──

_ts = DATA["national_ts"]
_taux = DATA["national_taux"]
_meth = DATA["methodes"]

# Latest values for KPIs
_latest_ts = _ts.iloc[-1]
_latest_taux = _taux.iloc[-1]
_latest_meth = _meth.iloc[-1]


def _fig_trend():
    """Total IVG 1990-2023 with COVID band."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_ts["annee"], y=_ts["total_brut"],
        mode="lines+markers", name="Total IVG (brut)",
        line=dict(color="#2c3e50", width=2.5), marker=dict(size=4),
        hovertemplate="%{x} : %{y:,.0f}<extra></extra>",
    ))
    # Sans reprises (available from ~2016)
    sr = _ts.dropna(subset=["total_sans_reprises"])
    if not sr.empty:
        fig.add_trace(go.Scatter(
            x=sr["annee"], y=sr["total_sans_reprises"],
            mode="lines", name="Sans reprises",
            line=dict(color="#95a5a6", width=1.5, dash="dash"),
        ))
    # COVID band
    fig.add_vrect(x0=2019.5, x1=2021.5,
                  fillcolor="rgba(200,200,200,0.2)", line_width=0,
                  annotation_text="COVID", annotation_position="top left",
                  annotation_font=dict(size=9, color="gray"))
    fig.update_layout(
        title=dict(text="Total IVG — France (1990–2023)", font=dict(size=14)),
        yaxis_title="Nombre d'IVG", xaxis_title=None,
        height=380, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.12),
        hovermode="x unified",
    )
    return fig


def _fig_stacked():
    """Stacked area : hors étab / instrumentale / médicamenteuse en étab."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["hors_etab"],
        mode="lines", stackgroup="one", name="Hors établissement",
        line=dict(color="#2ecc71", width=0.5),
        fillcolor="rgba(46,204,113,0.6)",
        hovertemplate="%{y:,.0f}<extra>Hors étab.</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["medic_etab"],
        mode="lines", stackgroup="one", name="Médicamenteuse (étab.)",
        line=dict(color="#3498db", width=0.5),
        fillcolor="rgba(52,152,219,0.6)",
        hovertemplate="%{y:,.0f}<extra>Médic. étab.</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["instrumentales"],
        mode="lines", stackgroup="one", name="Instrumentale (étab.)",
        line=dict(color="#e74c3c", width=0.5),
        fillcolor="rgba(231,76,60,0.5)",
        hovertemplate="%{y:,.0f}<extra>Instrumentale</extra>",
    ))
    # COVID band
    fig.add_vrect(x0=2019.5, x1=2021.5,
                  fillcolor="rgba(200,200,200,0.15)", line_width=0)
    fig.update_layout(
        title=dict(text="Modalités et lieux (2016–2024)", font=dict(size=14)),
        yaxis_title="Nombre d'IVG", xaxis_title=None,
        height=380, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.15),
        hovermode="x unified",
    )
    return fig


def _fig_taux_ica():
    """Compact: taux + ICA on double Y axis."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_taux["annee"], y=_taux["taux_1000"],
        mode="lines+markers", name="Taux ‰",
        line=dict(color="#2980b9", width=2), marker=dict(size=3),
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=_taux["annee"], y=_taux["ica"],
        mode="lines+markers", name="ICA",
        line=dict(color="#e67e22", width=2, dash="dot"), marker=dict(size=3),
        yaxis="y2",
    ))
    fig.update_layout(
        title=dict(text="Taux pour 1 000 femmes & ICA (1990–2023)", font=dict(size=13)),
        yaxis=dict(title=dict(text="Taux ‰ (15-49 ans)", font=dict(color="#2980b9", size=11)),
                   tickfont=dict(size=9)),
        yaxis2=dict(title=dict(text="ICA", font=dict(color="#e67e22", size=11)),
                    tickfont=dict(size=9), overlaying="y", side="right"),
        height=260, margin=dict(l=50, r=50, t=35, b=25),
        legend=dict(orientation="h", y=-0.2),
        hovermode="x unified",
    )
    return fig


# ── Layout ─────────────────────────────────────────────────────

def layout():
    total_fmt = f"{int(_latest_ts['total_brut']):,}".replace(",", " ")
    taux_fmt = f"{_latest_taux['taux_1000']:.1f} ‰"
    ica_fmt = f"{_latest_taux['ica']:.2f}"
    pct_med = f"{_latest_meth['pct_medicamenteux']:.0f}%"

    return html.Div([
        # KPI row
        kpi_row([
            kpi_card(total_fmt, f"Total IVG {int(_latest_ts['annee'])}",
                     "Record historique", "up"),
            kpi_card(taux_fmt, f"Taux national {int(_latest_taux['annee'])}"),
            kpi_card(ica_fmt, f"ICA {int(_latest_taux['annee'])}",
                     "≈ 62% des femmes au cours de leur vie", "neutral"),
            kpi_card(pct_med, f"Part médicamenteux {int(_latest_meth['annee'])}",
                     f"vs 66% en {int(_meth.iloc[0]['annee'])}", "up"),
        ]),

        # Two columns: trend + stacked area
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_fig_trend(), config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=_fig_stacked(), config={"displayModeBar": False}), md=6),
        ], className="mb-3"),

        # Compact bottom: taux + ICA
        dcc.Graph(figure=_fig_taux_ica(), config={"displayModeBar": False}),
    ])
