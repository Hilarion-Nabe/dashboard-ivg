"""
data/load.py — Chargement et nettoyage des 8 fichiers CSV IVG.

Reprend les conventions du prototype Streamlit (encodage, regex année,
standardisation dep_code) et ajoute le chargement des feuilles 4/7/8.
"""

import json
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

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

DROM_CODES = {"971", "972", "973", "974", "976"}


# ── Utilitaires ────────────────────────────────────────────────

def _read(path: Path, sep=";") -> pd.DataFrame:
    """Lecture CSV avec fallback encodage (BOM Windows, Latin-1)."""
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, sep=sep, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire {path}")


def _std_dep_code(code) -> str:
    """Standardise un code département : int/float/str → str zéro-paddé."""
    if pd.isna(code):
        return ""
    s = str(code).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.isdigit() and len(s) == 1:
        s = s.zfill(2)
    return s


def _comma_to_float(series: pd.Series) -> pd.Series:
    """Convertit une série avec virgules françaises en float."""
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")


# ── Chargement fichier par fichier ─────────────────────────────

def load_national_ts() -> pd.DataFrame:
    """CSV2 — Totaux IVG nationaux 1990-2023 + ratio d'avortement."""
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
    """CSV3 — Taux pour 1000 femmes + ICA, 1990-2023."""
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
    """CSV5 — Répartition méthodes/lieux, 2016-2024 (9 lignes)."""
    df = _read(FILES["methodes"])
    # Nettoyage \n dans les noms de colonnes
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]

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

    # Features dérivées
    df["total"] = df["hors_etab"] + df["instrumentales"] + df["medic_etab"]
    for col_name, col_src in [("pct_hors_etab", "hors_etab"),
                               ("pct_instrumentales", "instrumentales"),
                               ("pct_medic_etab", "medic_etab")]:
        df[col_name] = (df[col_src] / df["total"] * 100).round(1)

    df["total_medicamenteux"] = df["hors_etab"] + df["medic_etab"]
    df["pct_medicamenteux"] = (df["total_medicamenteux"] / df["total"] * 100).round(1)

    return df.sort_values("annee").reset_index(drop=True)


def load_dep_year() -> pd.DataFrame:
    """CSV1 — Départemental multi-années (2016-2022), 101 depts × 7 ans."""
    df = _read(FILES["dep_year"])

    # Extraction année numérique + résolution doublons "nouvelle méthode"
    df["annee"] = df["Années"].str.extract(r"(\d{4})")[0].astype(int)
    df["is_nouvelle_methode"] = df["Années"].str.contains("nouvelle méthode", na=False)

    mask = df.duplicated(subset=["Zone géographique", "annee"], keep=False)
    if mask.any():
        df = df[~(mask & ~df["is_nouvelle_methode"])].copy()

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

    # Supprimer colonnes lourdes (géo, codes inutiles)
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
    """CSV4 — Carte départementale 2023 (taux + géométrie)."""
    df = _read(FILES["dep_2023"])
    df["dep_code"] = df["Code département"].apply(_std_dep_code)
    df = df.rename(columns={
        "Département de résidence": "dep_nom",
        "Taux de recours 2023  pour 1 000 femmes de 15 à 49 ans": "taux_2023",
    })
    df["is_drom"] = df["dep_code"].isin(DROM_CODES)
    return df


def extract_geojson(dep_2023_df: pd.DataFrame) -> dict:
    """Extrait un GeoJSON FeatureCollection depuis la colonne `geom` de CSV4."""
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
    """Feuille 4 — Part IVG mineures (<18 ans) par zone, 2016-2024."""
    df = _read(FILES["mineures"])
    df["part_mineures"] = _comma_to_float(df["part_age_inf18"])
    df["part_age_inconnu"] = _comma_to_float(df["part_age_inc"])
    df = df.rename(columns={"annee": "annee"})
    df["annee"] = df["annee"].astype(int)

    # is_dept sera affecté APRÈS par _flag_depts_from_lookup()
    # Pour l'instant, on met False partout (sera corrigé dans cache.py)
    df["is_dept"] = False

    return df[["zone_geo", "annee", "part_mineures", "part_age_inconnu", "is_dept"]].copy()


def load_praticiens() -> pd.DataFrame:
    """Feuille 7 — Praticiens IVG par profession/mode, 2016-2024."""
    df = _read(FILES["praticiens"])
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"ANNEE": "annee"})

    # Drop trailing empty row
    df = df.dropna(subset=["annee"])
    df["annee"] = df["annee"].astype(int)

    # Rename to lowercase
    rename = {
        "CAB_GO": "cab_go", "CAB_MG": "cab_mg", "CAB_SF": "cab_sf", "CAB_AUT": "cab_aut",
        "TELE_GO": "tele_go", "TELE_MG": "tele_mg", "TELE_SF": "tele_sf", "TELE_AUT": "tele_aut",
    }
    df = df.rename(columns=rename)

    # Totaux par profession (NaN = 0 pour sommes)
    for prof in ("go", "mg", "sf"):
        df[f"total_{prof}"] = df[f"cab_{prof}"].fillna(0) + df[f"tele_{prof}"].fillna(0)
    df["total_aut"] = df["cab_aut"].fillna(0) + df["tele_aut"].fillna(0)
    df["total_prat"] = df["total_go"] + df["total_mg"] + df["total_sf"] + df["total_aut"]

    # is_dept sera affecté APRÈS par _flag_depts_from_lookup()
    df["is_dept"] = False

    return df


def load_age_dept() -> pd.DataFrame:
    """Feuille 8 — IVG par classe d'âge × département, 2016-2024."""
    df = _read(FILES["age_dept"])

    age_cols_raw = ["AGE_INF_18", "AGE_18&19", "AGE_20_24",
                    "AGE_25_29", "AGE_30_34", "AGE_35_39", "AGE_40&plus"]
    age_cols_clean = ["age_inf18", "age_18_19", "age_20_24",
                      "age_25_29", "age_30_34", "age_35_39", "age_40plus"]

    df = df.rename(columns=dict(zip(age_cols_raw, age_cols_clean)))
    df["annee"] = df["annee"].astype(int)

    # Total et parts en %
    df["total_dept"] = df[age_cols_clean].sum(axis=1)
    for col in age_cols_clean:
        pct_col = "pct_" + col.replace("age_", "")
        df[pct_col] = (df[col] / df["total_dept"] * 100).round(1)

    # is_dept sera affecté APRÈS par _flag_depts_from_lookup()
    df["is_dept"] = False

    return df


# ── Chargement complet ─────────────────────────────────────────

def load_all() -> dict:
    """Charge et nettoie les 8 fichiers. Retourne un dict de DataFrames."""
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
