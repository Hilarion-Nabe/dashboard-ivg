"""
app.py — Dashboard IVG France (Dash + Bootstrap).

Architecture: all 4 tabs are rendered once at startup. Tab switching
toggles visibility (display:block/none) instead of swapping content.
This avoids callback conflicts in Dash 4.0.

Run locally:   python app.py
Deploy:        gunicorn app:server
"""

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# ── Data (loaded once at import) ───────────────────────────────
from data.cache import DATA

# ── Components ─────────────────────────────────────────────────
from components.header import make_header
from components.footer import make_footer
from components.filterbar import make_filterbar
from components.dept_drawer import make_drawer, build_drawer_content

# ── Pages ──────────────────────────────────────────────────────
from pages import tab1_constat, tab2_fracture, tab3_patientes, tab4_offre


# ══════════════════════════════════════════════════════════════
# APP INIT
# ══════════════════════════════════════════════════════════════

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="IVG France — Dashboard",
    update_title=None,
)

server = app.server

# ── Dept dropdown options ──────────────────────────────────────
_dep_options = [
    {"label": f"{row['dep_nom']} ({row['dep_code']})", "value": row["dep_code"]}
    for _, row in DATA["dep_lookup"].sort_values("dep_nom").iterrows()
]

VISIBLE = {"display": "block", "padding": "20px 30px"}
HIDDEN = {"display": "none"}


# ══════════════════════════════════════════════════════════════
# LAYOUT — All tabs rendered once, visibility toggled
# ══════════════════════════════════════════════════════════════

app.layout = html.Div([
    # Header
    make_header(),

    # Filter bar (sticky)
    make_filterbar(min_year=2016, max_year=2024),

    # Tabs (navigation only, no content inside)
    dbc.Tabs(id="main-tabs", active_tab="tab-1", className="custom-tabs", children=[
        dbc.Tab(label="Le Constat", tab_id="tab-1"),
        dbc.Tab(label="La Fracture", tab_id="tab-2"),
        dbc.Tab(label="Les Patientes", tab_id="tab-3"),
        dbc.Tab(label="L'Offre de soins", tab_id="tab-4"),
    ]),

    # ALL tab contents rendered at once — only one visible at a time
    html.Div(id="content-tab-1", style=VISIBLE, children=tab1_constat.layout()),
    html.Div(id="content-tab-2", style=HIDDEN, children=tab2_fracture.layout()),
    html.Div(id="content-tab-3", style=HIDDEN, children=tab3_patientes.layout()),
    html.Div(id="content-tab-4", style=HIDDEN, children=tab4_offre.layout()),

    # Drill-down drawer (offcanvas, hidden by default)
    make_drawer(),

    # Footer (permanent)
    make_footer(),
])


# ══════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════

# ── 1) Tab switching: toggle visibility ────────────────────────
@app.callback(
    Output("content-tab-1", "style"),
    Output("content-tab-2", "style"),
    Output("content-tab-3", "style"),
    Output("content-tab-4", "style"),
    Input("main-tabs", "active_tab"),
)
def switch_tab(active_tab):
    tab_map = {"tab-1": 0, "tab-2": 1, "tab-3": 2, "tab-4": 3}
    styles = [HIDDEN, HIDDEN, HIDDEN, HIDDEN]
    idx = tab_map.get(active_tab, 0)
    styles[idx] = VISIBLE
    return styles


# ── 2) Populate dept dropdown options ──────────────────────────
@app.callback(
    Output("filter-dept", "options"),
    Input("main-tabs", "active_tab"),
)
def populate_dept_dropdown(_):
    return _dep_options


# ── 3) Tab 2: Update choropleth map ───────────────────────────
@app.callback(
    Output("map-choropleth", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
)
def update_choropleth(year, zone):
    return tab2_fracture._build_choropleth(year, zone)


# ── 4) Tab 2: Update ranking ──────────────────────────────────
@app.callback(
    Output("ranking-chart", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
)
def update_ranking(year, zone):
    return tab2_fracture._build_ranking(year, zone)


# ── 5) Tab 3: Update pyramid ──────────────────────────────────
@app.callback(
    Output("pyramid-chart", "figure"),
    Input("filter-year", "value"),
)
def update_pyramid(year):
    return tab3_patientes.build_pyramid(year)


# ── 6) Tab 3: Update mineures ranking ─────────────────────────
@app.callback(
    Output("mineures-ranking", "figure"),
    Input("filter-year", "value"),
    Input("filter-zone", "value"),
)
def update_mineures_ranking(year, zone):
    return tab3_patientes.build_mineures_ranking(year, zone)


# ── 7) Tab 4: Update deserts ranking ──────────────────────────
@app.callback(
    Output("deserts-ranking", "figure"),
    Input("filter-year", "value"),
)
def update_deserts(year):
    return tab4_offre.build_deserts_ranking(year)


# ── 8) Drill-down drawer ──────────────────────────────────────
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
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    dep_code = None

    if trigger_id == "map-choropleth" and map_click:
        try:
            dep_code = map_click["points"][0]["location"]
        except (KeyError, IndexError):
            return no_update, no_update, no_update

    elif trigger_id == "ranking-chart" and ranking_click:
        try:
            dep_code = ranking_click["points"][0]["customdata"]
        except (KeyError, IndexError, TypeError):
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

    lookup = DATA["dep_lookup"]
    match = lookup[lookup["dep_code"] == dep_code]
    dep_nom = match.iloc[0]["dep_nom"] if not match.empty else dep_code

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
# RUN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
