"""
pages/tab1_constat.py — Onglet 1 : Le Constat.

C'est la page d'accueil du dashboard. On y montre la situation nationale
en un coup d'œil : combien d'IVG en France, comment ça évolue depuis 1990,
et comment les pratiques se transforment (médicamenteux vs instrumental).

Trois graphiques :
  - La courbe historique du nombre total d'IVG (1990-2023)
  - L'aire empilée des modalités/lieux (2016-2024)
  - Un graphique compact taux + ICA sur double axe

Tous les graphiques sont statiques (pas de callback), ils sont
construits une fois au chargement et ne changent pas avec les filtres.
C'est un choix volontaire : cet onglet donne le contexte général.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data.cache import DATA
from components.kpi_cards import kpi_card, kpi_row

# On récupère les données une fois pour toutes depuis le cache
_ts = DATA["national_ts"]
_taux = DATA["national_taux"]
_meth = DATA["methodes"]

# Dernières valeurs pour les KPI en haut de page
_latest_ts = _ts.iloc[-1]
_latest_taux = _taux.iloc[-1]
_latest_meth = _meth.iloc[-1]


def _fig_trend():
    """
    Courbe du nombre total d'IVG en France de 1990 à 2023.
    On affiche aussi la série "sans reprises" quand elle est disponible
    (à partir de 2016). La bande grise marque la période COVID.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_ts["annee"], y=_ts["total_brut"],
        mode="lines+markers", name="Total IVG (brut)",
        line=dict(color="#2c3e50", width=2.5), marker=dict(size=4),
        hovertemplate="%{x} : %{y:,.0f}<extra></extra>",
    ))
    # Série "sans reprises" (IVG hors tentatives après échec)
    sr = _ts.dropna(subset=["total_sans_reprises"])
    if not sr.empty:
        fig.add_trace(go.Scatter(
            x=sr["annee"], y=sr["total_sans_reprises"],
            mode="lines", name="Sans reprises",
            line=dict(color="#95a5a6", width=1.5, dash="dash"),
        ))
    # Bande COVID (2020-2021)
    fig.add_vrect(x0=2019.5, x1=2021.5,
                  fillcolor="rgba(200,200,200,0.2)", line_width=0,
                  annotation_text="COVID", annotation_position="top left",
                  annotation_font=dict(size=9, color="gray"))
    fig.update_layout(
        title=dict(text="Total IVG — France (1990–2023)", font=dict(size=14)),
        yaxis=dict(title="Nombre d'IVG", gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
        xaxis_title=None,
        height=380, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.12),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def _fig_stacked():
    """
    Aire empilée montrant la répartition des IVG par modalité et lieu.
    Trois couches en dégradé de bleus pour rester dans la palette
    du dashboard : bleu clair (hors étab.), bleu moyen (médic. étab.),
    bleu foncé (instrumentale). La montée du hors-établissement
    depuis 2016 se lit dans l'expansion de la couche la plus claire.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["hors_etab"],
        mode="lines", stackgroup="one", name="Hors établissement",
        line=dict(color="#7fb3d8", width=0.5),
        fillcolor="rgba(127,179,216,0.7)",
        hovertemplate="%{y:,.0f}<extra>Hors étab.</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["medic_etab"],
        mode="lines", stackgroup="one", name="Médicamenteuse (étab.)",
        line=dict(color="#2980b9", width=0.5),
        fillcolor="rgba(41,128,185,0.7)",
        hovertemplate="%{y:,.0f}<extra>Médic. étab.</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_meth["annee"], y=_meth["instrumentales"],
        mode="lines", stackgroup="one", name="Instrumentale (étab.)",
        line=dict(color="#1a5276", width=0.5),
        fillcolor="rgba(26,82,118,0.7)",
        hovertemplate="%{y:,.0f}<extra>Instrumentale</extra>",
    ))
    # Bande COVID
    fig.add_vrect(x0=2019.5, x1=2021.5,
                  fillcolor="rgba(200,200,200,0.15)", line_width=0)
    fig.update_layout(
        title=dict(text="Modalités et lieux (2016–2024)", font=dict(size=14)),
        yaxis=dict(title="Nombre d'IVG", gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
        xaxis_title=None,
        height=380, margin=dict(l=50, r=20, t=40, b=30),
        legend=dict(orientation="h", y=-0.15),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig  


def _fig_taux_ica():
    """
    Graphique compact avec double axe Y : le taux pour 1000 femmes
    à gauche et l'ICA à droite. Ça permet de voir les deux indicateurs
    sur le même graphique sans qu'ils se chevauchent.
    """
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
        yaxis=dict(title="Taux ‰ (15-49 ans)", title_font=dict(color="#2980b9", size=12),
                   tickfont=dict(size=9), gridcolor="#f0f0f0"),
        yaxis2=dict(title="ICA", title_font=dict(color="#e67e22", size=12),
                    tickfont=dict(size=9), overlaying="y", side="right", gridcolor="#f0f0f0"),
        height=260, margin=dict(l=50, r=55, t=35, b=25),
        legend=dict(orientation="h", y=-0.2),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


# ── Layout de l'onglet ────────────────────────────────────────

def layout():
    """
    Construit le layout complet de l'onglet Constat.

    On commence par un encart qui pose le cadre du dashboard : c'est la
    première chose que l'utilisateur voit, et ça lui donne les clés de
    lecture avant de plonger dans les chiffres. Ensuite viennent les KPI
    et les trois graphiques qui brossent le portrait national.
    """ 
    import components.kpi_cards as _kpi_mod 
    _kpi_mod._accent_index = 0
    # ... reste inchangé
    total_fmt = f"{int(_latest_ts['total_brut']):,}".replace(",", " ")
    taux_fmt = f"{_latest_taux['taux_1000']:.1f} ‰"
    ica_fmt = f"{_latest_taux['ica']:.2f}"
    pct_med = f"{_latest_meth['pct_medicamenteux']:.0f}%"

    # Encart d'introduction — bordure bleue à gauche, style "callout"
    intro = html.Div(
        style={
            "borderLeft": "4px solid #2980b9",
            "backgroundColor": "#f8f9fa",
            "padding": "20px 24px",
            "marginBottom": "20px",
            "borderRadius": "4px",
        },
        children=[
            html.H5("Pourquoi ce dashboard ?",
                     style={"fontWeight": "bold", "marginBottom": "10px"}),
            html.P(
                "Ce dashboard analyse l'IVG en France sous un angle à la fois "
                "national, territorial et démographique. Il permet d'identifier "
                "les évolutions du recours, les disparités entre départements, "
                "les profils de patientes et les transformations de l'offre de soins.",
                style={"marginBottom": "10px", "lineHeight": "1.6"},
            ),
            html.P(
                "La page d'ouverture présente le constat général. Les filtres "
                "interactifs sont ensuite disponibles dans les onglets d'exploration "
                "pour approfondir les écarts territoriaux, le profil des patientes "
                "et l'offre de soins.",
                style={"marginBottom": "0", "lineHeight": "1.6"},
            ),
        ],
    )

    return html.Div([
        # Encart introductif
        intro,

        # Ligne de KPI
        kpi_row([
            kpi_card(total_fmt, f"Total IVG {int(_latest_ts['annee'])}",
                     "Record historique", "up"),
            kpi_card(taux_fmt, f"Taux national {int(_latest_taux['annee'])}"),
            kpi_card(ica_fmt, f"ICA {int(_latest_taux['annee'])}",
                     "≈ 62% des femmes au cours de leur vie", "neutral"),
            kpi_card(pct_med, f"Part médicamenteux {int(_latest_meth['annee'])}",
                     f"vs 66% en {int(_meth.iloc[0]['annee'])}", "up"),
        ]),

        # Deux colonnes : courbe historique + aire empilée
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_fig_trend(), config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=_fig_stacked(), config={"displayModeBar": False}), md=6),
        ], className="mb-3"),

        # Graphique compact en bas : taux + ICA
        dcc.Graph(figure=_fig_taux_ica(), config={"displayModeBar": False}),
    ])
