"""
components/header.py — Bandeau titre en haut du dashboard.

Affiché en permanence, il donne le titre du projet et les sources.
Le style est défini dans assets/styles.css (classe .header-banner).
"""

from dash import html


def make_header():
    return html.Div(className="header-banner", children=[
        html.H1("IVG en France — Droit légal, accessibilité réelle"),
        html.P("Analyse territoriale et démographique · DREES/SNDS · 2016-2024"),
    ])
