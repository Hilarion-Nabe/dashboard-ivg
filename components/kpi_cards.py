"""
components/kpi_cards.py — Composant réutilisable pour les cartes KPI.

Les KPI (Key Performance Indicators) sont les petits encadrés en haut
de chaque onglet qui affichent les chiffres clés : total IVG, taux,
part des mineures, nombre de praticiens, etc.

Chaque carte reçoit automatiquement une bordure latérale colorée qui
lui donne une identité visuelle propre sans casser l'harmonie générale.
Les couleurs reprennent la palette du dashboard (bleus, orange, vert).

On a deux fonctions :
  - kpi_card() : crée UNE carte avec valeur, label et delta optionnel
  - kpi_row() : aligne plusieurs cartes sur une ligne responsive
"""

from dash import html
import dash_bootstrap_components as dbc

# Palette d'accents pour la bordure gauche des KPI.
# On alterne ces couleurs au fil des cartes créées.
_ACCENT_COLORS = ["#2980b9", "#1a5276", "#e67e22", "#27ae60"]
_accent_index = 0


def kpi_card(value: str, label: str, delta: str = None, delta_dir: str = "neutral"):
    """
    Crée une carte KPI individuelle avec un accent latéral coloré.

    Paramètres :
      value     — la valeur principale affichée en gros (ex: "251 169")
      label     — le libellé en dessous (ex: "Total IVG 2023")
      delta     — texte optionnel de comparaison (ex: "+3.8% vs 2022")
      delta_dir — direction du delta pour la couleur : "up", "down" ou "neutral"
    """
    global _accent_index
    accent = _ACCENT_COLORS[_accent_index % len(_ACCENT_COLORS)]
    _accent_index += 1

    children = [
        html.Div(value, className="kpi-value"),
        html.Div(label, className="kpi-label"),
    ]
    if delta:
        children.append(html.Div(delta, className=f"kpi-delta {delta_dir}"))

    return html.Div(
        className="kpi-card",
        style={"borderLeft": f"3px solid {accent}"},
        children=children,
    )


def kpi_row(cards: list):
    """
    Dispose une liste de kpi_card() sur une ligne responsive.
    Le nombre de colonnes s'adapte au nombre de cartes passées.
    """
    n = len(cards)
    col_width = max(12 // n, 3)
    return dbc.Row(
        [dbc.Col(card, md=col_width) for card in cards],
        className="g-3 mb-3",
    ) 