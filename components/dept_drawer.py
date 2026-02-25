"""
components/dept_drawer.py — Panneau drill-down département.

S'ouvre via clic sur la carte ou le ranking.
Affiche : KPIs, mini trend, profil âge, part mineures.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def make_drawer():
    """Creates the offcanvas drawer (hidden by default, opened via callback)."""
    return dbc.Offcanvas(
        id="dept-drawer",
        title="Profil département",
        placement="end",
        is_open=False,
        style={"width": "480px"},
        children=[
            html.Div(id="drawer-content", children=[
                html.P("Cliquez sur un département pour voir son profil.",
                       className="micro-guide"),
            ]),
        ],
    )


def build_drawer_content(dep_nom, dep_code, annee_dep, annee_feuilles,
                         dep_year, mineures, age_dept, dep_2023):
    """
    Builds the drawer HTML content for a given department.

    Parameters
    ----------
    annee_dep : int       — Year for dep_year data (capped at 2022)
    annee_feuilles : int  — Year for mineures/age_dept (up to 2024)

    Called from callback when user clicks on a department.
    Returns a list of Dash HTML components.
    """
    import plotly.graph_objects as go
    from components.kpi_cards import kpi_card

    children = []
    children.append(html.H3(f"{dep_nom} ({dep_code})"))

    # ── KPIs (from dep_year, capped year) ──
    dy = dep_year[(dep_year["dep_code"] == dep_code)]
    row = dy[dy["annee"] == annee_dep] if annee_dep in dy["annee"].values else dy.iloc[-1:]

    if not row.empty:
        r = row.iloc[0]
        kpis = html.Div(style={"display": "flex", "gap": "12px", "marginBottom": "16px"}, children=[
            kpi_card(f"{r['taux_recours']:.1f} ‰", f"Taux {int(r['annee'])}"),
            kpi_card(f"#{int(r['rang_national'])}", "Rang national"),
            kpi_card(f"{r['ecart_mediane']:+.1f}", "Écart médiane"),
        ])
        children.append(kpis)

    # ── Mini trend : taux 2016-2022 ──
    if not dy.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=dy["annee"], y=dy["taux_recours"],
            mode="lines+markers",
            line=dict(color="#3498db", width=2),
            marker=dict(size=5),
        ))
        fig_trend.update_layout(
            height=180, margin=dict(l=40, r=10, t=25, b=30),
            title=dict(text="Taux de recours ‰", font=dict(size=12)),
            xaxis=dict(dtick=1, tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            showlegend=False,
        )
        children.append(dcc.Graph(figure=fig_trend, config={"displayModeBar": False}))

    # ── Profil âge (feuille 8, uses annee_feuilles) ──
    ad = age_dept[(age_dept["dep_code"] == dep_code) & (age_dept["annee"] == annee_feuilles)]
    if not ad.empty:
        row_age = ad.iloc[0]
        age_labels = ["<18", "18-19", "20-24", "25-29", "30-34", "35-39", "40+"]
        pct_cols = ["pct_inf18", "pct_18_19", "pct_20_24", "pct_25_29",
                    "pct_30_34", "pct_35_39", "pct_40plus"]
        vals = [row_age.get(c, 0) for c in pct_cols]

        fig_age = go.Figure()
        fig_age.add_trace(go.Bar(
            x=age_labels, y=vals,
            marker_color="#3498db",
            text=[f"{v:.0f}%" for v in vals],
            textposition="outside",
        ))
        fig_age.update_layout(
            height=180, margin=dict(l=30, r=10, t=25, b=30),
            title=dict(text=f"Profil d'âge {annee_feuilles} (%)", font=dict(size=12)),
            yaxis=dict(range=[0, max(vals) * 1.3 if vals else 50], tickfont=dict(size=9)),
            xaxis=dict(tickfont=dict(size=9)),
            showlegend=False,
        )
        children.append(dcc.Graph(figure=fig_age, config={"displayModeBar": False}))

    # ── Mineures (feuille 4, uses annee_feuilles) ──
    min_data = mineures[(mineures["dep_code"] == dep_code) & (mineures["annee"] == annee_feuilles)]
    fr_data = mineures[(mineures["zone_geo"] == "France entière") & (mineures["annee"] == annee_feuilles)]

    if not min_data.empty:
        val = min_data.iloc[0]["part_mineures"]
        fr_val = fr_data.iloc[0]["part_mineures"] if not fr_data.empty else None
        delta = f"France : {fr_val:.1f}%" if fr_val is not None else ""
        children.append(
            html.Div(style={"marginTop": "12px"}, children=[
                kpi_card(f"{val:.1f}%", f"Part mineures (<18) {annee_feuilles}", delta, "neutral"),
            ])
        )

    return children
