"""
data/transforms.py — Features dérivées et pré-agrégations.

Toutes les transformations coûteuses sont faites une seule fois au démarrage,
puis stockées dans le cache (voir cache.py).
"""

import pandas as pd
import numpy as np


def flag_depts(df: pd.DataFrame, dep_lookup: pd.DataFrame,
               zone_col: str = "zone_geo") -> pd.DataFrame:
    """
    Sets is_dept = True only for rows whose zone_geo matches a known
    department name from the 101-entry lookup table.
    This is a POSITIVE filter — much safer than trying to exclude
    all possible region/total names.
    """
    known = set(dep_lookup["dep_nom"].values)
    df = df.copy()
    df["is_dept"] = df[zone_col].isin(known)
    return df


def build_dep_lookup(dep_year: pd.DataFrame) -> pd.DataFrame:
    """Table de correspondance dep_nom → dep_code (101 lignes)."""
    return (dep_year[["dep_nom", "dep_code", "region", "is_drom"]]
            .drop_duplicates(subset=["dep_nom"])
            .reset_index(drop=True))


def enrich_dep_year(dep_year: pd.DataFrame) -> pd.DataFrame:
    """Ajoute rang, écart médiane, % hors hospitalier au dep_year."""
    df = dep_year.copy()
    df["pct_hors_hosp"] = (df["total_hors_hosp"] / df["total_ivg"] * 100).round(1)

    # Rang national et écart médiane par année
    ranks = []
    for annee, grp in df.groupby("annee"):
        g = grp.copy()
        g["rang_national"] = g["taux_recours"].rank(ascending=False, method="min").astype(int)
        med = g["taux_recours"].median()
        g["ecart_mediane"] = (g["taux_recours"] - med).round(1)
        ranks.append(g)
    return pd.concat(ranks, ignore_index=True)


def build_national_age(age_dept: pd.DataFrame) -> pd.DataFrame:
    """Agrège le profil d'âge national par année (somme des départements)."""
    dept_only = age_dept[age_dept["is_dept"]].copy()
    age_vol_cols = ["age_inf18", "age_18_19", "age_20_24",
                    "age_25_29", "age_30_34", "age_35_39", "age_40plus"]

    nat = dept_only.groupby("annee")[age_vol_cols].sum().reset_index()
    nat["total"] = nat[age_vol_cols].sum(axis=1)

    for col in age_vol_cols:
        pct_col = "pct_" + col.replace("age_", "")
        nat[pct_col] = (nat[col] / nat["total"] * 100).round(1)

    return nat.sort_values("annee").reset_index(drop=True)


def build_national_mineures(mineures: pd.DataFrame) -> pd.DataFrame:
    """Extrait la série nationale de la part des mineures."""
    fr = mineures[mineures["zone_geo"] == "France entière"].copy()
    return fr.sort_values("annee").reset_index(drop=True)


def build_national_praticiens(praticiens: pd.DataFrame) -> pd.DataFrame:
    """Agrège les praticiens au niveau national par année."""
    dept_only = praticiens[praticiens["is_dept"]].copy()
    agg = dept_only.groupby("annee").agg(
        total_go=("total_go", "sum"),
        total_mg=("total_mg", "sum"),
        total_sf=("total_sf", "sum"),
        total_aut=("total_aut", "sum"),
        total_prat=("total_prat", "sum"),
    ).reset_index()

    agg["pct_go"] = (agg["total_go"] / agg["total_prat"] * 100).round(1)
    agg["pct_mg"] = (agg["total_mg"] / agg["total_prat"] * 100).round(1)
    agg["pct_sf"] = (agg["total_sf"] / agg["total_prat"] * 100).round(1)

    return agg.sort_values("annee").reset_index(drop=True)


def build_charge_moyenne(nat_prat: pd.DataFrame, methodes: pd.DataFrame) -> pd.DataFrame:
    """Calcule la charge moyenne = total IVG / total praticiens par année."""
    merged = nat_prat.merge(
        methodes[["annee", "total"]].rename(columns={"total": "total_ivg"}),
        on="annee", how="inner"
    )
    merged["charge_moyenne"] = (merged["total_ivg"] / merged["total_prat"]).round(1)
    return merged


def build_deserts(praticiens: pd.DataFrame, dep_lookup: pd.DataFrame) -> pd.DataFrame:
    """Identifie les départements 'déserts' (≤ 5 praticiens libéraux), par année."""
    dept_only = praticiens[praticiens["is_dept"]].copy()
    # Jointure pour ajouter dep_code
    dept_only = dept_only.merge(dep_lookup[["dep_nom", "dep_code"]],
                                 left_on="zone_geo", right_on="dep_nom", how="left")
    deserts = dept_only[dept_only["total_prat"] <= 5][
        ["zone_geo", "dep_code", "annee", "total_prat"]
    ].sort_values(["annee", "total_prat"])
    return deserts


def attach_dep_code(df: pd.DataFrame, dep_lookup: pd.DataFrame,
                    zone_col: str = "zone_geo") -> pd.DataFrame:
    """Attache dep_code à un DataFrame ayant une colonne zone_geo (nom de département)."""
    return df.merge(
        dep_lookup[["dep_nom", "dep_code"]],
        left_on=zone_col, right_on="dep_nom", how="left"
    ).drop(columns=["dep_nom"], errors="ignore")
