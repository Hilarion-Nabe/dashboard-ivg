"""
pages/tab2_fracture.py — Onglet 2 : La Fracture (inégalités territoriales).

C'est l'onglet le plus interactif du dashboard. Il répond à la question :
est-ce que le taux de recours à l'IVG varie beaucoup d'un département à l'autre ?
(Spoiler : oui, énormément.)

Deux visualisations côte à côte :
  - À gauche : carte choroplèthe de France par département
  - À droite : classement (top/bottom 15 départements)

L'utilisateur peut cliquer sur un département dans la carte OU dans
le classement pour ouvrir le panneau de détail (dept_drawer).
Les filtres année et zone de la barre du haut pilotent ces deux graphiques.
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

# Années disponibles pour la carte : 2016-2022 (dep_year) + 2023 (fichier carte)
_YEARS_MAP = sorted(_dep_year["annee"].unique()) + [2023]


def _build_choropleth(year, zone="all"):
    """
    Construit la carte choroplèthe pour une année donnée.
    Pour 2023 on utilise le fichier carte dédié, pour 2016-2022
    on pioche dans le fichier départemental multi-années.
    Si l'année demandée n'existe pas (ex: 2024), on affiche un message.
    """
    if year == 2023:
        df = _dep2023[["dep_code", "dep_nom", "taux_2023", "is_drom"]].copy()
        df = df.rename(columns={"taux_2023": "taux_recours"})
    else:
        df = _dep_year[_dep_year["annee"] == year][
            ["dep_code", "dep_nom", "taux_recours", "is_drom"]
        ].copy()

    if df.empty:
        return go.Figure().update_layout(title="Données non disponibles pour cette année")

    # Filtre par zone géographique (métropole / DROM / tout)
    if zone == "metro":
        df = df[~df["is_drom"]]
    elif zone == "drom":
        df = df[df["is_drom"]]

    # Construction de la carte avec Plotly Express
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

    # Centrage : France métropolitaine par défaut, ou Outre-mer si filtre DROM
    if zone == "drom":
        fig.update_layout(mapbox=dict(center=dict(lat=-15, lon=-55), zoom=2.5))
    else:
        fig.update_layout(mapbox=dict(center=dict(lat=46.2, lon=2.5), zoom=4.5))

    fig.update_layout(
        title=dict(text=f"Taux de recours ‰ — {year}", font=dict(size=14)),
        height=550, margin=dict(l=0, r=0, t=40, b=10),
        coloraxis_colorbar=dict(title="‰", thickness=15, len=0.6),
    )
    return fig


def _build_ranking(year, zone="all", n=15):
    """
    Cleveland dot plot montrant les départements aux extrêmes du taux
    de recours, avec la médiane nationale comme point de repère.

    Chaque département est représenté par une ligne horizontale portant
    deux points : un losange gris pour la médiane nationale (identique
    pour tous, c'est le repère fixe) et un rond coloré pour le taux
    réel du département. L'écart entre les deux se lit immédiatement
    dans la distance qui les sépare.

    Ce type de graphique — popularisé par William Cleveland en 1984 —
    est reconnu en dataviz pour sa capacité à rendre les comparaisons
    plus précises que les bar charts : l'œil humain estime mieux la
    position d'un point sur un axe que la longueur d'une barre.

    On affiche les Top N (taux les plus élevés) en haut, puis un
    espace, puis les Bottom N (taux les plus bas) en bas. Le passage
    de l'un à l'autre matérialise visuellement la "fracture".
    """
    import pandas as pd

    if year == 2023:
        df = _dep2023[["dep_code", "dep_nom", "taux_2023", "is_drom"]].copy()
        df = df.rename(columns={"taux_2023": "taux_recours"})
    else:
        df = _dep_year[_dep_year["annee"] == year][
            ["dep_code", "dep_nom", "taux_recours", "is_drom"]
        ].copy()

    if df.empty:
        return go.Figure()

    if zone == "metro":
        df = df[~df["is_drom"]]
    elif zone == "drom":
        df = df[df["is_drom"]]

    mediane = df["taux_recours"].median()

    # Constitution des deux groupes
    top = df.nlargest(n, "taux_recours").copy()
    bottom = df.nsmallest(n, "taux_recours").copy()

    # Tri pour l'affichage vertical :
    # Bottom en bas (du plus bas au plus haut), séparateur, Top en haut
    bottom = bottom.sort_values("taux_recours", ascending=False)
    top = top.sort_values("taux_recours", ascending=False)

    # On insère une ligne vide comme séparateur visuel entre les groupes
    separator = pd.DataFrame([{
        "dep_nom": "",  "dep_code": "", "taux_recours": None,
        "is_drom": False
    }])
    display = pd.concat([bottom, separator, top], ignore_index=True)

    # Ordre des catégories sur l'axe Y (de bas en haut)
    y_order = display["dep_nom"].tolist()

    fig = go.Figure()

    # ── Segments reliant la médiane au taux réel ───────────────────
    for _, row in display.iterrows():
        if row["dep_nom"] == "" or pd.isna(row["taux_recours"]):
            continue
        seg_color = "#e0e0e0"
        fig.add_trace(go.Scatter(
            x=[mediane, row["taux_recours"]],
            y=[row["dep_nom"], row["dep_nom"]],
            mode="lines",
            line=dict(color=seg_color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ── Points : médiane (losange gris, repère fixe) ──────────────
    real_rows = display[display["dep_nom"] != ""].dropna(subset=["taux_recours"])
    fig.add_trace(go.Scatter(
        x=[mediane] * len(real_rows),
        y=real_rows["dep_nom"],
        mode="markers",
        marker=dict(
            symbol="diamond",
            color="#bdc3c7",
            size=7,
            line=dict(color="white", width=0.5),
        ),
        name=f"Médiane ({mediane:.1f} ‰)",
        hovertemplate=f"Médiane nationale : {mediane:.1f} ‰<extra></extra>",
    ))

    # ── Points : taux réel — Métropole (bleu) ─────────────────────
    metro = real_rows[real_rows["is_drom"] != True]
    if not metro.empty:
        fig.add_trace(go.Scatter(
            x=metro["taux_recours"],
            y=metro["dep_nom"],
            mode="markers",
            marker=dict(
                color="#2980b9",
                size=10,
                line=dict(color="white", width=1.5),
            ),
            name="Métropole",
            customdata=metro["dep_code"],
            text=metro["taux_recours"].apply(lambda v: f"{v:.1f} ‰"),
            hovertemplate="<b>%{y}</b><br>Taux : %{text}<br>Écart : %{customdata}<extra>Métropole</extra>",
        ))

    # ── Points : taux réel — DROM (orange) ─────────────────────────
    drom = real_rows[real_rows["is_drom"] == True]
    if not drom.empty:
        fig.add_trace(go.Scatter(
            x=drom["taux_recours"],
            y=drom["dep_nom"],
            mode="markers",
            marker=dict(
                color="#e67e22",
                size=10,
                line=dict(color="white", width=1.5),
            ),
            name="DROM",
            customdata=drom["dep_code"],
            text=drom["taux_recours"].apply(lambda v: f"{v:.1f} ‰"),
            hovertemplate="<b>%{y}</b><br>Taux : %{text}<extra>DROM</extra>",
        ))

    # ── Ligne verticale de la médiane ──────────────────────────────
    fig.add_vline(
        x=mediane, line_width=1, line_color="#bdc3c7", line_dash="dot",
    )

    # ── Annotations pour identifier les deux groupes ───────────────
    fig.add_annotation(
        x=1.0, xref="paper", y=top.iloc[-1]["dep_nom"],
        text="▲ Taux les plus élevés",
        showarrow=False,
        font=dict(size=9, color="#2c3e50", weight="bold"),
        xanchor="right",
    )
    fig.add_annotation(
        x=1.0, xref="paper", y=bottom.iloc[-1]["dep_nom"],
        text="▼ Taux les plus bas",
        showarrow=False,
        font=dict(size=9, color="#95a5a6", weight="bold"),
        xanchor="right",
    )

    fig.update_layout(
        title=dict(
            text=f"Fracture territoriale — {year}",
            font=dict(size=13),
        ),
        xaxis=dict(
            title="Taux de recours (‰)",
            gridcolor="#f0f0f0",
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="#f8f8f8",
            categoryorder="array",
            categoryarray=y_order,
        ),
        height=max(600, len(display) * 22),
        margin=dict(l=170, r=80, t=45, b=35),
        legend=dict(
            orientation="h", y=-0.05,
            font=dict(size=10),
            itemsizing="constant",
        ),
        plot_bgcolor="white",
        hovermode="closest",
    )
    return fig 
  
   


def layout():
    """
    Layout de l'onglet Fracture avec deux états visuels :
      - année 2016-2023 : carte + classement normalement
      - année 2024 : contenu flouté en arrière-plan avec encart
        informatif superposé au centre (effet glassmorphism léger)

    Le wrapper parent est en position relative pour que l'encart
    puisse se positionner en absolu par-dessus le contenu flouté.
    """
    return html.Div(style={"position": "relative", "minHeight": "500px"}, children=[

        # ── État normal : carte + classement (toujours rendu) ──────
        html.Div(id="tab2-content", children=[
            dbc.Row([
                # Colonne gauche : la carte
                dbc.Col([
                    html.Div("Taux de recours par département", className="section-title"),
                    html.Div("‰ femmes 15-49 ans · cliquez sur un département",
                             className="section-subtitle"),
                    dcc.Graph(id="map-choropleth", config={"displayModeBar": False}),
                    html.P("Cliquez sur un département pour voir son profil.",
                           className="micro-guide"),
                ], md=7),

                # Colonne droite : le classement
                dbc.Col([
                    html.Div("Classement", className="section-title"),
                    html.Div("Écart à la médiane nationale · ◆ = médiane",
                             className="section-subtitle"),
                    dcc.Graph(id="ranking-chart", config={"displayModeBar": False}),
                ], md=5),
            ]),
        ]),

        # ── État fallback : superposé au centre si données absentes ──
        html.Div(id="tab2-nodata", style={"display": "none"}, children=[
            html.Div(
                style={
                    "position": "absolute",
                    "top": "0", "left": "0", "right": "0", "bottom": "0",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "zIndex": "10",
                    "textAlign": "center",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.95)",
                            "borderRadius": "12px",
                            "padding": "40px 50px",
                            "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                            "maxWidth": "520px",
                        },
                        children=[
                            html.Div("📊", style={"fontSize": "2.5rem",
                                                    "marginBottom": "16px",
                                                    "opacity": "0.5"}),
                            html.H4("Données départementales non disponibles",
                                     style={"fontWeight": "600",
                                            "color": "#2c3e50",
                                            "marginBottom": "12px"}),
                            html.P(
                                "Les données départementales couvrent la période "
                                "2016–2023. Les données nationales pour 2024 sont "
                                "visibles dans l'onglet Le Constat.",
                                style={"color": "#6c757d",
                                       "fontSize": "0.92rem",
                                       "lineHeight": "1.6",
                                       "marginBottom": "20px"},
                            ),
                            html.Div(
                                "Déplacez le curseur sur une année entre 2016 et 2023.",
                                style={
                                    "backgroundColor": "#f8f9fa",
                                    "border": "1px solid #e9ecef",
                                    "borderRadius": "8px",
                                    "padding": "10px 20px",
                                    "color": "#495057",
                                    "fontSize": "0.82rem",
                                    "fontWeight": "500",
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ]),
    ]) 