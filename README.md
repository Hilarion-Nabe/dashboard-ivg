# Dashboard IVG France — Dash + CSS + Render

## Lancement local

```bash
cd ivg_dash/
pip install -r requirements.txt
python app.py
```
Puis ouvrir http://localhost:8050

## Déploiement sur Render

1. **Push** le repo sur GitHub (incluant `data/raw/` avec les 8 CSV)
2. **Créer** un nouveau **Web Service** sur [render.com](https://render.com)
3. **Connecter** au repo GitHub
4. **Configurer** :
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:server --bind 0.0.0.0:$PORT`
   - Python version: 3.11+

Le fichier `render.yaml` pré-configure tout automatiquement si Render le détecte.

## Architecture

```
ivg_dash/
├── app.py                    # Point d'entrée Dash (server = app.server)
├── pages/
│   ├── tab1_constat.py       # Onglet 1 — Le Constat (urgence nationale)
│   ├── tab2_fracture.py      # Onglet 2 — La Fracture (territoires)
│   ├── tab3_patientes.py     # Onglet 3 — Les Patientes (profil démo)
│   └── tab4_offre.py         # Onglet 4 — L'Offre de soins (praticiens)
├── components/
│   ├── header.py             # Bandeau titre HPV-like
│   ├── filterbar.py          # Barre filtres sticky (année/zone/dept)
│   ├── kpi_cards.py          # Composant KPI réutilisable
│   ├── footer.py             # Footer 3 lignes méthodo
│   └── dept_drawer.py        # Panneau drill-down département
├── data/
│   ├── load.py               # Chargement + nettoyage des 8 CSV
│   ├── transforms.py         # Features dérivées (rang, charge, déserts)
│   ├── cache.py              # Singleton — charge tout UNE SEULE FOIS
│   └── raw/                  # 8 fichiers CSV sources
├── assets/
│   └── styles.css            # CSS custom HPV-like
├── requirements.txt
├── render.yaml
└── DATA_MODEL.md             # Documentation du modèle de données
```

## Données intégrées

| Fichier | Contenu | Période |
|---------|---------|---------|
| er-ivg-graf1-sept-2024.csv | Totaux nationaux + ratio | 1990-2023 |
| er-ivg-graphique-2-ica0.csv | Taux ‰ + ICA | 1990-2023 |
| graf-dyn-er-ivg.csv | Modalités nationales | 2016-2024 |
| ivg_ods_test1.csv | Départemental multi-années | 2016-2022 |
| er-ivg-carte-1.csv | Carte taux 2023 + GeoJSON | 2023 |
| donnees_feuil4.csv | Part mineures (<18) | 2016-2024 |
| donnees_feuil7.csv | Praticiens par profession | 2016-2024 |
| donnees_feuil8.csv | Profil d'âge par département | 2016-2024 |
