"""
data_loader.py — Chargement, nettoyage et standardisation des 5 CSV IVG.

Chaque fonction lit UN fichier CSV, nettoie les colonnes, standardise
les types, et retourne un DataFrame propre. La fonction load_all()
orchestre le tout et retourne un dictionnaire de DataFrames.

Usage :
    from src.data_loader import load_all
    dfs = load_all()
    national_ts = dfs["national_ts"]
"""

import pandas as pd
import warnings
from pathlib import Path
from src.config import (
    CSV_NATIONAL_TS, CSV_NATIONAL_TAUX, CSV_METHODES,
    CSV_DEP_YEAR, CSV_DEP_2023, PROCESSED, DROM_CODES,
)


# ── Utilitaire de lecture CSV robuste ────────────────────────────

def _read_csv_safe(path: Path, sep: str = ";") -> pd.DataFrame:
    """
    Lit un CSV en essayant utf-8-sig puis latin-1.
    utf-8-sig gère le BOM Windows qui traîne souvent dans les CSV
    téléchargés depuis des sites français (data.gouv, DREES, etc.).
    """
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, sep=sep, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire {path} avec utf-8-sig, latin-1 ou cp1252.")


def _standardize_dep_code(code) -> str:
    """
    Standardise un code département en chaîne de 2-3 caractères.
    Gère : int 1→'01', float 1.0→'01', str '1'→'01', '2A'→'2A', '971'→'971'.
    """
    if pd.isna(code):
        return ""
    s = str(code).strip()
    # Retirer le .0 éventuel des floats lus comme numériques
    if s.endswith(".0"):
        s = s[:-2]
    # Zéro-padding pour les départements 1-9 (pas pour les DROM 97x)
    if s.isdigit() and len(s) == 1:
        s = s.zfill(2)
    elif s.isdigit() and len(s) == 2:
        s = s.zfill(2)
    return s


# ── Chargement de chaque CSV ─────────────────────────────────────

def load_national_ts() -> pd.DataFrame:
    """
    Fichier : er-ivg-graf1-sept-2024.csv
    Contenu : totaux IVG nationaux 1990-2023, ratio d'avortement.
    """
    df = _read_csv_safe(CSV_NATIONAL_TS)

    # Vérification minimale
    assert "Années" in df.columns, f"Colonne 'Années' absente. Colonnes trouvées : {df.columns.tolist()}"

    # Nettoyage
    df = df.rename(columns={
        "Années": "annee",
        "Total IVG brut": "total_brut",
        "Total IVG sans reprises": "total_sans_reprises",
        "Ratio d'avortement brut": "ratio_brut",
        "Ratio d'avortement sans reprises": "ratio_sans_reprises",
    })
    df["annee"] = df["annee"].astype(int)
    df = df.sort_values("annee").reset_index(drop=True)

    print(f"  ✓ national_ts : {len(df)} lignes, {df['annee'].min()}-{df['annee'].max()}")
    return df


def load_national_taux() -> pd.DataFrame:
    """
    Fichier : er-ivg-graphique-2-ica0.csv
    Contenu : taux pour 1000 femmes + ICA, 1990-2023.
    """
    df = _read_csv_safe(CSV_NATIONAL_TAUX)

    df = df.rename(columns={
        "Années": "annee",
        "IVG pour 1 000 femmes (tous âges, en %)": "taux_1000",
        "IVG pour 1 000 femmes (sans reprises, en %)": "taux_1000_sr",
        "ICA": "ica",
        "ICA (sans reprises)": "ica_sr",
    })
    df["annee"] = df["annee"].astype(int)
    df = df.sort_values("annee").reset_index(drop=True)

    print(f"  ✓ national_taux : {len(df)} lignes, {df['annee'].min()}-{df['annee'].max()}")
    return df


def load_methodes() -> pd.DataFrame:
    """
    Fichier : graf-dyn-er-ivg.csv
    Contenu : répartition hors étab / instrumentale / médicamenteuse, 2016-2024.
    Attention : les noms de colonnes contiennent des sauts de ligne.
    """
    df = _read_csv_safe(CSV_METHODES)

    # Les colonnes ont des \n internes — on les nettoie d'abord
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]

    # Renommage robuste : chercher par sous-chaîne si le nom exact ne matche pas
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "année" in col_lower or "annee" in col_lower:
            rename_map[col] = "annee"
        elif "hors" in col_lower:
            rename_map[col] = "hors_etab"
        elif "instrumental" in col_lower:
            rename_map[col] = "instrumentales"
        elif "médicament" in col_lower or "medicament" in col_lower:
            rename_map[col] = "medic_etab"

    df = df.rename(columns=rename_map)

    # Vérification
    attendues = {"annee", "hors_etab", "instrumentales", "medic_etab"}
    manquantes = attendues - set(df.columns)
    if manquantes:
        warnings.warn(f"Colonnes manquantes dans methodes : {manquantes}. Colonnes trouvées : {df.columns.tolist()}")

    df["annee"] = df["annee"].astype(int)

    # Calculs dérivés
    df["total"] = df["hors_etab"] + df["instrumentales"] + df["medic_etab"]
    df["pct_hors_etab"] = (df["hors_etab"] / df["total"] * 100).round(1)
    df["pct_instrumentales"] = (df["instrumentales"] / df["total"] * 100).round(1)
    df["pct_medic_etab"] = (df["medic_etab"] / df["total"] * 100).round(1)
    # Part totale médicamenteuse (hors étab = quasi 100% médicamenteux)
    df["total_medicamenteux"] = df["hors_etab"] + df["medic_etab"]
    df["pct_medicamenteux"] = (df["total_medicamenteux"] / df["total"] * 100).round(1)

    df = df.sort_values("annee").reset_index(drop=True)
    print(f"  ✓ methodes : {len(df)} lignes, {df['annee'].min()}-{df['annee'].max()}")
    return df


def load_dep_year() -> pd.DataFrame:
    """
    Fichier : ivg_ods_test1.csv
    Contenu : données départementales multi-années (2016-2022), par méthode et lieu.
    Gère la colonne 'Années' qui contient parfois 'nouvelle méthode'.
    """
    df = _read_csv_safe(CSV_DEP_YEAR)

    # Extraire l'année numérique (ex: "2020  nouvelle méthode" → 2020)
    df["annee"] = df["Années"].str.extract(r"(\d{4})")[0].astype(int)
    df["is_nouvelle_methode"] = df["Années"].str.contains("nouvelle méthode", na=False)

    # Pour les années où les deux méthodes coexistent (2020, 2021),
    # on garde la "nouvelle méthode" pour la cohérence avec 2022+
    mask_doublon = df.duplicated(subset=["Zone géographique", "annee"], keep=False)
    if mask_doublon.any():
        # Garder nouvelle méthode quand disponible
        df = df[~(mask_doublon & ~df["is_nouvelle_methode"])].copy()
        print("  ⚠ Doublons 2020/2021 résolus (nouvelle méthode conservée)")

    # Standardiser le code département
    df["code_dep"] = df["Code Officiel Département"].apply(_standardize_dep_code)

    # Flag DROM
    df["is_drom"] = df["code_dep"].isin(DROM_CODES)

    # Renommage des colonnes clés pour lisibilité
    df = df.rename(columns={
        "Zone géographique": "departement",
        "TOTAL IVG-": "total_ivg",
        "taux de recours(p 1000 femmes de 15 à 49 ans)**-": "taux_recours",
        "Total IVG en établissements hospitaliers": "total_hosp",
        "Total IVG hors établissements hospitaliers": "total_hors_hosp",
        "IVG en établissements hospitaliers - méthode instrumentale": "instru_hosp",
        "IVG en établissements hospitaliers - méthode médicamenteuse": "medic_hosp",
        "Nom Officiel Région": "region",
    })

    # Supprimer les colonnes géographiques lourdes (inutiles pour le dashboard)
    cols_drop = [c for c in df.columns if c in ("Geo Shape", "geo_point_2d", "Code Officiel Région")]
    df = df.drop(columns=cols_drop, errors="ignore")

    df = df.sort_values(["annee", "departement"]).reset_index(drop=True)
    print(f"  ✓ dep_year : {len(df)} lignes, {df['annee'].nunique()} années, {df['departement'].nunique()} départements")
    return df


def load_dep_2023() -> pd.DataFrame:
    """
    Fichier : er-ivg-carte-1.csv
    Contenu : taux de recours 2023 par département (101 depts).
    """
    df = _read_csv_safe(CSV_DEP_2023)

    df["code_dep"] = df["Code département"].apply(_standardize_dep_code)

    df = df.rename(columns={
        "Département de résidence": "departement",
        "Taux de recours 2023  pour 1 000 femmes de 15 à 49 ans": "taux_2023",
    })

    df["is_drom"] = df["code_dep"].isin(DROM_CODES)

    # Supprimer colonnes géo lourdes
    cols_drop = [c for c in df.columns if c in ("geom", "centroid", "Code département")]
    df = df.drop(columns=cols_drop, errors="ignore")

    df = df.sort_values("taux_2023", ascending=False).reset_index(drop=True)
    print(f"  ✓ dep_2023 : {len(df)} départements, taux min={df['taux_2023'].min()}, max={df['taux_2023'].max()}")
    return df


# ── QA checks ────────────────────────────────────────────────────

def _qa_checks(dfs: dict) -> None:
    """Vérifie la cohérence inter-fichiers."""
    nt = dfs["national_ts"]
    ntx = dfs["national_taux"]
    meth = dfs["methodes"]
    dy = dfs["dep_year"]
    d23 = dfs["dep_2023"]

    # Les deux fichiers nationaux doivent couvrir les mêmes années
    common_years = set(nt["annee"]) & set(ntx["annee"])
    if len(common_years) < 30:
        warnings.warn(f"Seulement {len(common_years)} années communes entre national_ts et national_taux")

    # Le fichier méthodes doit avoir 2016-2024
    if meth["annee"].min() > 2016 or meth["annee"].max() < 2024:
        warnings.warn(f"methodes couvre {meth['annee'].min()}-{meth['annee'].max()}, attendu 2016-2024")

    # Le fichier départemental doit avoir ~101 départements
    n_dep = dy["departement"].nunique()
    if n_dep < 95:
        warnings.warn(f"dep_year : seulement {n_dep} départements (attendu ~101)")

    # La carte 2023 doit avoir 101 départements
    if len(d23) < 95:
        warnings.warn(f"dep_2023 : seulement {len(d23)} départements")

    print("  ✓ QA checks passés")


# ── Fonction principale ──────────────────────────────────────────

def load_all(save_processed: bool = False) -> dict:
    """
    Charge et nettoie les 5 CSV. Retourne un dict de DataFrames.

    Parameters
    ----------
    save_processed : bool
        Si True, sauvegarde les DataFrames nettoyés en CSV dans data/processed/.

    Returns
    -------
    dict avec clés : national_ts, national_taux, methodes, dep_year, dep_2023
    """
    print("Chargement des données IVG...")

    dfs = {
        "national_ts": load_national_ts(),
        "national_taux": load_national_taux(),
        "methodes": load_methodes(),
        "dep_year": load_dep_year(),
        "dep_2023": load_dep_2023(),
    }

    _qa_checks(dfs)

    if save_processed:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        for name, df in dfs.items():
            out = PROCESSED / f"{name}.csv"
            df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"  → Sauvé : {out}")

    print("Chargement terminé.\n")
    return dfs


# ── Exécution directe (test) ─────────────────────────────────────
if __name__ == "__main__":
    dfs = load_all(save_processed=True)
    for name, df in dfs.items():
        print(f"\n{'='*60}")
        print(f"{name} — shape={df.shape}")
        print(df.head(3).to_string())