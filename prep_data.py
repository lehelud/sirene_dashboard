"""
prep_data.py - Preparation donnees SIRENE
URLs et colonnes verifiees sur data.gouv.fr (Mars 2026)

Colonnes disponibles dans StockUniteLegale :
  siren, dateCreationUniteLegale, etatAdministratifUniteLegale,
  activitePrincipaleUniteLegale, categorieJuridiqueUniteLegale (int64),
  trancheEffectifsUniteLegale
NOTE: dateCessationUniteLegale N'EXISTE PAS dans ce fichier
"""

import io
import sys
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")

# URLs directes des fichiers parquet (verifiees Mars 2026)
URL_UL_PARQUET = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"

# Colonnes exactes du fichier StockUniteLegale
COLS_UL = [
    "siren",
    "dateCreationUniteLegale",
    "etatAdministratifUniteLegale",
    "activitePrincipaleUniteLegale",
    "categorieJuridiqueUniteLegale",
    "trancheEffectifsUniteLegale",
]

GRANDS_SECTEURS = {
    "A":"Agriculture","B":"Industrie","C":"Industrie","D":"Industrie","E":"Industrie",
    "F":"Construction","G":"Commerce / Transport / HCR","H":"Commerce / Transport / HCR",
    "I":"Commerce / Transport / HCR","J":"Services aux entreprises",
    "K":"Services aux entreprises","L":"Services aux entreprises",
    "M":"Services aux entreprises","N":"Services aux entreprises",
    "O":"Services publics / Sante","P":"Services publics / Sante",
    "Q":"Services publics / Sante","R":"Autres","S":"Autres","T":"Autres","U":"Autres",
}

SECTEURS_CIBLES = [
    "Agriculture","Industrie","Construction",
    "Commerce / Transport / HCR","Services aux entreprises"
]

TRANCHES = {
    "NN":"Non employeur","00":"0 salarie","01":"1-2 salaries","02":"3-5 salaries",
    "03":"6-9 salaries","11":"10-19 salaries","12":"20-49 salaries",
    "21":"50-99 salaries","22":"100-199 salaries","31":"200-249 salaries",
    "32":"250-499 salaries","41":"500-999 salaries","42":"1 000-1 999 salaries",
    "51":"2 000-4 999 salaries","52":"5 000-9 999 salaries","53":"10 000 salaries et plus",
}


def telecharger_fichier(url: str, label: str) -> io.BytesIO:
    print(f"\n Telechargement de {label}...")
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=label) as bar:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            buf.write(chunk)
            bar.update(len(chunk))
    buf.seek(0)
    return buf


def charger_ul() -> pd.DataFrame:
    buf = telecharger_fichier(URL_UL_PARQUET, "Unites legales (parquet)")
    print(" Lecture parquet...")
    df = pd.read_parquet(buf, columns=COLS_UL)
    print(f" {len(df):,} lignes chargees")
    return df


def preparer_donnees(df: pd.DataFrame) -> pd.DataFrame:
    print(" Preparation des donnees...")
    # categorieJuridiqueUniteLegale est int64
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    # Exclure associations (7000-7999) et administration (9000-9999)
    df = df[~df["cat_jur"].between(7000, 9999)].copy()
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["mois"] = df["dateCreation"].dt.to_period("M").astype(str)
    df["grand_secteur"] = (
        df["activitePrincipaleUniteLegale"].astype(str).str[0].str.upper()
        .map(GRANDS_SECTEURS).fillna("Autres")
    )
    df["section_naf"] = df["activitePrincipaleUniteLegale"].astype(str).str[:2]
    df["libelle_taille"] = (
        df["trancheEffectifsUniteLegale"].astype(str)
        .map(TRANCHES).fillna("Non renseigne")
    )
    print(f" {len(df):,} entreprises secteur marchand")
    return df


def agreger_creations(df: pd.DataFrame) -> pd.DataFrame:
    import datetime
    now = datetime.datetime.now().year
    d = df[df["annee"].between(max(2000, now-15), now)]
    return (
        d.groupby(["annee","grand_secteur","cat_jur"], dropna=False)
        .size().reset_index(name="nb_creations")
        .rename(columns={"cat_jur":"categorie_juridique"})
    )


def agreger_naf(df: pd.DataFrame) -> pd.DataFrame:
    actives = df[df["etatAdministratifUniteLegale"]=="A"]
    return (
        actives.groupby(["section_naf","grand_secteur"])
        .size().reset_index(name="nb_entreprises")
    )


def agreger_taille(df: pd.DataFrame) -> pd.DataFrame:
    actives = df[df["etatAdministratifUniteLegale"]=="A"]
    return (
        actives.groupby(["libelle_taille","grand_secteur"])
        .size().reset_index(name="nb_entreprises")
    )


def agreger_cessations(df: pd.DataFrame) -> pd.DataFrame:
    # Pas de dateCessation dans StockUniteLegale
    # On approxime avec les entreprises cessees (etat = C) par annee de creation
    cessees = df[
        (df["etatAdministratifUniteLegale"]=="C")
        & df["grand_secteur"].isin(SECTEURS_CIBLES)
        & df["annee"].notna()
    ].copy()
    return (
        cessees.groupby(["mois","annee","grand_secteur"])
        .size().reset_index(name="nb_cessations")
        .rename(columns={"mois":"annee_mois"})
    )


def main():
    print("=" * 60)
    print("  SIRENE Dashboard - Preparation des donnees")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)

    # 1. Charger
    df_raw = charger_ul()

    # 2. Preparer
    df = preparer_donnees(df_raw)
    del df_raw  # liberer memoire

    # 3. Agreger et sauvegarder
    fichiers = [
        ("creations_annee.parquet", agreger_creations(df)),
        ("cessations_mois.parquet", agreger_cessations(df)),
        ("repartition_naf.parquet", agreger_naf(df)),
        ("repartition_taille.parquet", agreger_taille(df)),
    ]

    for nom, d in fichiers:
        chemin = DATA_DIR / nom
        d.to_parquet(chemin, index=False)
        taille = chemin.stat().st_size / 1024
        print(f" {nom} : {len(d):,} lignes ({taille:.0f} Ko)")

    print("\n Donnees pretes dans ./data/")
    print(" Lance maintenant : streamlit run app.py")


if __name__ == "__main__":
    main()
