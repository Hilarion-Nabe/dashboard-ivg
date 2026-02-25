"""
components/footer.py — Footer permanent (3 lignes méthodo).
"""

from dash import html


def make_footer():
    return html.Div(className="footer", children=[
        html.Span("⚠ Rupture méthodologique 2020 — comparaisons avant/après avec prudence"),
        html.Span("Taux de recours ≠ accessibilité réelle"),
        html.Span("Source : DREES / SNDS (sept. 2024)"),
    ])
