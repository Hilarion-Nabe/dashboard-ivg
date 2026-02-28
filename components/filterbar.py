"""
components/filterbar.py — Barre de filtres en haut du dashboard.

Contient trois filtres globaux qui s'appliquent à l'onglet actif :
  - Un slider pour choisir l'année (2016-2024)
  - Un sélecteur zone : métropole, DROM, ou tout
  - Un dropdown département pour ouvrir le panneau de détail

La barre est "sticky" (reste visible au scroll) grâce au CSS.
Les données départementales (carte, ranking) couvrent 2016-2023,
donc pour 2024 certains graphes affichent un message "non disponible".
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def make_filterbar(min_year=2016, max_year=2024):
    """
    Crée la barre de filtres avec le slider année, le choix de zone
    et le dropdown département. max_year=2024 car les données nationales
    vont jusque-là, même si les données départementales s'arrêtent à 2023.
    """
    return html.Div(id="filter-bar",className="filter-bar", children=[

        # Slider année
        html.Div([
            html.Label("Année"),
            dcc.Slider(
                id="filter-year",
                min=min_year, max=max_year,
                step=1, value=max_year,
                marks={y: str(y) for y in range(min_year, max_year + 1)},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "1", "minWidth": "300px"}),

        # Choix de zone géographique
        html.Div([
            html.Label("Zone"),
            dcc.RadioItems(
                id="filter-zone",
                options=[
                    {"label": " Tous", "value": "all"},
                    {"label": " Métropole", "value": "metro"},
                    {"label": " DROM", "value": "drom"},
                ],
                value="all",
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
            ),
        ]),

        # Sélecteur de département (ouvre le panneau drill-down)
        html.Div([
            html.Label("Département"),
            dcc.Dropdown(
                id="filter-dept",
                placeholder="Sélectionner...",
                clearable=True,
                style={"minWidth": "200px", "fontSize": "0.85rem"},
            ),
        ]),
    ])
