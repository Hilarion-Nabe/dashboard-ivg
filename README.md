# IVG en France — Droit légal, accessibilité réelle

Un tableau de bord interactif développé avec **Dash** pour explorer les données sur l'interruption volontaire de grossesse en France. Le dashboard croise évolution nationale, inégalités territoriales, profil des patientes et transformations de l'offre de soins, à partir de données ouvertes DREES/SNDS et Data.gouv.fr.

## 🌐 Accès en ligne

Le dashboard est accessible via ce lien : [IVG Dashboard Live](https://dashboard-ivg.onrender.com)

## 👥 Auteurs

AZZOUZI Hiba, BENBETKA Rania, BENGUENNA Célia, LAVOGEZ Ethan, NABE-NANA Hilarion 

*Université de Lille-UFR 3S (ILIS)*

## 📸 Aperçu

> *Insérez ici une ou deux captures d'écran du dashboard.*

Le tableau de bord fournit :
- **Carte choroplèthe** des taux de recours à l'IVG par département
- **Cleveland dot plot** des écarts à la médiane nationale (Top/Bottom 15)
- **Pyramide d'âge** et dot plot des mineures par département
- **Lollipop chart** des déserts IVG (départements ≤ 5 praticiens)
- **Filtres dynamiques** pour explorer les données par année, zone et département
- **Drill-down** par département (KPI locaux, tendance, profil d'âge)

## 🔗 Sources des données

Les données proviennent de deux sources complémentaires :
- **DREES / SNDS** — 5 fichiers collectés via scraping API ([script](scripts/scrape_widgets_to_csv.py))
- **Data.gouv.fr** — 3 fichiers téléchargés manuellement (`donnees_feuil4`, `feuil7`, `feuil8`)

| Fichier | Source | Période |
|---------|--------|---------|
| `er-ivg-graf1-sept-2024.csv` | DREES / SNDS | 1990–2023 |
| `er-ivg-graphique-2-ica0.csv` | DREES / SNDS | 1990–2023 |
| `graf-dyn-er-ivg.csv` | DREES / SNDS | 2016–2024 |
| `ivg_ods_test1.csv` | DREES / SNDS | 2016–2022 |
| `er-ivg-carte-1.csv` | DREES / SNDS | 2023 |
| `donnees_feuil4.csv` | Data.gouv.fr | 2016–2024 |
| `donnees_feuil7.csv` | Data.gouv.fr | 2016–2024 |
| `donnees_feuil8.csv` | Data.gouv.fr | 2016–2024 |

Documentation détaillée du modèle de données : [`DATA_MODEL.md`](DATA_MODEL.md)

## 🏗 Stack technique

- **Dash** 2.x + **Plotly** 5.x pour les visualisations
- **Dash Bootstrap Components** pour la mise en page
- **pandas** + **numpy** pour le traitement des données
- **requests** + API Opendatasoft pour la collecte (scraping DREES)
- **gunicorn** sur **Render** (free tier)

## 📁 Structure du projet

```
ivg_dash/
├── app.py                        # Point d'entrée Dash
├── requirements.txt              # Dépendances Python
├── render.yaml                   # Config Render
│
├── assets/
│   └── styles.css                # Charte graphique
│
├── components/
│   ├── header.py                 # Bandeau titre
│   ├── footer.py                 # Pied de page méthodologique
│   ├── filterbar.py              # Barre de filtres (année/zone/dept)
│   ├── kpi_cards.py              # Cartes KPI
│   └── dept_drawer.py            # Panneau drill-down département
│
├── data/
│   ├── load.py                   # Lecture et nettoyage des CSV
│   ├── transforms.py             # Calculs dérivés
│   ├── cache.py                  # Chargement unique au démarrage
│   └── raw/                      # 8 fichiers CSV sources
│
├── pages/
│   ├── tab1_constat.py           # Onglet 1 — Le Constat
│   ├── tab2_fracture.py          # Onglet 2 — La Fracture
│   ├── tab3_patientes.py         # Onglet 3 — Les Patientes
│   └── tab4_offre.py             # Onglet 4 — L'Offre de soins
│
├── scripts/
│   └── scrape_widgets_to_csv.py  # Collecte automatisée des CSV DREES
│
└── DATA_MODEL.md                 # Documentation des données
```

## 🛠 Installation & lancement en local

```bash
git clone https://github.com/Hilarion-Nabe/dashboard-ivg.git
cd name_your_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
python app.py
```

Ouvrir http://localhost:8050

## ⚠ Note méthodologique

La DREES signale une rupture de série en 2020 (passage au SNDS). Les comparaisons avant/après 2020 sont à interpréter avec prudence. Le taux de recours mesure la fréquence du recours, pas l'accessibilité réelle de l'offre.
