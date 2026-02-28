"""
pages/tab4_offre.py — Onglet 4 : L'Offre de soins.

Cet onglet explore le versant "offre" de la question : qui pratique les IVG
en libéral, et est-ce qu'il y a assez de praticiens partout ?

On y voit :
  - La recomposition spectaculaire de l'offre : les sages-femmes sont passées
    de quasi 0% à ~41% des praticiens IVG en 8 ans
  - Les gynécologues (GO) sont en forte baisse, les généralistes (MG) stables
  - Les "déserts IVG" : départements avec 5 praticiens libéraux ou moins
  - La charge moyenne par praticien (total IVG / total praticiens)

Le graphique empilé est statique, le classement des déserts est dynamique
(piloté par le slider année via callback dans app.py).
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
    """
    Graphique empilé 100% montrant l'évolution des parts de chaque
    profession dans l'offre de soins IVG libérale.
    On utilise un dégradé de bleus cohérent avec la charte du dashboard :
    bleu clair pour les SF (en croissance), bleu moyen pour les MG
    (stables), bleu foncé/marine pour les GO (en recul).
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_sf"],
        mode="lines", stackgroup="one", groupnorm="percent",
        name="Sages-femmes (SF)",
        line=dict(width=0.5, color="#a9cce3"),
        fillcolor="rgba(169,204,227,0.8)",
        hovertemplate="%{x} : %{y:.1f}%<extra>SF</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_mg"],
        mode="lines", stackgroup="one",
        name="Médecins généralistes (MG)",
        line=dict(width=0.5, color="#2980b9"),
        fillcolor="rgba(41,128,185,0.8)",
        hovertemplate="%{x} : %{y:.1f}%<extra>MG</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_nat_prat["annee"], y=_nat_prat["pct_go"],
        mode="lines", stackgroup="one",
        name="Gynécologues-obst. (GO)",
        line=dict(width=0.5, color="#154360"),
        fillcolor="rgba(21,67,96,0.8)",
        hovertemplate="%{x} : %{y:.1f}%<extra>GO</extra>",
    ))
    fig.update_layout( 
        title=dict(text="Recomposition de l'offre — Part par profession (%)",
                   font=dict(size=14)),
        yaxis=dict(title="Part (%)", ticksuffix="%", range=[0, 100],
                   gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
        xaxis_title=None,
        height=420, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.12),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig  


def build_deserts_ranking(year):
    """
    Classement des départements "déserts IVG" pour une année donnée,
    affiché sous forme de lollipop chart (point + tige horizontale).

    On considère un département comme désert s'il a 5 praticiens
    libéraux ou moins. 
    """
    df = _deserts[_deserts["annee"] == year].copy()
    if df.empty:
        return go.Figure().update_layout(
            title="Aucun département avec ≤ 5 praticiens cette année",
            height=250,
        )

    df = df.sort_values("total_prat", ascending=True)

    fig = go.Figure()

    # Les tiges horizontales (lignes allant de 0 au point)
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[0, row["total_prat"]],
            y=[row["zone_geo"], row["zone_geo"]],
            mode="lines",
            line=dict(color="#a9cce3", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Les points au bout de chaque tige
    fig.add_trace(go.Scatter(
        x=df["total_prat"],
        y=df["zone_geo"],
        mode="markers+text",
        marker=dict(color="#2980b9", size=10),
        text=df["total_prat"].astype(int).astype(str) + " prat.",
        textposition="middle right",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b> : %{x:.0f} praticiens<extra></extra>",
        showlegend=False,
    ))

    fig.update_layout(
        title=dict(text=f"Déserts IVG — Départements ≤ 5 praticiens ({year})",
                   font=dict(size=13)),
        height=max(250, len(df) * 25),
        margin=dict(l=160, r=60, t=35, b=25),
        showlegend=False,
        xaxis=dict( range=[0,6]),
    )
    return fig 

    


# ── Layout de l'onglet ────────────────────────────────────────

def layout(): 
    import components.kpi_cards as _kpi_mod
    _kpi_mod._accent_index = 0 

    # KPI calculés à partir des premières et dernières valeurs
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
            # Colonne gauche : graphique empilé des professions
            dbc.Col([
                dcc.Graph(figure=_fig_stacked_100(), config={"displayModeBar": False}),
            ], md=7),

            # Colonne droite : classement des déserts
            dbc.Col([
                dcc.Graph(id="deserts-ranking", config={"displayModeBar": False}),
                            ], md=5),
        ]),
    ])  
