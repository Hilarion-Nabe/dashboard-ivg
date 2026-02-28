# Modèle de données canon — Dashboard IVG Dash

## Clés standardisées (utilisées dans tous les DataFrames)

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `annee` | int | Année de référence | 2023 |
| `dep_code` | str | Code département (2 chars + 2A/2B + 97x) | "01", "2A", "971" |
| `dep_nom` | str | Nom du département | "Ain" |
| `region` | str | Nom de la région | "Auvergne-Rhône-Alpes" |
| `is_drom` | bool | True si DROM (971-976) | True |

---

## DF1 — `national_ts` (série longue volumes)
Source : CSV2 (`er-ivg-graf1-sept-2024.csv`)
Grain : national × année (1990–2023, 34 lignes)

| Colonne | Type | Origine |
|---------|------|---------|
| annee | int | "Années" cast |
| total_brut | int | direct |
| total_sans_reprises | float (NaN avant 2016) | direct |
| ratio_brut | float | direct |
| ratio_sans_reprises | float (NaN avant 2016) | direct |

---

## DF2 — `national_taux` (série longue taux + ICA)
Source : CSV3 (`er-ivg-graphique-2-ica0.csv`)
Grain : national × année (1990–2023, 34 lignes)

| Colonne | Type | Origine |
|---------|------|---------|
| annee | int | cast |
| taux_1000 | float | direct |
| taux_1000_sr | float (NaN avant 2016) | direct |
| ica | float | direct |
| ica_sr | float (NaN avant 2016) | direct |

---

## DF3 — `methodes` (modalités nationales)
Source : CSV5 (`graf-dyn-er-ivg.csv`)
Grain : national × année (2016–2024, 9 lignes)

| Colonne | Type | Origine |
|---------|------|---------|
| annee | int | cast |
| hors_etab | int | volume |
| instrumentales | int | volume |
| medic_etab | int | volume |
| total | int | **dérivé** sum(3 cols) |
| pct_hors_etab | float | **dérivé** |
| pct_instrumentales | float | **dérivé** |
| pct_medic_etab | float | **dérivé** |
| pct_medicamenteux | float | **dérivé** (hors_etab + medic_etab) / total |

---

## DF4 — `dep_year` (départemental multi-années)
Source : CSV1 (`ivg_ods_test1.csv`)
Grain : département × année (101 depts × 7 ans = ~707 lignes, 2016–2022)

| Colonne | Type | Origine |
|---------|------|---------|
| dep_code | str | standardisé |
| dep_nom | str | "Zone géographique" |
| region | str | "Nom Officiel Région" |
| annee | int | regex extract |
| is_drom | bool | dérivé |
| total_ivg | int | "TOTAL IVG-" |
| taux_recours | float | direct |
| total_hosp | int | direct |
| total_hors_hosp | int | direct |
| instru_hosp | int | direct |
| medic_hosp | int | direct |
| **pct_hors_hosp** | float | **dérivé** total_hors_hosp / total_ivg × 100 |
| **rang_national** | int | **dérivé** rank(taux_recours) par année |
| **ecart_mediane** | float | **dérivé** taux_recours - median(taux_recours) par année |

---

## DF5 — `dep_2023` (snapshot départemental 2023 + géométrie)
Source : CSV4 (`er-ivg-carte-1.csv`)
Grain : département (101 lignes)

| Colonne | Type | Origine |
|---------|------|---------|
| dep_code | str | standardisé |
| dep_nom | str | "Département de résidence" |
| taux_2023 | float | direct |
| is_drom | bool | dérivé |
| geojson | dict | **parsé** de la colonne `geom` |

Note : on extrait le GeoJSON pour construire un FeatureCollection Plotly.

---

## DF6 — `mineures` (part <18 ans)
Source : F4 (`donnees_feuil4.csv`)
Grain : département × année (101 depts × 9 ans ≈ 909 lignes dept, + régions/totaux)

| Colonne | Type | Origine |
|---------|------|---------|
| zone_geo | str | direct (dept OU région OU total) |
| dep_code | str | **jointure** via table correspondance dep_nom → dep_code |
| annee | int | direct |
| part_mineures | float | `part_age_inf18` après virgule→point |
| part_age_inconnu | float | `part_age_inc` après virgule→point |
| is_dept | bool | **dérivé** (filtre zones qui sont des départements) |

---

## DF7 — `praticiens` (offre de soins)
Source : F7 (`donnees_feuil7.csv`)
Grain : département × année (101+ depts × 9 ans, + régions/totaux)

| Colonne | Type | Origine |
|---------|------|---------|
| zone_geo | str | direct |
| dep_code | str | **jointure** |
| annee | int | `ANNEE` cast |
| cab_go | float | `CAB_GO` (NaN = absence) |
| cab_mg | float | `CAB_MG` |
| cab_sf | float | `CAB_SF` |
| cab_aut | float | `CAB_AUT` |
| tele_go | float | `TELE_GO` |
| tele_mg | float | `TELE_MG` |
| tele_sf | float | `TELE_SF` |
| tele_aut | float | `TELE_AUT` |
| **total_go** | float | **dérivé** cab_go + tele_go (fillna 0) |
| **total_mg** | float | **dérivé** |
| **total_sf** | float | **dérivé** |
| **total_prat** | float | **dérivé** sum all |
| **is_dept** | bool | **dérivé** |

Features agrégées nationales (par année) :
- **charge_moyenne** = total_ivg_national / sum(total_prat) par année
- **pct_go**, **pct_mg**, **pct_sf** = parts par profession
- **deserts** = départements avec total_prat <= 5

---

## DF8 — `age_dept` (profil d'âge par département)
Source : F8 (`donnees_feuil8.csv`)
Grain : département × année (101+ depts × 9 ans)

| Colonne | Type | Origine |
|---------|------|---------|
| zone_geo | str | direct |
| dep_code | str | **jointure** |
| annee | int | direct |
| age_inf18 | int | volume |
| age_18_19 | int | volume |
| age_20_24 | int | volume |
| age_25_29 | int | volume |
| age_30_34 | int | volume |
| age_35_39 | int | volume |
| age_40plus | int | volume |
| **total_dept** | int | **dérivé** sum |
| **pct_inf18** | float | **dérivé** age_inf18 / total_dept × 100 |
| **pct_18_19** | float | **dérivé** |
| **pct_20_24** | float | **dérivé** |
| **pct_25_29** | float | **dérivé** |
| **pct_30_34** | float | **dérivé** |
| **pct_35_39** | float | **dérivé** |
| **pct_40plus** | float | **dérivé** |
| **is_dept** | bool | **dérivé** |

---

## Table de correspondance `dep_nom → dep_code`

Construite à partir de CSV1 (`dep_year`) qui contient les deux champs.
Sert de table de jointure pour F4, F7, F8 qui n'ont que `zone_geo` (nom).

```python
dep_lookup = dep_year[["dep_nom", "dep_code"]].drop_duplicates()
# 101 lignes, clé unique
```
