"""
components/filterbar.py — Barre de filtres sticky (année, zone géo).

Les filtres sont globaux et s'appliquent à l'onglet actif via callbacks.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def make_filterbar(min_year=2016, max_year=2024):
    """Creates the sticky filter bar with year slider and zone selector.
    Note: max_year=2024 for national data, but dept data only goes to 2023.
    Tabs that use dept data will show fallback for unsupported years.
    """
    return html.Div(className="filter-bar", children=[

        # Year selector
        html.Div([
            html.Label("Année"),
            dcc.Slider(
                id="filter-year",
                min=min_year, max=max_year,
                step=1, value=min(max_year, 2023),
                marks={y: str(y) for y in range(min_year, max_year + 1)},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "1", "minWidth": "300px"}),

        # Zone selector
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

        # Dept selector (for drill-down context)
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
