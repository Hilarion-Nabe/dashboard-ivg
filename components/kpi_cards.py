"""
components/kpi_cards.py — Reusable KPI card components.
"""

from dash import html
import dash_bootstrap_components as dbc


def kpi_card(value: str, label: str, delta: str = None, delta_dir: str = "neutral"):
    """
    Creates a single KPI card.

    Parameters
    ----------
    value : str      — Main displayed value (e.g. "251 169")
    label : str      — Short label (e.g. "TOTAL IVG 2023")
    delta : str      — Optional delta text (e.g. "+3.8% vs 2022")
    delta_dir : str  — "up", "down", or "neutral" for coloring
    """
    children = [
        html.Div(value, className="kpi-value"),
        html.Div(label, className="kpi-label"),
    ]
    if delta:
        children.append(html.Div(delta, className=f"kpi-delta {delta_dir}"))

    return html.Div(className="kpi-card", children=children)


def kpi_row(cards: list):
    """Wraps a list of kpi_card() in a responsive Bootstrap row."""
    n = len(cards)
    col_width = max(12 // n, 3)
    return dbc.Row(
        [dbc.Col(card, md=col_width) for card in cards],
        className="g-3 mb-3",
    )
