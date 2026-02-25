import sys, json
sys.path.insert(0, '.')
from data.load import load_dep_2023, extract_geojson

dep = load_dep_2023()
geo = extract_geojson(dep)
print(len(geo["features"]), "features")

with open("data/raw/departements.geojson", "w") as f:
    json.dump(geo, f)

print("Fichier data/raw/departements.geojson cree!")  