"""
data/load.py — Lecture et nettoyage des 8 fichiers CSV du projet.

On a 8 fichiers sources dans data/raw/, chacun avec un format un peu
différent (séparateurs, encodage, noms de colonnes). Ce module s'occupe
de tous les lire proprement et de les ramener à un format homogène
avec des noms de colonnes normalisés.

Le gros du travail c'est de gérer les cas particuliers :
  - les virgules françaises dans les décimales (ex: "3,5" au lieu de 3.5)
  - les codes départements en 2A/2B pour la Corse
  - la double méthode de comptage en 2020 (doublons à résoudre)
  - les lignes vides en fin de fichier sur certains CSV
"""

import json
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

# ── Chemins vers les fichiers sources ─────────────────────────
# ROOT pointe vers le dossier racine du projet (ivg_dash/)
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# Dictionnaire des 8 CSV avec un nom lisible pour chacun
FILES = {
    "national_ts":  RAW / "er-ivg-graf1-sept-2024.csv",
    "national_taux": RAW / "er-ivg-graphique-2-ica0.csv",
    "methodes":     RAW / "graf-dyn-er-ivg.csv",
    "dep_year":     RAW / "ivg_ods_test1.csv",
    "dep_2023":     RAW / "er-ivg-carte-1.csv",
    "mineures":     RAW / "donnees_feuil4.csv",
    "praticiens":   RAW / "donnees_feuil7.csv",
    "age_dept":     RAW / "donnees_feuil8.csv",
}

# Les 5 départements d'Outre-mer (DROM)
DROM_CODES = {"971", "972", "973", "974", "976"}


# ── Fonctions utilitaires ─────────────────────────────────────

def _read(path: Path, sep=";") -> pd.DataFrame:
    """
    Lit un CSV en essayant plusieurs encodages.
    Les fichiers de la DREES sont parfois en UTF-8 avec BOM,
    parfois en Latin-1... on essaye les trois encodages courants
    et on garde celui qui marche.
    """
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, sep=sep, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire {path}")


def _std_dep_code(code) -> str:
    """
    Normalise un code département vers un format string propre.
    Exemples : 1 → "01", 2A → "2A", 971.0 → "971"

    C'est nécessaire parce que selon les CSV, le code peut arriver
    en int (1), en float (1.0), ou en string ("01"), et il faut
    que ce soit cohérent partout pour les jointures entre tables.
    """
    if pd.isna(code):
        return ""
    s = str(code).strip()
    # pandas lit parfois "1" comme 1.0, on enlève le .0
    if s.endswith(".0"):
        s = s[:-2]
    # Les départements 1 à 9 doivent être sur 2 caractères (01, 02...)
    if s.isdigit() and len(s) == 1:
        s = s.zfill(2)
    return s


def _comma_to_float(series: pd.Series) -> pd.Series:
    """
    Convertit une colonne avec des virgules françaises en float.
    Ex: "4,3" → 4.3. Utile pour les feuilles 4/7/8 de la DREES
    qui utilisent la notation française.
    """
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")


# ── Chargement de chaque fichier ──────────────────────────────

def load_national_ts() -> pd.DataFrame:
    """
    Charge les totaux nationaux d'IVG de 1990 à 2023.
    Contient le nombre brut d'IVG, la version "sans reprises"
    (disponible à partir de 2016), et le ratio IVG/naissances.
    """
    df = _read(FILES["national_ts"])
    df = df.rename(columns={
        "Années": "annee",
        "Total IVG brut": "total_brut",
        "Total IVG sans reprises": "total_sans_reprises",
        "Ratio d'avortement brut": "ratio_brut",
        "Ratio d'avortement sans reprises": "ratio_sans_reprises",
    })
    df["annee"] = df["annee"].astype(int)
    return df.sort_values("annee").reset_index(drop=True)


def load_national_taux() -> pd.DataFrame:
    """
    Charge les taux de recours (pour 1000 femmes 15-49 ans)
    et l'ICA (Indice Conjoncturel d'Avortement) de 1990 à 2023.
    L'ICA c'est l'analogue de l'indice de fécondité mais pour l'IVG.
    """
    df = _read(FILES["national_taux"])
    df = df.rename(columns={
        "Années": "annee",
        "IVG pour 1 000 femmes (tous âges, en %)": "taux_1000",
        "IVG pour 1 000 femmes (sans reprises, en %)": "taux_1000_sr",
        "ICA": "ica",
        "ICA (sans reprises)": "ica_sr",
    })
    df["annee"] = df["annee"].astype(int)
    return df.sort_values("annee").reset_index(drop=True)


def load_methodes() -> pd.DataFrame:
    """
    Charge la répartition nationale des IVG par méthode et lieu
    (2016-2024, 9 lignes seulement).
    Trois catégories : hors établissement, instrumentale en étab.,
    médicamenteuse en étab.
    On calcule aussi les pourcentages correspondants.
    """
    df = _read(FILES["methodes"])
    # Les noms de colonnes contiennent parfois des \n, on nettoie
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]

    # Renommage des colonnes (on cherche par mot-clé car les noms
    # exacts changent selon les versions du fichier DREES)
    rename_map = {}
    for col in df.columns:
        cl = col.lower()
        if "année" in cl or "annee" in cl:
            rename_map[col] = "annee"
        elif "hors" in cl:
            rename_map[col] = "hors_etab"
        elif "instrumental" in cl:
            rename_map[col] = "instrumentales"
        elif "médicament" in cl or "medicament" in cl:
            rename_map[col] = "medic_etab"
    df = df.rename(columns=rename_map)
    df["annee"] = df["annee"].astype(int)

    # Colonnes dérivées : total et pourcentages
    df["total"] = df["hors_etab"] + df["instrumentales"] + df["medic_etab"]
    for col_name, col_src in [("pct_hors_etab", "hors_etab"),
                               ("pct_instrumentales", "instrumentales"),
                               ("pct_medic_etab", "medic_etab")]:
        df[col_name] = (df[col_src] / df["total"] * 100).round(1)

    # Part totale du médicamenteux = hors étab (quasi 100% médic.) + médic. en étab.
    df["total_medicamenteux"] = df["hors_etab"] + df["medic_etab"]
    df["pct_medicamenteux"] = (df["total_medicamenteux"] / df["total"] * 100).round(1)

    return df.sort_values("annee").reset_index(drop=True)


def load_dep_year() -> pd.DataFrame:
    """
    Charge le gros fichier départemental multi-années (2016-2022).
    C'est le fichier le plus lourd (~9 Mo brut), 101 départements × 7 ans.

    Particularité : en 2020-2021, il y a des doublons car la DREES
    a publié les chiffres avec l'ancienne ET la nouvelle méthode.
    On garde la "nouvelle méthode" quand il y a doublon.
    """
    df = _read(FILES["dep_year"])

    # L'année est dans un champ texte du style "2020 (nouvelle méthode)"
    # On extrait juste le nombre avec une regex
    df["annee"] = df["Années"].str.extract(r"(\d{4})")[0].astype(int)
    df["is_nouvelle_methode"] = df["Années"].str.contains("nouvelle méthode", na=False)

    # Gestion des doublons 2020-2021 : on garde la nouvelle méthode
    mask = df.duplicated(subset=["Zone géographique", "annee"], keep=False)
    if mask.any():
        df = df[~(mask & ~df["is_nouvelle_methode"])].copy()

    # Normalisation du code département
    df["dep_code"] = df["Code Officiel Département"].apply(_std_dep_code)
    df["is_drom"] = df["dep_code"].isin(DROM_CODES)

    df = df.rename(columns={
        "Zone géographique": "dep_nom",
        "TOTAL IVG-": "total_ivg",
        "taux de recours(p 1000 femmes de 15 à 49 ans)**-": "taux_recours",
        "Total IVG en établissements hospitaliers": "total_hosp",
        "Total IVG hors établissements hospitaliers": "total_hors_hosp",
        "IVG en établissements hospitaliers - méthode instrumentale": "instru_hosp",
        "IVG en établissements hospitaliers - méthode médicamenteuse": "medic_hosp",
        "Nom Officiel Région": "region",
    })

    # On vire les colonnes lourdes qui ne servent pas au dashboard
    # (géométries, codes redondants, colonnes détail inutilisées)
    drop = [c for c in df.columns if c in (
        "Geo Shape", "geo_point_2d", "Code Officiel Région",
        "Code Officiel Département", "Années", "is_nouvelle_methode",
        "IVG en établissements hospitaliers - méthode non précisée",
        "IVG hors établissements hospitaliers - cabinet libéral",
        "IVG hors établissements hospitaliers - centres",
    )]
    df = df.drop(columns=drop, errors="ignore")

    return df.sort_values(["annee", "dep_nom"]).reset_index(drop=True)


def load_dep_2023() -> pd.DataFrame:
    """
    Charge la carte départementale 2023 (taux + géométrie GeoJSON).
    Ce fichier contient la colonne `geom` avec le contour de chaque
    département — c'est ce qui permet d'afficher la carte choroplèthe.
    """
    df = _read(FILES["dep_2023"])
    df["dep_code"] = df["Code département"].apply(_std_dep_code)
    df = df.rename(columns={
        "Département de résidence": "dep_nom",
        "Taux de recours 2023  pour 1 000 femmes de 15 à 49 ans": "taux_2023",
    })
    df["is_drom"] = df["dep_code"].isin(DROM_CODES)
    return df


def extract_geojson(dep_2023_df: pd.DataFrame) -> dict:
    """
    Transforme la colonne `geom` du CSV carte en un vrai GeoJSON
    (FeatureCollection) utilisable par Plotly pour la choroplèthe.
    On parcourt chaque ligne et on parse le JSON de la géométrie.
    """
    features = []
    for _, row in dep_2023_df.iterrows():
        try:
            geom = json.loads(row["geom"]) if isinstance(row["geom"], str) else None
        except (json.JSONDecodeError, TypeError):
            geom = None
        if geom:
            features.append({
                "type": "Feature",
                "id": row["dep_code"],
                "properties": {
                    "dep_code": row["dep_code"],
                    "dep_nom": row["dep_nom"],
                },
                "geometry": geom,
            })
    return {"type": "FeatureCollection", "features": features}


def load_mineures() -> pd.DataFrame:
    """
    Charge la feuille 4 — part des IVG chez les mineures (<18 ans)
    par zone géographique, de 2016 à 2024.
    Attention : ce fichier mélange départements, régions et totaux nationaux
    dans la même colonne zone_geo. Le tri se fait plus tard dans cache.py.
    """
    df = _read(FILES["mineures"])
    df["part_mineures"] = _comma_to_float(df["part_age_inf18"])
    df["part_age_inconnu"] = _comma_to_float(df["part_age_inc"])
    df = df.rename(columns={"annee": "annee"})
    df["annee"] = df["annee"].astype(int)

    # Le flag is_dept sera mis à jour plus tard avec la table de correspondance
    # (on ne peut pas deviner ici quelles lignes sont des départements)
    df["is_dept"] = False

    return df[["zone_geo", "annee", "part_mineures", "part_age_inconnu", "is_dept"]].copy()


def load_praticiens() -> pd.DataFrame:
    """
    Charge la feuille 7 — nombre de praticiens IVG par type
    (gynéco, généraliste, sage-femme) et par mode (cabinet, téléconsultation).
    Couvre 2016 à 2024.

    Même problème que load_mineures() : la colonne zone_geo mélange
    départements et régions, le tri se fait après.
    """
    df = _read(FILES["praticiens"])
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"ANNEE": "annee"})

    # Certains fichiers ont une ligne vide à la fin, on la vire
    df = df.dropna(subset=["annee"])
    df["annee"] = df["annee"].astype(int)

    # Passage en minuscules pour les noms de colonnes praticiens
    rename = {
        "CAB_GO": "cab_go", "CAB_MG": "cab_mg", "CAB_SF": "cab_sf", "CAB_AUT": "cab_aut",
        "TELE_GO": "tele_go", "TELE_MG": "tele_mg", "TELE_SF": "tele_sf", "TELE_AUT": "tele_aut",
    }
    df = df.rename(columns=rename)

    # Totaux par profession : cabinet + téléconsultation (NaN = 0 pour les sommes)
    for prof in ("go", "mg", "sf"):
        df[f"total_{prof}"] = df[f"cab_{prof}"].fillna(0) + df[f"tele_{prof}"].fillna(0)
    df["total_aut"] = df["cab_aut"].fillna(0) + df["tele_aut"].fillna(0)
    df["total_prat"] = df["total_go"] + df["total_mg"] + df["total_sf"] + df["total_aut"]

    # Même logique que les autres feuilles : is_dept sera corrigé après
    df["is_dept"] = False

    return df


def load_age_dept() -> pd.DataFrame:
    """
    Charge la feuille 8 — nombre d'IVG par tranche d'âge et par département.
    Couvre 2016 à 2024.
    On calcule aussi la part de chaque tranche en pourcentage.
    """
    df = _read(FILES["age_dept"])

    age_cols_raw = ["AGE_INF_18", "AGE_18&19", "AGE_20_24",
                    "AGE_25_29", "AGE_30_34", "AGE_35_39", "AGE_40&plus"]
    age_cols_clean = ["age_inf18", "age_18_19", "age_20_24",
                      "age_25_29", "age_30_34", "age_35_39", "age_40plus"]

    df = df.rename(columns=dict(zip(age_cols_raw, age_cols_clean)))
    df["annee"] = df["annee"].astype(int)

    # Total par zone + parts en pourcentage pour chaque tranche
    df["total_dept"] = df[age_cols_clean].sum(axis=1)
    for col in age_cols_clean:
        pct_col = "pct_" + col.replace("age_", "")
        df[pct_col] = (df[col] / df["total_dept"] * 100).round(1)

    # is_dept sera corrigé dans cache.py via la table de correspondance
    df["is_dept"] = False

    return df


# ── Fonction principale : tout charger d'un coup ─────────────

def load_all() -> dict:
    """
    Charge et nettoie les 8 fichiers CSV.
    Renvoie un dictionnaire avec un DataFrame par fichier.
    Appelée une seule fois au démarrage de l'appli.
    """
    print("Chargement des données IVG...")
    dfs = {
        "national_ts":  load_national_ts(),
        "national_taux": load_national_taux(),
        "methodes":     load_methodes(),
        "dep_year":     load_dep_year(),
        "dep_2023":     load_dep_2023(),
        "mineures":     load_mineures(),
        "praticiens":   load_praticiens(),
        "age_dept":     load_age_dept(),
    }
    print("  ✓ 8 fichiers chargés")
    return dfs
