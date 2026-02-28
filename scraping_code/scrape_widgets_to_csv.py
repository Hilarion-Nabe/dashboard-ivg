# data/scrape_widgets_to_csv.py
from __future__ import annotations

import re
import csv
import json
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import requests

BASE = "https://data.drees.solidarites-sante.gouv.fr"

WIDGET_URLS: List[Tuple[str, str]] = [
    ("https://data.drees.solidarites-sante.gouv.fr/explore/embed/dataset/er-ivg-carte-1/table/", "er-ivg-carte-1.csv"),
    ("https://data.drees.solidarites-sante.gouv.fr/explore/embed/dataset/er-ivg-graf1-sept-2024/table/", "er-ivg-graf1-sept-2024.csv"),
    ("https://data.drees.solidarites-sante.gouv.fr/explore/embed/dataset/er-ivg-graphique-2-ica0/table/", "er-ivg-graphique-2-ica0.csv"),
    ("https://data.drees.solidarites-sante.gouv.fr/explore/embed/dataset/graf-dyn-er-ivg/table/", "graf-dyn-er-ivg.csv"),
    ("https://data.drees.solidarites-sante.gouv.fr/explore/embed/dataset/ivg_ods_test1/table/?disjunctive.annee", "ivg_ods_test1.csv"),
]

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ivg-dashboard-scraper/1.0)"
})


def dataset_id_from_widget_url(url: str) -> str:
    m = re.search(r"/dataset/([^/]+)/", url)
    if not m:
        raise ValueError(f"Impossible d'extraire dataset_id depuis: {url}")
    return m.group(1)


def fetch_dataset_metadata(dataset_id: str) -> Dict:
    url = f"{BASE}/api/explore/v2.1/catalog/datasets/{dataset_id}"
    r = SESSION.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def get_field_order_and_labels(meta: Dict) -> Tuple[List[str], Dict[str, str]]:
    fields = meta.get("fields", [])
    order = [f["name"] for f in fields if "name" in f]
    labels = {f["name"]: f.get("label", f["name"]) for f in fields if "name" in f}
    return order, labels


def fetch_all_records(dataset_id: str, batch_size: int = 100) -> pd.DataFrame:
    all_rows: List[Dict] = []
    offset = 0

    while True:
        url = f"{BASE}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
        params = {"limit": batch_size, "offset": offset}
        r = SESSION.get(url, params=params, timeout=60)
        r.raise_for_status()
        payload = r.json()

        results = payload.get("results", [])
        if not results:
            break

        all_rows.extend(results)
        offset += len(results)

        total = payload.get("total_count")
        if total is not None and offset >= int(total):
            break

    return pd.DataFrame(all_rows)


def _coerce_to_dict(v: Any) -> Dict | None:
    """Essaye de convertir v (dict / json str / python dict str) en dict."""
    if isinstance(v, dict):
        return v
    if not isinstance(v, str) or not v.strip():
        return None

    s = v.strip()
    # JSON
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # repr python
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    return None


def _format_geo_shape_like_ods(v: Any) -> str:
    """
    Export ODS observé: {"coordinates": ...} (double quotes).
    L'API peut fournir:
      - dict {'type': 'Feature', 'geometry': {'coordinates': ...}}
      - dict {'coordinates': ...}
    """
    d = _coerce_to_dict(v)
    if not d:
        return "" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v)

    coords = None
    if "coordinates" in d:
        coords = d["coordinates"]
    elif "geometry" in d and isinstance(d["geometry"], dict) and "coordinates" in d["geometry"]:
        coords = d["geometry"]["coordinates"]

    if coords is None:
        # fallback : dump entier
        return json.dumps(d, ensure_ascii=False)

    return json.dumps({"coordinates": coords}, ensure_ascii=False)


def _format_geo_point_like_ods(v: Any) -> str:
    """
    Export ODS observé: "lat, lon" (ex: "46.09..., 5.34...")
    L'API peut fournir: {'lon': ..., 'lat': ...}
    """
    d = _coerce_to_dict(v)
    if d and "lat" in d and "lon" in d:
        return f"{d['lat']}, {d['lon']}"

    # parfois c'est déjà une string "lat, lon"
    if isinstance(v, str):
        return v

    return "" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v)


def export_like_site(df: pd.DataFrame, dataset_id: str, out_csv: Path) -> None:
    meta = fetch_dataset_metadata(dataset_id)
    field_order, labels = get_field_order_and_labels(meta)

    keep = [c for c in field_order if c in df.columns]
    df2 = df.copy()
    df2 = df2[keep].where(pd.notnull(df2[keep]), "")

    # Reformater les colonnes geo avant de renommer en labels
    if "geo_shape" in df2.columns:
        df2["geo_shape"] = df2["geo_shape"].apply(_format_geo_shape_like_ods)
    if "geo_point_2d" in df2.columns:
        df2["geo_point_2d"] = df2["geo_point_2d"].apply(_format_geo_point_like_ods)

    # Renommer colonnes en labels
    df2 = df2.rename(columns={c: labels.get(c, c) for c in df2.columns})

    # Ordre de tri 
    sort_cols = [c for c in ["Zone géographique", "Années"] if c in df2.columns]
    if sort_cols:
        df2 = df2.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)

    # UTF-8 avec BOM + ';' + quoting minimal
    df2.to_csv(
        out_csv,
        index=False,
        sep=";",
        encoding="utf-8-sig",     
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print(f" {dataset_id} -> {out_csv.name} ({len(df2)} lignes, {len(df2.columns)} colonnes)")


def scrape_one(widget_url: str, filename: str) -> None:
    dataset_id = dataset_id_from_widget_url(widget_url)
    df = fetch_all_records(dataset_id, batch_size=100)
    export_like_site(df, dataset_id, OUT_DIR / filename)


def main() -> None:
    for url, filename in WIDGET_URLS:
        scrape_one(url, filename)


if __name__ == "__main__":
    main()