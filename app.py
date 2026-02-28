"""
app.py — Point d'entrée du Dashboard IVG France.

C'est ce fichier qui fait tourner toute l'application. Il :
  1) Initialise l'app Dash avec Bootstrap
  2) Définit le layout global (header, filtres, onglets, footer)
  3) Enregistre tous les callbacks (interactions utilisateur)
  4) Expose la variable `server` pour gunicorn (déploiement Render)

Pour lancer en local :   python app.py
Pour déployer :           gunicorn app:server --bind 0.0.0.0:$PORT
"""

import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

# ── Chargement des données (une seule fois à l'import) ───────
from data.cache import DATA

# ── Composants d'interface ────────────────────────────────────
from components.header import make_header
from components.footer import make_footer
from components.filterbar import make_filterbar
from components.dept_drawer import make_drawer, build_drawer_content

# ── Les 4 pages/onglets ──────────────────────────────────────
from pages import tab1_constat, tab2_fracture, tab3_patientes, tab4_offre


# ══════════════════════════════════════════════════════════════
# INITIALISATION DE L'APP
# ══════════════════════════════════════════════════════════════

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="IVG France — Dashboard",
    update_title=None,  # évite le "Updating..." dans l'onglet du navigateur
)

# Variable server exposée pour gunicorn (Render)
server = app.server


# ══════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL
# ══════════════════════════════════════════════════════════════

# Liste déroulante des départements pour le filtre (construite au démarrage)
_dep_options = [
    {"label": f"{row['dep_nom']} ({row['dep_code']})", "value": row["dep_code"]}
    for _, row in DATA["dep_lookup"].sort_values("dep_nom").iterrows()
]
VISIBLE = {"display": "block", "padding": "20px 30px"}
HIDDEN = {"display": "none"} 
app.layout = html.Div([
    # Bandeau titre
    make_header(),

    # Barre de filtres (année, zone, département) — masquée sur l'onglet Constat
    make_filterbar(min_year=2016, max_year=2024),

    # Navigation par onglets (les Tab sont vides : le contenu est dans
    # les 4 Div ci-dessous, affichés/masqués par le callback switch_tab.
    # Cette approche "pre-render + toggle" évite de reconstruire le DOM
    # à chaque changement d'onglet — c'est plus fluide pour l'utilisateur.)
    dbc.Tabs(id="main-tabs", active_tab="tab-1", className="custom-tabs", children=[
        dbc.Tab(label="Le Constat", tab_id="tab-1"),
        dbc.Tab(label="La Fracture", tab_id="tab-2"),
        dbc.Tab(label="Les Patientes", tab_id="tab-3"),
        dbc.Tab(label="L'Offre de soins", tab_id="tab-4"),
    ]),

    # Les 4 onglets sont rendus une seule fois au démarrage.
    # Un seul est visible à la fois, les autres sont masqués (display:none).
    html.Div(id="content-tab-1", style=VISIBLE, children=tab1_constat.layout()),
    html.Div(id="content-tab-2", style=HIDDEN, children=tab2_fracture.layout()),
    html.Div(id="content-tab-3", style=HIDDEN, children=tab3_patientes.layout()),
    html.Div(id="content-tab-4", style=HIDDEN, children=tab4_offre.layout()),

    # Panneau latéral de détail département (caché par défaut)
    make_drawer(),

    # Pied de page avec rappels méthodologiques
    make_footer(),
])


# ══════════════════════════════════════════════════════════════
# CALLBACKS — Toute l'interactivité du dashboard
# ══════════════════════════════════════════════════════════════

# ── 1) Remplissage du dropdown département ────────────────────
@app.callback(
    Output("content-tab-1", "style"),
    Output("content-tab-2", "style"),
    Output("content-tab-3", "style"),
    Output("content-tab-4", "style"),
    Output("filter-bar", "style"),
    Input("main-tabs", "active_tab"),
)
def switch_tab(active_tab):
    tab_map = {"tab-1": 0, "tab-2": 1, "tab-3": 2, "tab-4": 3}
    styles = [HIDDEN, HIDDEN, HIDDEN, HIDDEN]
    idx = tab_map.get(active_tab, 0)
    styles[idx] = VISIBLE

    # L'onglet Constat est une vue d'ensemble statique, les filtres
    # n'ont pas de sens ici — on les masque pour ne pas surcharger la page.
    # Ils réapparaissent dès qu'on bascule sur un onglet interactif.
    filterbar_style = HIDDEN if active_tab == "tab-1" else {"display": "flex"}

    return *styles, filterbar_style


# ── 2) Changement d'onglet ───────────────────────────────────
# ──  Remplissage du dropdown département ────────────────────
# Le dropdown est créé vide dans filterbar.py (pour éviter de coder
# en dur la liste des départements). Ce callback le remplit au premier
# rendu avec les 101 départements triés par nom. La liste _dep_options
# est construite une fois au démarrage à partir de la table dep_lookup.
@app.callback(
    Output("filter-dept", "options"),
    Input("main-tabs", "active_tab"),
)
def populate_dept_dropdown(_):
    return _dep_options 
# ── Tab 2 : bascule contenu / encart "pas de données" ────────
# Les données départementales s'arrêtent à 2023. Quand l'utilisateur
# sélectionne 2024, la carte et le classement n'ont rien à afficher.
# Plutôt que de montrer des graphiques vides, on bascule vers un
# encart informatif qui guide l'utilisateur vers les années couvertes.
@app.callback(
    Output("tab2-content", "style"),
    Output("tab2-nodata", "style"),
    Input("filter-year", "value"),
)
def toggle_tab2_content(year):
    """
    Quand les données départementales ne sont pas disponibles (2024),
    on garde le contenu visible mais flouté en arrière-plan, avec
    l'encart d'information superposé au centre. Ça maintient la densité
    visuelle de la page tout en communiquant l'absence de données.
    """
    if year is not None and 2016 <= year <= 2023:
        return {"display": "block"}, {"display": "none"}
    return (
        {"display": "block", "filter": "blur(6px)", "opacity": "0.4",
         "pointerEvents": "none"},
        {"display": "flex"},
    )

# ── 3) Mise à jour de la carte choroplèthe (onglet 2) ────────
@app.callback(
    Output("map-choropleth", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
    Input("main-tabs", "active_tab"),
)
def update_choropleth(year, zone, active_tab):
    if active_tab != "tab-2":
        return no_update
    return tab2_fracture._build_choropleth(year, zone)


# ── 4) Mise à jour du classement départemental (onglet 2) ────
@app.callback(
    Output("ranking-chart", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
    Input("main-tabs", "active_tab"),
)
def update_ranking(year, zone, active_tab):
    if active_tab != "tab-2":
        return no_update
    return tab2_fracture._build_ranking(year, zone)


# ── 5) Mise à jour de la pyramide d'âge (onglet 3) ──────────
@app.callback(
    Output("pyramid-chart", "figure"),
    Input("filter-year", "value"),
    Input("main-tabs", "active_tab"),
)
def update_pyramid(year, active_tab):
    if active_tab != "tab-3":
        return no_update
    return tab3_patientes.build_pyramid(year)


# ── 6) Mise à jour du classement mineures (onglet 3) ─────────
@app.callback(
    Output("mineures-ranking", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
    Input("main-tabs", "active_tab"),
)
def update_mineures_ranking(year, zone, active_tab):
    if active_tab != "tab-3":
        return no_update
    return tab3_patientes.build_mineures_ranking(year, zone)


# ── 7) Mise à jour du classement déserts (onglet 4) ──────────
@app.callback(
    Output("deserts-ranking", "figure"),
    Input("filter-year", "value"),
    Input("main-tabs", "active_tab"),
)
def update_deserts(year, active_tab):
    if active_tab != "tab-4":
        return no_update
    return tab4_offre.build_deserts_ranking(year)


# ── 8) Ouverture du panneau département (drill-down) ─────────
@app.callback(
    Output("dept-drawer", "is_open"),
    Output("dept-drawer", "title"),
    Output("drawer-content", "children"),
    Input("map-choropleth", "clickData"),
    Input("ranking-chart", "clickData"),
    Input("filter-dept", "value"),
    State("filter-year", "value"),
    State("dept-drawer", "is_open"),
    prevent_initial_call=True,
)
def handle_drill_down(map_click, ranking_click, dept_dropdown, year, is_open):
    """
    Ouvre le panneau latéral quand l'utilisateur clique sur un département
    dans la carte, dans le classement, ou le sélectionne dans le dropdown.
    On récupère le code département selon la source du clic, puis on
    construit le contenu du panneau avec build_drawer_content().
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    dep_code = None

    # On identifie le département selon ce qui a déclenché le callback
    if trigger_id == "map-choropleth" and map_click:
        try:
            dep_code = map_click["points"][0]["location"]
        except (KeyError, IndexError):
            return no_update, no_update, no_update

    elif trigger_id == "ranking-chart" and ranking_click:
        try:
            dep_code = ranking_click["points"][0]["customdata"]
        except (KeyError, IndexError, TypeError):
            # Plan B : on cherche par nom si le customdata n'est pas dispo
            try:
                dep_name = ranking_click["points"][0]["y"]
                lookup = DATA["dep_lookup"]
                match = lookup[lookup["dep_nom"] == dep_name]
                if not match.empty:
                    dep_code = match.iloc[0]["dep_code"]
            except (KeyError, IndexError):
                return no_update, no_update, no_update

    elif trigger_id == "filter-dept" and dept_dropdown:
        dep_code = dept_dropdown

    if dep_code is None:
        return no_update, no_update, no_update

    # Récupération du nom du département
    lookup = DATA["dep_lookup"]
    match = lookup[lookup["dep_code"] == dep_code]
    dep_nom = match.iloc[0]["dep_nom"] if not match.empty else dep_code

    # dep_year couvre 2016-2022, donc on plafonne l'année à 2022 pour ces données
    # Les feuilles 4/7/8 vont jusqu'à 2024, on garde l'année du slider
    drill_year_dep = min(year, 2022) if year else 2022

    content = build_drawer_content(
        dep_nom=dep_nom,
        dep_code=dep_code,
        annee_dep=drill_year_dep,
        annee_feuilles=year or 2024,
        dep_year=DATA["dep_year"],
        mineures=DATA["mineures"],
        age_dept=DATA["age_dept"],
        dep_2023=DATA["dep_2023"],
    )

    return True, f"Profil — {dep_nom} ({dep_code})", content


# ══════════════════════════════════════════════════════════════
# LANCEMENT LOCAL
# ══════════════════════════════════════════════════════════════

import os

if __name__ == "__main__":
    app.run(
        debug=os.getenv("DASH_DEBUG", "false").lower() == "true",
        host="0.0.0.0",
        port=8050,
    ) 