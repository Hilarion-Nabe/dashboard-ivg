"""
app.py — Dashboard IVG France (Streamlit)

Lancement :  streamlit run app.py

Ce dashboard présente les données publiques de la DREES sur les IVG
en France métropolitaine et dans les DROM (2016-2024).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import load_all
from src.config import COLORS, ANNEE_COVID_START, ANNEE_COVID_END, DROM_NOMS

# ── Configuration page ───────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard IVG France",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Chargement des données (cache pour performance) ──────────────
@st.cache_data(show_spinner="Chargement des données...")
def get_data():
    return load_all()


dfs = get_data()
national_ts = dfs["national_ts"]
national_taux = dfs["national_taux"]
methodes = dfs["methodes"]
dep_year = dfs["dep_year"]
dep_2023 = dfs["dep_2023"]


# ── Utilitaire : bande COVID sur un graphique Plotly ─────────────
def add_covid_band(fig):
    """Ajoute une bande grise verticale 2020-2021 pour marquer la période COVID."""
    fig.add_vrect(
        x0=ANNEE_COVID_START - 0.5, x1=ANNEE_COVID_END + 0.5,
        fillcolor=COLORS["covid"], line_width=0,
        annotation_text="COVID", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="gray",
    )
    return fig


# ── Sidebar ──────────────────────────────────────────────────────
st.sidebar.title("📊 Dashboard IVG France")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "A — Tendance nationale (volume)",
        "B — Taux et ICA",
        "C — Méthodes et lieux",
        "D — Carte départementale 2023",
        "E — Exploration départementale",
        "📖 Méthodologie",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Sources** : DREES, SAE, PMSI, Assurance Maladie (SNDS).  \n"
    "Données publiques — septembre 2024."
)
st.sidebar.markdown(
    "⚠️ *Taux de recours ≠ accessibilité réelle.  \n"
    "Corrélation ≠ causalité.*"
)


# ══════════════════════════════════════════════════════════════════
# PAGE A — Tendance nationale (volume)
# ══════════════════════════════════════════════════════════════════
if page == "A — Tendance nationale (volume)":
    st.title("Évolution du nombre total d'IVG en France (1990–2023)")

    st.info(
        "⚠️ **Rupture méthodologique en 2020** : la DREES a modifié sa méthode de "
        "comptage. Les niveaux avant et après 2020 ne sont pas strictement comparables. "
        "La distinction « sans reprises » (hors IVG après échec d'une 1ère tentative) "
        "est disponible à partir de 2016."
    )

    # Graphique 1 : Total IVG brut
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=national_ts["annee"], y=national_ts["total_brut"],
        mode="lines+markers", name="Total IVG (brut)",
        line=dict(color=COLORS["total"], width=2.5),
        marker=dict(size=5),
    ))
    # Ajouter la série "sans reprises" (disponible à partir de 2016)
    sr = national_ts.dropna(subset=["total_sans_reprises"])
    if not sr.empty:
        fig1.add_trace(go.Scatter(
            x=sr["annee"], y=sr["total_sans_reprises"],
            mode="lines+markers", name="Sans reprises",
            line=dict(color=COLORS["total_sr"], width=2, dash="dash"),
            marker=dict(size=4),
        ))
    fig1 = add_covid_band(fig1)
    fig1.update_layout(
        yaxis_title="Nombre d'IVG",
        xaxis_title="Année",
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Graphique 2 : Ratio d'avortement (IVG / naissances vivantes)
    st.subheader("Ratio d'avortement (IVG pour 100 naissances vivantes)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=national_ts["annee"],
        y=national_ts["ratio_brut"] * 100,  # convertir en %
        mode="lines+markers", name="Ratio brut",
        line=dict(color=COLORS["total"], width=2.5),
    ))
    sr2 = national_ts.dropna(subset=["ratio_sans_reprises"])
    if not sr2.empty:
        fig2.add_trace(go.Scatter(
            x=sr2["annee"],
            y=sr2["ratio_sans_reprises"] * 100,
            mode="lines+markers", name="Ratio sans reprises",
            line=dict(color=COLORS["total_sr"], width=2, dash="dash"),
        ))
    fig2 = add_covid_band(fig2)
    fig2.update_layout(
        yaxis_title="IVG pour 100 naissances vivantes",
        xaxis_title="Année",
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Chiffres clés
    latest = national_ts[national_ts["annee"] == national_ts["annee"].max()].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total IVG (brut)", f"{int(latest['total_brut']):,}".replace(",", " "),
                delta=f"{latest['annee']:.0f}")
    col2.metric("Ratio d'avortement",
                f"{latest['ratio_brut']*100:.1f} pour 100 naissances")
    col3.metric("Record historique ?",
                "Oui" if latest["total_brut"] == national_ts["total_brut"].max() else "Non")


# ══════════════════════════════════════════════════════════════════
# PAGE B — Taux pour 1000 femmes et ICA
# ══════════════════════════════════════════════════════════════════
elif page == "B — Taux et ICA":
    st.title("Taux de recours et Indice Conjoncturel d'Avortement (1990–2023)")

    st.info(
        "L'**ICA** (Indice Conjoncturel d'Avortement) estime le nombre moyen d'IVG "
        "qu'une femme connaîtrait au cours de sa vie si les taux par âge observés "
        "une année donnée restaient constants. C'est l'analogue de l'indice "
        "conjoncturel de fécondité."
    )

    tab1, tab2 = st.tabs(["Taux pour 1 000 femmes", "ICA"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=national_taux["annee"], y=national_taux["taux_1000"],
            mode="lines+markers", name="Tous âges",
            line=dict(color=COLORS["total"], width=2.5),
        ))
        sr = national_taux.dropna(subset=["taux_1000_sr"])
        if not sr.empty:
            fig.add_trace(go.Scatter(
                x=sr["annee"], y=sr["taux_1000_sr"],
                mode="lines+markers", name="Sans reprises",
                line=dict(color=COLORS["total_sr"], width=2, dash="dash"),
            ))
        fig = add_covid_band(fig)
        fig.update_layout(
            yaxis_title="IVG pour 1 000 femmes (15-49 ans)",
            xaxis_title="Année", height=500,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=national_taux["annee"], y=national_taux["ica"],
            mode="lines+markers", name="ICA",
            line=dict(color=COLORS["total"], width=2.5),
        ))
        sr = national_taux.dropna(subset=["ica_sr"])
        if not sr.empty:
            fig.add_trace(go.Scatter(
                x=sr["annee"], y=sr["ica_sr"],
                mode="lines+markers", name="ICA sans reprises",
                line=dict(color=COLORS["total_sr"], width=2, dash="dash"),
            ))
        fig = add_covid_band(fig)
        fig.update_layout(
            yaxis_title="ICA (nombre moyen d'IVG par femme au cours de la vie)",
            xaxis_title="Année", height=500,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Chiffres clés
    latest = national_taux[national_taux["annee"] == national_taux["annee"].max()].iloc[0]
    col1, col2 = st.columns(2)
    col1.metric("Taux 2023", f"{latest['taux_1000']:.1f} ‰")
    col2.metric("ICA 2023", f"{latest['ica']:.2f}",
                help="Un ICA de 0,62 signifie qu'environ 62% des femmes connaîtraient "
                     "au moins une IVG au cours de leur vie aux taux actuels.")


# ══════════════════════════════════════════════════════════════════
# PAGE C — Méthodes et lieux
# ══════════════════════════════════════════════════════════════════
elif page == "C — Méthodes et lieux":
    st.title("Transformation des pratiques d'IVG (2016–2024)")

    st.info(
        "Les IVG hors établissement (cabinets libéraux, centres) sont quasi "
        "exclusivement réalisées par méthode médicamenteuse. La part totale de la "
        "méthode médicamenteuse = hors établissement + médicamenteuse en établissement."
    )

    # Graphique empilé en aires (stacked area)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=methodes["annee"], y=methodes["hors_etab"],
        mode="lines", name="Hors établissement",
        line=dict(width=0.5, color=COLORS["hors_etab"]),
        stackgroup="one",
        hovertemplate="%{y:,.0f} (%{customdata:.1f}%)",
        customdata=methodes["pct_hors_etab"],
    ))
    fig.add_trace(go.Scatter(
        x=methodes["annee"], y=methodes["medic_etab"],
        mode="lines", name="Médicamenteuse (en étab.)",
        line=dict(width=0.5, color=COLORS["medic_etab"]),
        stackgroup="one",
        hovertemplate="%{y:,.0f} (%{customdata:.1f}%)",
        customdata=methodes["pct_medic_etab"],
    ))
    fig.add_trace(go.Scatter(
        x=methodes["annee"], y=methodes["instrumentales"],
        mode="lines", name="Instrumentale (en étab.)",
        line=dict(width=0.5, color=COLORS["instrumentales"]),
        stackgroup="one",
        hovertemplate="%{y:,.0f} (%{customdata:.1f}%)",
        customdata=methodes["pct_instrumentales"],
    ))
    fig = add_covid_band(fig)
    fig.update_layout(
        yaxis_title="Nombre d'IVG",
        xaxis_title="Année", height=500,
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Parts en pourcentage (bar chart empilé)
    st.subheader("Parts relatives (%)")
    fig2 = go.Figure()
    for col, name, color in [
        ("pct_hors_etab", "Hors établissement", COLORS["hors_etab"]),
        ("pct_medic_etab", "Médicamenteuse (étab.)", COLORS["medic_etab"]),
        ("pct_instrumentales", "Instrumentale (étab.)", COLORS["instrumentales"]),
    ]:
        fig2.add_trace(go.Bar(
            x=methodes["annee"], y=methodes[col],
            name=name, marker_color=color,
            text=methodes[col].apply(lambda v: f"{v:.0f}%"),
            textposition="inside",
        ))
    fig2.update_layout(
        barmode="stack", yaxis_title="%", xaxis_title="Année",
        height=400, yaxis=dict(range=[0, 105]),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Chiffres clés
    latest = methodes[methodes["annee"] == methodes["annee"].max()].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Part hors établissement", f"{latest['pct_hors_etab']:.0f}%",
                delta=f"vs {methodes[methodes['annee']==2016].iloc[0]['pct_hors_etab']:.0f}% en 2016")
    col2.metric("Part médicamenteux total", f"{latest['pct_medicamenteux']:.0f}%")
    col3.metric(f"Total IVG {int(latest['annee'])}", f"{int(latest['total']):,}".replace(",", " "))


# ══════════════════════════════════════════════════════════════════
# PAGE D — Carte départementale 2023
# ══════════════════════════════════════════════════════════════════
elif page == "D — Carte départementale 2023":
    st.title("Taux de recours à l'IVG par département (2023)")

    st.info(
        "⚠️ Un taux élevé ne signifie pas nécessairement un meilleur accès. "
        "Les écarts reflètent des facteurs multiples : socio-économiques, "
        "démographiques, culturels, et d'offre de soins."
    )

    # Choix d'affichage
    zone = st.radio(
        "Zone géographique :",
        ["Tous", "Métropole uniquement", "DROM uniquement"],
        horizontal=True,
    )

    if zone == "Métropole uniquement":
        data = dep_2023[~dep_2023["is_drom"]]
    elif zone == "DROM uniquement":
        data = dep_2023[dep_2023["is_drom"]]
    else:
        data = dep_2023

    # Bar chart horizontal (fallback robuste — marche toujours)
    data_sorted = data.sort_values("taux_2023", ascending=True)

    # Couleur conditionnelle : DROM en orange, métropole en bleu
    colors = data_sorted["is_drom"].map({True: COLORS["drom"], False: COLORS["metro"]})

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=data_sorted["departement"],
        x=data_sorted["taux_2023"],
        orientation="h",
        marker_color=colors,
        text=data_sorted["taux_2023"].apply(lambda v: f"{v:.1f} ‰"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Taux : %{x:.1f} ‰<extra></extra>",
    ))

    # Ligne médiane
    mediane = data["taux_2023"].median()
    fig.add_vline(x=mediane, line_dash="dash", line_color="red",
                  annotation_text=f"Médiane : {mediane:.1f} ‰",
                  annotation_position="top right")

    fig.update_layout(
        xaxis_title="Taux de recours (‰ femmes 15-49 ans)",
        height=max(400, len(data) * 22),  # Ajuster la hauteur au nombre de depts
        margin=dict(l=200),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stats résumées
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Min", f"{data['taux_2023'].min():.1f} ‰",
                help=data.loc[data["taux_2023"].idxmin(), "departement"])
    col2.metric("Médiane", f"{mediane:.1f} ‰")
    col3.metric("Moyenne", f"{data['taux_2023'].mean():.1f} ‰")
    col4.metric("Max", f"{data['taux_2023'].max():.1f} ‰",
                help=data.loc[data["taux_2023"].idxmax(), "departement"])


# ══════════════════════════════════════════════════════════════════
# PAGE E — Exploration départementale
# ══════════════════════════════════════════════════════════════════
elif page == "E — Exploration départementale":
    st.title("Exploration par département (2016–2022)")

    st.info(
        "⚠️ La rupture méthodologique de 2020 affecte les niveaux absolus. "
        "Les tendances relatives restent interprétables avec prudence."
    )

    # Filtres
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        regions = sorted(dep_year["region"].dropna().unique())
        sel_region = st.selectbox("Région :", ["Toutes"] + regions)
    with col_f2:
        if sel_region != "Toutes":
            depts = sorted(dep_year[dep_year["region"] == sel_region]["departement"].unique())
        else:
            depts = sorted(dep_year["departement"].unique())
        sel_depts = st.multiselect("Département(s) :", depts, default=depts[:3])

    if not sel_depts:
        st.warning("Sélectionne au moins un département.")
        st.stop()

    filtered = dep_year[dep_year["departement"].isin(sel_depts)]

    # Graphique 1 : Taux de recours
    st.subheader("Taux de recours (‰ femmes 15-49 ans)")
    fig = px.line(
        filtered, x="annee", y="taux_recours",
        color="departement", markers=True,
        labels={"annee": "Année", "taux_recours": "Taux ‰", "departement": "Département"},
    )
    fig = add_covid_band(fig)
    fig.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # Graphique 2 : Répartition lieu (hospitalier vs hors hospitalier)
    st.subheader("Répartition hospitalier / hors hospitalier")
    if len(sel_depts) == 1:
        dept_data = filtered.copy()
        dept_data["pct_hors_hosp"] = (dept_data["total_hors_hosp"] / dept_data["total_ivg"] * 100).round(1)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=dept_data["annee"], y=dept_data["total_hosp"],
            name="Hospitalier", marker_color=COLORS["medic_etab"],
        ))
        fig2.add_trace(go.Bar(
            x=dept_data["annee"], y=dept_data["total_hors_hosp"],
            name="Hors hospitalier", marker_color=COLORS["hors_etab"],
        ))
        fig2.update_layout(barmode="stack", height=400, xaxis_title="Année", yaxis_title="Nombre d'IVG")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        # Comparaison multi-départements : % hors hospitalier
        filtered_pct = filtered.copy()
        filtered_pct["pct_hors_hosp"] = (filtered_pct["total_hors_hosp"] / filtered_pct["total_ivg"] * 100).round(1)
        fig2 = px.line(
            filtered_pct, x="annee", y="pct_hors_hosp",
            color="departement", markers=True,
            labels={"pct_hors_hosp": "% hors hospitalier", "annee": "Année"},
        )
        fig2.update_layout(height=400, hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)

    # Tableau récapitulatif
    st.subheader("Données brutes")
    cols_display = ["departement", "annee", "total_ivg", "taux_recours",
                    "total_hosp", "total_hors_hosp", "instru_hosp", "medic_hosp"]
    cols_present = [c for c in cols_display if c in filtered.columns]
    st.dataframe(
        filtered[cols_present].sort_values(["departement", "annee"]),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE Méthodologie
# ══════════════════════════════════════════════════════════════════
elif page == "📖 Méthodologie":
    st.title("Méthodologie et limites")

    st.header("Comment lire ce dashboard ?")
    st.markdown("""
Ce dashboard présente les données publiques de la DREES sur les Interruptions
Volontaires de Grossesse (IVG) en France métropolitaine et dans les DROM
(Guadeloupe, Martinique, Guyane, La Réunion, Mayotte).

Les indicateurs présentés sont :

- Le **nombre total d'IVG** (brut, et « sans reprises » lorsque disponible).
- Le **taux de recours** (IVG pour 1 000 femmes de 15 à 49 ans).
- Le **ratio d'avortement** (IVG pour 100 naissances vivantes).
- L'**ICA** (Indice Conjoncturel d'Avortement) : nombre moyen d'IVG qu'une femme
  connaîtrait au cours de sa vie aux taux actuels par âge.
- La **répartition par méthode** (instrumentale vs. médicamenteuse) et par **lieu**
  (établissement hospitalier vs. hors établissement).
    """)

    st.header("Limites et précautions")

    st.warning("**Taux de recours ≠ accessibilité réelle**")
    st.markdown("""
Un taux de recours élevé dans un département ne signifie pas nécessairement un
meilleur accès à l'IVG. Il peut refléter des facteurs socio-économiques,
démographiques ou culturels. Inversement, un taux bas peut masquer des difficultés
d'accès (manque de praticiens, éloignement géographique).
    """)

    st.warning("**Rupture méthodologique autour de 2020**")
    st.markdown("""
À partir de 2020, la DREES a modifié sa méthode de comptage (intégration des
remontées SNDS pour les IVG en libéral). Pour 2020 et 2021, les deux méthodes
coexistent. Les comparaisons avant/après 2020 doivent être faites avec précaution.
    """)

    st.warning("**DROM vs. Métropole**")
    st.markdown("""
Les DROM présentent des taux significativement plus élevés que la métropole.
Ces écarts reflètent des contextes spécifiques qui ne sont pas directement
comparables à la situation métropolitaine.
    """)

    st.warning("**Corrélation ≠ causalité**")
    st.markdown("""
Les variations observées sont **descriptives**. Elles ne permettent pas d'identifier
des relations de cause à effet sans analyses complémentaires contrôlant les
facteurs confondants.
    """)

    st.header("Sources")
    st.markdown("""
- **DREES** (Direction de la recherche, des études, de l'évaluation et des statistiques) :
  *Les interruptions volontaires de grossesse en 2023 — Résultats définitifs*, Études & Résultats, septembre 2024.
- **SAE** (Statistique annuelle des établissements de santé).
- **PMSI** (Programme de médicalisation des systèmes d'information).
- **SNDS** (Système national des données de santé) via l'Assurance Maladie.
    """)


# ── Footer global ────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("Dashboard réalisé à des fins d'analyse descriptive. "
                    "Ne constitue pas un avis médical.") 
                    