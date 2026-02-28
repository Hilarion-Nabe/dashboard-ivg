"""
components/footer.py — Pied de page permanent du dashboard.

Trois rappels méthodologiques affichés en permanence pour que
l'utilisateur garde en tête les limites de l'analyse. Le footer
est structuré en trois colonnes avec un séparateur fin au-dessus.
"""

from dash import html
import dash_bootstrap_components as dbc


def make_footer():
    """
    Footer en trois colonnes équilibrées. Chaque mention a un rôle :
      - gauche : avertissement méthodologique (rupture de série)
      - centre : rappel conceptuel (taux ≠ accessibilité)
      - droite : source des données (DREES/SNDS)
    """
    return html.Div(className="footer", children=[
        dbc.Row([
            dbc.Col(
                html.Span([
                    html.Span("⚠ ", style={"color": "#e67e22"}),
                    "Rupture méthodologique 2020 — comparaisons avant/après avec prudence",
                ]),
                md=5,
                className="footer-item footer-left",
            ),
            dbc.Col(
                html.Span(
                    "Taux de recours ≠ accessibilité réelle",
                    style={"fontStyle": "italic"},
                ),
                md=4,
                className="footer-item footer-center",
            ),
            dbc.Col(
                html.Span([
                    html.Strong("Source : "),
                    "DREES / SNDS (sept. 2024)",
                ]),
                md=3,
                className="footer-item footer-right",
            ),
        ], className="g-0"),
    ]) 

