"""
config.py — Chemins, constantes et couleurs du projet Dashboard IVG.

Ce fichier centralise toute la configuration pour éviter les
chemins en dur et les magic numbers éparpillés dans le code.
"""

from pathlib import Path 

# ── Chemins ──────────────────────────────────────────────────────
# Path() gère automatiquement les / et \ selon l'OS
ROOT = Path(__file__).resolve().parent.parent  # racine du projet  
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# Fichiers CSV sources (noms exacts tels que téléchargés)
CSV_NATIONAL_TS = RAW / "er-ivg-graf1-sept-2024.csv"       # Totaux nationaux 1990-2023
CSV_NATIONAL_TAUX = RAW / "er-ivg-graphique-2-ica0.csv"    # Taux + ICA 1990-2023
CSV_METHODES = RAW / "graf-dyn-er-ivg.csv"                  # Répartition méthodes 2016-2024
CSV_DEP_YEAR = RAW / "ivg_ods_test1.csv"                    # Départemental multi-années
CSV_DEP_2023 = RAW / "er-ivg-carte-1.csv"                   # Carte taux 2023

# ── Colonnes attendues par CSV ───────────────────────────────────
# On les documente ici pour pouvoir vérifier à la lecture

COLS_NATIONAL_TS = {
    "annee": "Années",
    "total_brut": "Total IVG brut",
    "total_sans_reprises": "Total IVG sans reprises",
    "ratio_brut": "Ratio d'avortement brut",
    "ratio_sans_reprises": "Ratio d'avortement sans reprises",
}

COLS_NATIONAL_TAUX = {
    "annee": "Années",
    "taux_1000": "IVG pour 1 000 femmes (tous âges, en %)",
    "taux_1000_sr": "IVG pour 1 000 femmes (sans reprises, en %)",
    "ica": "ICA",
    "ica_sr": "ICA (sans reprises)",
}

# Les colonnes de ce CSV ont des sauts de ligne internes
COLS_METHODES = {
    "annee": "Année",
    "hors_etab": "IVG hors établissement de santé",
    "instrumentales": "IVG instrumentales \nen établissement",
    "medicamenteuses_etab": "IVG médicamenteuses \nen établissement",
}

COLS_DEP_YEAR = {
    "departement": "Zone géographique",
    "annee_raw": "Années",
    "instru_hosp": "IVG en établissements hospitaliers - méthode instrumentale",
    "medic_hosp": "IVG en établissements hospitaliers - méthode médicamenteuse",
    "np_hosp": "IVG en établissements hospitaliers - méthode non précisée",
    "liberal": "IVG hors établissements hospitaliers - cabinet libéral",
    "centres": "IVG hors établissements hospitaliers - centres",
    "total": "TOTAL IVG-",
    "taux_recours": "taux de recours(p 1000 femmes de 15 à 49 ans)**-",
    "total_hosp": "Total IVG en établissements hospitaliers",
    "total_hors_hosp": "Total IVG hors établissements hospitaliers",
    "code_dep": "Code Officiel Département",
    "nom_region": "Nom Officiel Région",
    "code_region": "Code Officiel Région",
}

COLS_DEP_2023 = {
    "code_dep": "Code département",
    "departement": "Département de résidence",
    "taux_2023": "Taux de recours 2023  pour 1 000 femmes de 15 à 49 ans",
}

# ── Codes départements DROM ─────────────────────────────────────
DROM_CODES = {"971", "972", "973", "974", "976"}
DROM_NOMS = {
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte",
}

# ── Couleurs (palette cohérente pour tout le dashboard) ──────────
COLORS = {
    "hors_etab": "#2ecc71",         # vert — hors établissement
    "instrumentales": "#e74c3c",     # rouge — instrumentale
    "medic_etab": "#3498db",         # bleu — médicamenteuse en étab.
    "total": "#2c3e50",              # bleu foncé — total
    "total_sr": "#95a5a6",           # gris — sans reprises
    "covid": "rgba(200,200,200,0.3)",# gris transparent — bande COVID
    "drom": "#e67e22",               # orange — DROM
    "metro": "#2980b9",              # bleu — métropole
}

# ── Années repères ───────────────────────────────────────────────
ANNEE_COVID_START = 2020
ANNEE_COVID_END = 2021
ANNEE_RUPTURE_METHODO = 2020  # Changement méthode DREES