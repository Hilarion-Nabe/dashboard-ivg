"""
data/cache.py — Singleton data cache.

Loads all data ONCE at import time. All modules import from here.
No recompute on callbacks.

Usage:
    from data.cache import DATA
    DATA["national_ts"]  # DataFrame
    DATA["geojson"]      # GeoJSON FeatureCollection dict
"""

from data.load import load_all, extract_geojson
from data.transforms import (
    flag_depts, build_dep_lookup, enrich_dep_year, build_national_age,
    build_national_mineures, build_national_praticiens,
    build_charge_moyenne, build_deserts, attach_dep_code,
)

# ── Load everything once ───────────────────────────────────────
_raw = load_all()

# ── Lookup table ───────────────────────────────────────────────
_dep_lookup = build_dep_lookup(_raw["dep_year"])

# ── GeoJSON ────────────────────────────────────────────────────
import json
from pathlib import Path
_geojson_path = Path(__file__).resolve().parent / "raw" / "departements.geojson"
with open(_geojson_path) as f:
    _geojson = json.load(f)

# ── Fix is_dept flags using positive match against known 101 depts ──
_raw["mineures"] = flag_depts(_raw["mineures"], _dep_lookup)
_raw["praticiens"] = flag_depts(_raw["praticiens"], _dep_lookup)
_raw["age_dept"] = flag_depts(_raw["age_dept"], _dep_lookup)

# ── Enrichments ────────────────────────────────────────────────
_dep_year = enrich_dep_year(_raw["dep_year"])
_nat_age = build_national_age(_raw["age_dept"])
_nat_mineures = build_national_mineures(_raw["mineures"])
_nat_prat = build_national_praticiens(_raw["praticiens"])
_charge = build_charge_moyenne(_nat_prat, _raw["methodes"])
_deserts = build_deserts(_raw["praticiens"], _dep_lookup)

# Attach dep_code to feuilles that only have zone_geo
_mineures = attach_dep_code(_raw["mineures"], _dep_lookup)
_praticiens = attach_dep_code(_raw["praticiens"], _dep_lookup)
_age_dept = attach_dep_code(_raw["age_dept"], _dep_lookup)

# ── Public interface ───────────────────────────────────────────
DATA = {
    # Raw (cleaned)
    "national_ts":     _raw["national_ts"],
    "national_taux":   _raw["national_taux"],
    "methodes":        _raw["methodes"],
    "dep_2023":        _raw["dep_2023"],

    # Enriched
    "dep_year":        _dep_year,
    "mineures":        _mineures,
    "praticiens":      _praticiens,
    "age_dept":        _age_dept,

    # Pre-aggregated
    "nat_age":         _nat_age,
    "nat_mineures":    _nat_mineures,
    "nat_prat":        _nat_prat,
    "charge":          _charge,
    "deserts":         _deserts,

    # Geo
    "geojson":         _geojson,
    "dep_lookup":      _dep_lookup,
}

print(f"  ✓ Cache initialisé — {len(DATA)} datasets prêts")
