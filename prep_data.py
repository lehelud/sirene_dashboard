"""
prep_data.py - Preparation donnees SIRENE - Version 2
Genere 7 fichiers parquet agregés pour le dashboard ambitieux.

Fichiers produits dans ./data/ :
  creations_mensuel.parquet   - creations par mois/secteur
  stock_actives.parquet       - actives par secteur/forme/taille
  survie.parquet              - taux de survie par cohorte
  formes_juridiques.parquet   - formes juridiques
  employeurs.parquet          - ratio employeurs
  departements.parquet        - agregation par departement
  naf_detail.parquet          - repartition par code NAF 2 chiffres
"""
import io
import datetime
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")
URL_UL   = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"
URL_ETAB = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

COLS_UL = [
    "siren","dateCreationUniteLegale","etatAdministratifUniteLegale",
    "activitePrincipaleUniteLegale","categorieJuridiqueUniteLegale",
    "trancheEffectifsUniteLegale","caractereEmployeurUniteLegale",
    "economieSocialeSolidaireUniteLegale",
]
COLS_ETAB = [
    "siren","codeCommuneEtablissement","etatAdministratifEtablissement",
    "activitePrincipaleEtablissement",
]

TRANCHES = {
    "NN":"Non employeur","00":"0 sal.","01":"1-2","02":"3-5","03":"6-9",
    "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
    "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999",
    "52":"5000-9999","53":"10000+",
}

CAT_JUR_LIB = {
    1:"Entrepreneur individuel",
    2:"Indivision / Fiducie",
    3:"Personne morale etrangere",
    4:"Organisme public",
    5:"SA / SAS / SARL",
    6:"Autre personne morale",
}

def div_to_secteur(div_str):
    try:
        d = int(div_str)
    except (ValueError, TypeError):
        return "Autres"
    if 1 <= d <= 3:   return "Agriculture"
    if 5 <= d <= 39:  return "Industrie"
    if 41 <= d <= 43: return "Construction"
    if 45 <= d <= 56: return "Commerce / Transport / HCR"
    if 58 <= d <= 66: return "Services aux entreprises"
    if 68 <= d <= 75: return "Services aux entreprises"
    if 77 <= d <= 82: return "Services aux entreprises"
    if 84 <= d <= 88: return "Services publics / Sante"
    return "Autres"

def code_to_forme(cat):
    try:
        c = int(str(cat)[:1])
        return CAT_JUR_LIB.get(c, "Autre")
    except:
        return "Autre"

def telecharger(url, label):
    print(f"\n  Telechargement {label}...")
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=f"  {label}") as bar:
        for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
            buf.write(chunk)
            bar.update(len(chunk))
    buf.seek(0)
    return buf

def sauver(df, nom):
    p = DATA_DIR / nom
    df.to_parquet(p, index=False)
    print(f"  {nom}: {len(df):,} lignes  ({p.stat().st_size // 1024} Ko)")

def enrichir_ul(df):
    df = df.copy()
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df = df[~df["cat_jur"].between(7000, 9999)]
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"]  = df["dateCreation"].dt.year.astype("Int64")
    df["mois"]   = df["dateCreation"].dt.to_period("M").astype(str)
    naf = df["activitePrincipaleUniteLegale"].astype(str).str.strip()
    div = naf.str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df["div_naf"]       = div.fillna("00")
    df["grand_secteur"] = div.map(div_to_secteur).fillna("Autres")
    df["forme_jur"]     = df["cat_jur"].map(code_to_forme)
    df["libelle_taille"]= df["trancheEffectifsUniteLegale"].astype(str).map(TRANCHES).fillna("Non renseigne")
    df["est_employeur"] = df["caractereEmployeurUniteLegale"].astype(str).isin(["O"])
    df["est_ess"]       = df["economieSocialeSolidaireUniteLegale"].astype(str).isin(["O"])
    return df


def enrichir_ul(df):
    df = df.copy()
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df = df[~df["cat_jur"].between(7000, 9999)]
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"]  = df["dateCreation"].dt.year.astype("Int64")
    df["mois"]   = df["dateCreation"].dt.to_period("M").astype(str)
    naf = df["activitePrincipaleUniteLegale"].astype(str).str.strip()
    div = naf.str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df["div_naf"]       = div.fillna("00")
    df["grand_secteur"] = div.map(div_to_secteur).fillna("Autres")
    df["forme_jur"]     = df["cat_jur"].map(code_to_forme)
    df["libelle_taille"]= df["trancheEffectifsUniteLegale"].astype(str).map(TRANCHES).fillna("Non renseigne")
    df["est_employeur"] = df["caractereEmployeurUniteLegale"].astype(str).isin(["O"])
    df["est_ess"]       = df["economieSocialeSolidaireUniteLegale"].astype(str).isin(["O"])
    return df

