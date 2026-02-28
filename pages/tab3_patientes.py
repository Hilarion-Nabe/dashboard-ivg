"""
pages/tab3_patientes.py — Onglet 3 : Les Patientes (profil démographique).

Ici on s'intéresse à QUI a recours à l'IVG en France :
  - La répartition par tranche d'âge (pyramide horizontale)
  - Le zoom sur les mineures (<18 ans) : classement départemental
  - L'évolution nationale de la part des mineures dans le temps

Le graphique pyramide et le classement mineures se mettent à jour
avec le slider année (callbacks dans app.py). La courbe de tendance
en bas est statique (toutes les années affichées d'un coup).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data.cache import DATA
from components.kpi_cards import kpi_card, kpi_row

_nat_age = DATA["nat_age"]
_nat_min = DATA["nat_mineures"]
_mineures = DATA["mineures"]

# Labels et couleurs pour les tranches d'âge (utilisés dans la pyramide)
AGE_LABELS = ["<18", "18-19", "20-24", "25-29", "30-34", "35-39", "40+"]
PCT_COLS = ["pct_inf18", "pct_18_19", "pct_20_24", "pct_25_29",
            "pct_30_34", "pct_35_39", "pct_40plus"]
AGE_COLORS = ["#d4e6f1", "#a9cce3", "#7fb3d8", "#5499c7", "#2980b9", "#2471a3", "#1a5276"] 

def build_pyramid(year):
    """
    Construit la "pyramide" d'âge (en fait un bar chart horizontal)
    montrant la part de chaque tranche d'âge dans les IVG nationales.
    Chaque tranche a sa propre couleur pour faciliter la lecture.
    """
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
    """
    Dot plot montrant la part d'IVG chez les mineures (<18 ans) par
    département, avec la moyenne nationale en ligne de référence.

    On affiche les valeurs brutes (pourcentages réels) plutôt que
    l'écart à la moyenne, parce que c'est plus intuitif à lire pour
    l'utilisateur : il voit directement "Mayotte = 9.1%", ce qui est
    plus parlant que "+6.2 points". La ligne de référence France se
    retrouve naturellement au milieu de la zone visible, ce qui la
    rend immédiatement identifiable.

    Les DROM sont distingués en orange car leur contexte socio-
    démographique est très différent de la métropole.
    """
    df = _mineures[(_mineures["annee"] == year) & (_mineures["is_dept"])].copy()
    if df.empty:
        return go.Figure()

    # Jointure pour récupérer le flag DROM
    lookup = DATA["dep_lookup"]
    df = df.merge(lookup[["dep_nom", "is_drom"]],
                  left_on="zone_geo", right_on="dep_nom", how="left")

    if zone == "metro":
        df = df[df["is_drom"] != True]
    elif zone == "drom":
        df = df[df["is_drom"] == True]

    # Moyenne nationale (ligne de référence)
    fr_val = _nat_min[_nat_min["annee"] == year]["part_mineures"].values
    ref = fr_val[0] if len(fr_val) > 0 else df["part_mineures"].median()

    # Top N départements, triés du plus bas au plus haut
    top = df.nlargest(n, "part_mineures")
    top = top.sort_values("part_mineures", ascending=True)

    fig = go.Figure()

    # Tiges horizontales reliant la ligne de référence au point
    for _, row in top.iterrows():
        tige_color = "#e8c4a0" if row["is_drom"] else "#a9cce3"
        fig.add_trace(go.Scatter(
            x=[ref, row["part_mineures"]],
            y=[row["zone_geo"], row["zone_geo"]],
            mode="lines",
            line=dict(color=tige_color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Points DROM (orange)
    drom = top[top["is_drom"] == True]
    if not drom.empty:
        fig.add_trace(go.Scatter(
            x=drom["part_mineures"],
            y=drom["zone_geo"],
            mode="markers",
            marker=dict(color="#e67e22", size=10,
                        line=dict(color="white", width=1)),
            name="DROM",
            hovertemplate="<b>%{y}</b> : %{x:.1f}%<extra>DROM</extra>",
        ))

    # Points Métropole (bleu)
    metro = top[top["is_drom"] != True]
    if not metro.empty:
        fig.add_trace(go.Scatter(
            x=metro["part_mineures"],
            y=metro["zone_geo"],
            mode="markers",
            marker=dict(color="#2980b9", size=10,
                        line=dict(color="white", width=1)),
            name="Métropole",
            hovertemplate="<b>%{y}</b> : %{x:.1f}%<extra>Métropole</extra>",
        ))

    # Ligne de référence : moyenne nationale
    fig.add_vline(
        x=ref, line_width=2, line_color="#2c3e50", line_dash="dash",
        annotation_text=f"France : {ref:.1f}%",
        annotation_position="top",
        annotation_font=dict(size=11, color="#2c3e50", weight="bold"),
    )

    fig.update_layout(
        title=dict(
            text=f"Part mineures (<18 ans) — Top {n} départements — {year}",
            font=dict(size=13),
        ),
        xaxis=dict(
            title="Part des mineures (%)",
            gridcolor="#f0f0f0",
            ticksuffix="%",
            rangemode="tozero",
        ),
        yaxis=dict(gridcolor="#f8f8f8"),
        height=max(400, len(top) * 24),
        margin=dict(l=170, r=40, t=50, b=40),
        legend=dict(
            orientation="h", y=-0.08,
            font=dict(size=11),
            itemsizing="constant",
        ),
        plot_bgcolor="white",
        hovermode="closest",
    )
    return fig     

def build_trend_mineures():
    """
    Courbe de l'évolution nationale de la part des mineures dans les IVG.
    Graphique statique (pas piloté par le slider), il montre toute la série.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_nat_min["annee"], y=_nat_min["part_mineures"],
        mode="lines+markers", line=dict(color="#2980b9", width=2.5),
        marker=dict(size=5),
        hovertemplate="%{x} : %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Évolution nationale — Part mineures (<18 ans)", font=dict(size=13)),
        yaxis=dict(title="%", gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
        xaxis_title=None,
        height=230, margin=dict(l=45, r=20, t=35, b=25),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    ) 
    return fig


# ── Layout de l'onglet ────────────────────────────────────────

def layout():
    # KPI avec la dernière et la première année disponibles
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

        # Courbe de tendance en bas de page
        dcc.Graph(id="mineures-trend",
                  figure=build_trend_mineures(),
                  config={"displayModeBar": False}),
    ]) 
