"""
components/header.py — Bandeau titre du dashboard.
"""

from dash import html


def make_header():
    return html.Div(className="header-banner", children=[
        html.H1("IVG en France — Droit légal, accessibilité réelle"),
        html.P("Analyse territoriale et démographique · DREES/SNDS · 2016-2024"),
    ])
