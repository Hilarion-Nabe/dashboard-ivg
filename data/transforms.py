"""
data/transforms.py — Calculs dérivés et pré-agrégations.

Une fois les CSV chargés par load.py, on a des données "brutes" mais
il manque plein d'indicateurs utiles pour le dashboard : rang national,
écart à la médiane, totaux par profession, identification des déserts, etc.

Tout est calculé ici UNE SEULE FOIS au démarrage (via cache.py),
comme ça les callbacks Dash n'ont jamais à recalculer quoi que ce soit.
"""

import pandas as pd
import numpy as np


def flag_depts(df: pd.DataFrame, dep_lookup: pd.DataFrame,
               zone_col: str = "zone_geo") -> pd.DataFrame:
    """
    Marque les lignes qui correspondent à un vrai département (is_dept = True).

    Les feuilles 4, 7 et 8 mélangent départements, régions et totaux
    dans la même colonne zone_geo. Plutôt que d'essayer d'exclure toutes
    les régions possibles (fragile et risqué), on fait l'inverse :
    on ne garde comme "département" que les noms qu'on retrouve dans
    notre table de correspondance des 101 départements.
    """
    known = set(dep_lookup["dep_nom"].values)
    df = df.copy()
    df["is_dept"] = df[zone_col].isin(known)
    return df


def build_dep_lookup(dep_year: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la table de correspondance nom ↔ code département.
    101 lignes, une par département. Sert de référence pour toutes
    les jointures entre les différentes tables.
    """
    return (dep_year[["dep_nom", "dep_code", "region", "is_drom"]]
            .drop_duplicates(subset=["dep_nom"])
            .reset_index(drop=True))


def enrich_dep_year(dep_year: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit la table départementale avec des indicateurs dérivés :
      - pct_hors_hosp : part des IVG hors établissement
      - rang_national : classement du département (1 = taux le plus haut)
      - ecart_mediane : écart entre le taux du département et la médiane nationale

    On calcule tout ça année par année pour avoir un classement cohérent.
    """
    df = dep_year.copy()
    df["pct_hors_hosp"] = (df["total_hors_hosp"] / df["total_ivg"] * 100).round(1)

    # On boucle sur chaque année pour calculer le rang et l'écart médiane
    ranks = []
    for annee, grp in df.groupby("annee"):
        g = grp.copy()
        g["rang_national"] = g["taux_recours"].rank(ascending=False, method="min").astype(int)
        med = g["taux_recours"].median()
        g["ecart_mediane"] = (g["taux_recours"] - med).round(1)
        ranks.append(g)
    return pd.concat(ranks, ignore_index=True)


def build_national_age(age_dept: pd.DataFrame) -> pd.DataFrame:
    """
    Agrège le profil d'âge au niveau national (somme des départements).
    On ne prend que les lignes is_dept=True pour éviter de compter
    les régions en double.
    """
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
    """
    Extrait la ligne "France entière" de la feuille mineures
    pour avoir la série nationale de la part des <18 ans.
    """
    fr = mineures[mineures["zone_geo"] == "France entière"].copy()
    return fr.sort_values("annee").reset_index(drop=True)


def build_national_praticiens(praticiens: pd.DataFrame) -> pd.DataFrame:
    """
    Totalise les praticiens IVG au niveau national par année.
    On ne somme que les lignes département (is_dept=True)
    pour ne pas compter les régions en double.
    On calcule aussi la part de chaque profession (GO, MG, SF).
    """
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
    """
    Calcule la charge moyenne = total IVG / total praticiens, par année.
    Ça donne une idée du nombre d'IVG moyen par praticien libéral.
    (Attention : c'est une approximation, les hospitaliers ne sont pas dedans.)
    """
    merged = nat_prat.merge(
        methodes[["annee", "total"]].rename(columns={"total": "total_ivg"}),
        on="annee", how="inner"
    )
    merged["charge_moyenne"] = (merged["total_ivg"] / merged["total_prat"]).round(1)
    return merged


def build_deserts(praticiens: pd.DataFrame, dep_lookup: pd.DataFrame) -> pd.DataFrame:
    """
    Identifie les départements "déserts IVG" : ceux qui ont 5 praticiens
    libéraux ou moins pour une année donnée.
    Le seuil de 5 est un choix de notre part — en dessous, on considère
    que l'offre de soins est très insuffisante pour le territoire.
    """
    dept_only = praticiens[praticiens["is_dept"]].copy()
    # On ajoute le code département via jointure
    dept_only = dept_only.merge(dep_lookup[["dep_nom", "dep_code"]],
                                 left_on="zone_geo", right_on="dep_nom", how="left")
    deserts = dept_only[dept_only["total_prat"] <= 5][
        ["zone_geo", "dep_code", "annee", "total_prat"]
    ].sort_values(["annee", "total_prat"])
    return deserts


def attach_dep_code(df: pd.DataFrame, dep_lookup: pd.DataFrame,
                    zone_col: str = "zone_geo") -> pd.DataFrame:
    """
    Ajoute la colonne dep_code à un DataFrame qui n'a que le nom (zone_geo).
    Jointure simple sur le nom de département via la table de correspondance.
    """
    return df.merge(
        dep_lookup[["dep_nom", "dep_code"]],
        left_on=zone_col, right_on="dep_nom", how="left"
    ).drop(columns=["dep_nom"], errors="ignore")
