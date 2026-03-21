# Dashboard SIRENE - Entreprises du secteur marchand

Dashboard interactif d'analyse des entreprises françaises du secteur marchand, construit avec **Streamlit** et alimenté par la **Base SIRENE** (data.gouv.fr).

---

## Fonctionnalités

### Visualisations

| Onglet | Contenu |
|---|---|
| **Créations** | Évolution des créations d'entreprises par année et grand secteur |
| **Cessations** | Cessations mensuelles sur 5 ans par grand secteur |
| **Secteurs NAF** | Répartition des entreprises actives par grand secteur |
| **Taille** | Distribution par tranche d'effectifs |
| **Carte** | Carte interactive des établissements actifs par commune |
| **NAF 2008 -> 2025** | Comparaison des deux nomenclatures avec diagramme Sankey |

### Filtres disponibles
- Période de création (curseur année)
- Grands secteurs d'activité
- Catégorie juridique
- Département (pour la carte)

### KPIs en temps réel
- Total créations sur la période
- Créations de l'année en cours vs année précédente (delta %)
- Total cessations
- Nombre de secteurs suivis

### Onglet NAF 2008 -> 2025
Analyse de l'impact de la nouvelle nomenclature NAF 2025 (entrée en vigueur au 1er janvier 2027) :
- **Diagramme Sankey** : flux de correspondance entre groupes 2008 et 2025
- **Types de changements** : 1->1 identique, recodé, N->1 fusion, 1->N division, réarrangement
- **Comparaison sectorielle** : nombre de groupes par section avant/après
- **Table searchable** avec export CSV filtré

---

## Architecture

```
sirene_dashboard/
├── app.py                      <- Application Streamlit principale
├── auth.py                     <- Module d'authentification
├── naf_comparaison.py          <- Module comparaison NAF 2008/2025
├── prep_data.py                <- Script de préparation des données (offline)
├── setup_auth.py               <- Script de création des comptes utilisateurs
├── requirements.txt
├── auth_config.example.yaml    <- Modèle config auth
├── .gitignore
└── .vscode/launch.json         <- Configuration VS Code (F5 pour lancer)
```

### Principe de fonctionnement

```
Base SIRENE (data.gouv.fr) ~5 Go
    |
    v  prep_data.py (1x/mois, ~20 min)
    |
    v  data/ fichiers parquet agréges ~50 Mo
    |
    v  app.py -> Dashboard Streamlit
```

---

## Installation et lancement

### 1. Cloner le repo

```bash
git clone https://github.com/lehelud/sirene_dashboard.git
cd sirene_dashboard
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Créer les comptes utilisateurs

```bash
python setup_auth.py
```

Ce script interactif génère `auth_config.yaml` avec les mots de passe hashés (bcrypt).
**Ne jamais committer auth_config.yaml dans Git** — il est dans le .gitignore.

### 4. Préparer les données SIRENE

```bash
python prep_data.py
```

- Télécharge automatiquement les fichiers parquet depuis data.gouv.fr
- Filtre le secteur marchand (exclut associations et administrations)
- Génère les fichiers agrégés dans ./data/
- Durée estimée : ~20 minutes

### 5. Lancer l'application

```bash
streamlit run app.py
```

---

## Authentification

L'accès est sécurisé par `streamlit-authenticator`. Seuls les utilisateurs enregistrés peuvent accéder au dashboard.

### Ajouter un utilisateur

```bash
python setup_auth.py
# Choisir (a) pour ajouter un utilisateur
```

## Déploiement sur Streamlit Cloud

1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. **New app** -> choisir ce repo, branche `main`, fichier `app.py`
3. Dans **Advanced settings -> Secrets**, ajouter le contenu de `auth_config.yaml`
4. Passer l'app en **Private** dans les paramètres de partage

---

## Sources de données

| Source | Description | Fréquence |
|---|---|---|
| [Base SIRENE — data.gouv.fr](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/) | Unités légales et établissements | Mensuelle |
| [API Géo — geo.api.gouv.fr](https://geo.api.gouv.fr/) | Référentiel communes | Stable |
| [INSEE — NAF 2025](https://www.insee.fr/fr/information/8617910) | Table correspondance NAF rev.2 -> NAF 2025 | Janvier 2026 |

---

## Stack technique

| Outil | Usage |
|---|---|
| [Streamlit](https://streamlit.io/) | Framework dashboard |
| [Plotly](https://plotly.com/) | Graphiques interactifs |
| [Pandas](https://pandas.pydata.org/) | Manipulation des données |
| [PyArrow](https://arrow.apache.org/docs/python/) | Lecture fichiers Parquet |
| [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator) | Authentification |

---

## Mise à jour des données

Les données SIRENE sont mises à jour mensuellement. Pour rafraîchir :

```bash
rm data/*.parquet
python prep_data.py
```

---

## RGPD et données personnelles

La base SIRENE contient des données à caractère personnel. Ce dashboard est destiné à un usage statistique agrégé uniquement. Respecter le statut de diffusion de chaque unité (`statutDiffusionUniteLegale`).

---

## Auteur

**lehelud** — [github.com/lehelud](https://github.com/lehelud)

*Dashboard développé dans le cadre d'un apprentissage Streamlit + GitHub, avec données publiques françaises.*
