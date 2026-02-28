"""
data/cache.py — Cache central des données (chargé une seule fois).

Quand on importe ce module, tout se charge automatiquement :
les 8 CSV sont lus, nettoyés, enrichis, et stockés dans le
dictionnaire DATA. Ensuite tous les callbacks Dash piochent
directement dedans sans jamais recharger les fichiers.

C'est le pattern "singleton" : un seul chargement au démarrage,
puis lecture seule pour tout le reste de l'appli.

Utilisation dans les autres modules :
    from data.cache import DATA
    DATA["national_ts"]  # → DataFrame
    DATA["geojson"]      # → dict GeoJSON (contours départementaux)
"""

from data.load import load_all, extract_geojson
from data.transforms import (
    flag_depts, build_dep_lookup, enrich_dep_year, build_national_age,
    build_national_mineures, build_national_praticiens,
    build_charge_moyenne, build_deserts, attach_dep_code,
)

# ── Étape 1 : lecture des 8 CSV ──────────────────────────────
_raw = load_all()

# ── Étape 2 : table de correspondance nom ↔ code département ─
_dep_lookup = build_dep_lookup(_raw["dep_year"])

# ── Étape 3 : extraction du GeoJSON pour la carte ────────────
_geojson = extract_geojson(_raw["dep_2023"])

# ── Étape 4 : correction du flag is_dept sur les feuilles 4/7/8
# On utilise la table de correspondance pour identifier les vrais
# départements (vs les régions et totaux nationaux)
_raw["mineures"] = flag_depts(_raw["mineures"], _dep_lookup)
_raw["praticiens"] = flag_depts(_raw["praticiens"], _dep_lookup)
_raw["age_dept"] = flag_depts(_raw["age_dept"], _dep_lookup)

# ── Étape 5 : calculs dérivés et agrégations ─────────────────
_dep_year = enrich_dep_year(_raw["dep_year"])
_nat_age = build_national_age(_raw["age_dept"])
_nat_mineures = build_national_mineures(_raw["mineures"])
_nat_prat = build_national_praticiens(_raw["praticiens"])
_charge = build_charge_moyenne(_nat_prat, _raw["methodes"])
_deserts = build_deserts(_raw["praticiens"], _dep_lookup)

# Ajout du code département aux feuilles qui n'ont que le nom
_mineures = attach_dep_code(_raw["mineures"], _dep_lookup)
_praticiens = attach_dep_code(_raw["praticiens"], _dep_lookup)
_age_dept = attach_dep_code(_raw["age_dept"], _dep_lookup)

# ── Interface publique : le dictionnaire DATA ─────────────────
# C'est CE dictionnaire que tous les onglets et composants importent
DATA = {
    # Données nettoyées (niveau national)
    "national_ts":     _raw["national_ts"],
    "national_taux":   _raw["national_taux"],
    "methodes":        _raw["methodes"],
    "dep_2023":        _raw["dep_2023"],

    # Données départementales enrichies
    "dep_year":        _dep_year,
    "mineures":        _mineures,
    "praticiens":      _praticiens,
    "age_dept":        _age_dept,

    # Agrégations nationales pré-calculées
    "nat_age":         _nat_age,
    "nat_mineures":    _nat_mineures,
    "nat_prat":        _nat_prat,
    "charge":          _charge,
    "deserts":         _deserts,

    # Données géographiques
    "geojson":         _geojson,
    "dep_lookup":      _dep_lookup,
}

print(f"  ✓ Cache initialisé — {len(DATA)} datasets prêts")
