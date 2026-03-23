# Dashboard SIRENE — Entreprises du secteur marchand

Tableau de bord interactif d'analyse des entreprises françaises, construit avec **Streamlit** et alimenté par la **Base SIRENE** (data.gouv.fr).
Les données exposées n'ont pas toutes été comparées à des sources officielles, le dashboard peut donc comporter des erreurs.
Lien vers le streamlit cloud pour naviguer sans avoir besoin d'installer l'application : https://sirene-dashboard-sirene.streamlit.app/

## Onglets

| Onglet | Contenu |
|---|---|
| Vue d'ensemble | KPIs, treemap actives, structure employeurs/non-employeurs |
| Tendances | Courbes mensuelles, saisonnalite, heatmap par annee et secteur |
| Structure | Pareto, formes juridiques, taille, top divisions NAF |
| Survie | Taux de survie par cohorte, courbe, heatmap cohorte x duree |
| Carte | Carte interactive par departement, bulles proportionnelles |
| NAF 2008->2025 | Comparaison nomenclatures, entreprises impactees, table filtrable |

## Installation

```bash
git clone https://github.com/lehelud/sirene_dashboard.git
cd sirene_dashboard
pip install -r requirements.txt
python prep_data.py  # ~20 min, telecharge ~3 Go
python -m streamlit run app.py
```

## Mise à jour des données (non automatique car fichiers trop lourds pour Streamlit cloud)

```bash
python prep_data.py
git add -f data/*.parquet
git commit -m "data: maj mensuelle"
git push
```


## Fichiers generes par prep_data.py

| Fichier | Contenu |
|---|---|
| creations_mensuel.parquet | Creations par mois, annee, secteur |
| stock_actives.parquet | Actives par secteur, forme, taille |
| formes_juridiques.parquet | Repartition formes juridiques |
| employeurs.parquet | Ratio employeurs par secteur |
| naf_detail.parquet | Top divisions NAF (2 chiffres) |
| survie.parquet | Taux de survie par cohorte |
| departements.parquet | Etablissements par departement et secteur |

## Stack

- Streamlit, Plotly, Pandas, PyArrow, Requests

## Source

Base SIRENE — [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/) — Mise a jour mensuelle

**lehelud** — [github.com/lehelud](https://github.com/lehelud)
