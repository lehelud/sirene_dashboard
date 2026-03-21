"""
prep_data.py
------------
Script offline a lancer une fois par mois pour telecharger et pre-agreger
les donnees SIRENE depuis data.gouv.fr.

Usage :
    python prep_data.py

Produit dans ./data/ :
    - creations_annee.parquet
    - cessations_mois.parquet
    - repartition_naf.parquet
    - repartition_taille.parquet
    - carte_commune.parquet
"""

import io
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

URL_UNITES_LEGALES = (
    "https://www.data.gouv.fr/fr/datasets/r/"
    "825f4199-cadd-486c-ac46-a65a8ea1a047"
)
URL_ETABLISSEMENTS = (
    "https://www.data.gouv.fr/fr/datasets/r/"
    "0651fb76-bcf3-4f6a-a38d-bc04fa708576"
)

COLS_UL = [
    "siren",
    "dateCreationUniteLegale",
    "dateCessationUniteLegale",
    "activitePrincipaleUniteLegale",
    "categorieJuridiqueUniteLegale",
    "trancheEffectifsUniteLegale",
    "caractereEmployeurUniteLegale",
    "categorieEntreprise",
    "etatAdministratifUniteLegale",
    "economieSocialeSolidaireUniteLegale",
]

COLS_ETAB = [
    "siren",
    "siret",
    "codeCommuneEtablissement",
    "etatAdministratifEtablissement",
    "activitePrincipaleEtablissement",
    "trancheEffectifsEtablissement",
    "caractereEmployeurEtablissement",
    "etablissementSiege",
    "dateCreationEtablissement",
]

GRANDS_SECTEURS = {
    "A": "Agriculture",
    "B": "Industrie", "C": "Industrie", "D": "Industrie", "E": "Industrie",
    "F": "Construction",
    "G": "Commerce / Transport / HCR",
    "H": "Commerce / Transport / HCR",
    "I": "Commerce / Transport / HCR",
    "J": "Services aux entreprises",
    "K": "Services aux entreprises",
    "L": "Services aux entreprises",
    "M": "Services aux entreprises",
    "N": "Services aux entreprises",
    "O": "Services publics / Sante",
    "P": "Services publics / Sante",
    "Q": "Services publics / Sante",
    "R": "Autres", "S": "Autres", "T": "Autres", "U": "Autres",
}

SECTEURS_CIBLES = [
    "Agriculture", "Industrie", "Construction",
    "Commerce / Transport / HCR", "Services aux entreprises",
]


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def telecharger_fichier(url: str, nom: str) -> bytes:
    """Telecharge un fichier avec barre de progression."""
    print(f"\n Telechargement de {nom}...")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))
    buffer = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=nom) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            buffer.write(chunk)
            bar.update(len(chunk))
    buffer.seek(0)
    return buffer


def lire_parquet_ou_zip(buffer, colonnes: list) -> pd.DataFrame:
    """Lit un fichier parquet (direct ou dans un zip)."""
    try:
        return pd.read_parquet(buffer, columns=colonnes)
    except Exception:
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as z:
            parquet_files = [f for f in z.namelist() if f.endswith(".parquet")]
            if parquet_files:
                with z.open(parquet_files[0]) as f:
                    return pd.read_parquet(f, columns=colonnes)
            csv_files = [f for f in z.namelist() if f.endswith(".csv")]
            with z.open(csv_files[0]) as f:
                return pd.read_csv(f, usecols=colonnes, low_memory=False)


def secteur_depuis_naf(naf_serie: pd.Series) -> pd.Series:
    """Extrait la lettre de section NAF et mappe vers le grand secteur."""
    lettre = naf_serie.astype(str).str[0].str.upper()
    return lettre.map(GRANDS_SECTEURS).fillna("Autres")


# ---------------------------------------------------------------------------
# Chargement des donnees sources
# ---------------------------------------------------------------------------

def charger_unites_legales() -> pd.DataFrame:
    buffer = telecharger_fichier(URL_UNITES_LEGALES, "Unites legales")
    print("Lecture du fichier unites legales...")
    df = lire_parquet_ou_zip(buffer, COLS_UL)
    print(f"   -> {len(df):,} unites legales chargees")
    df["cat_juridique_prefix"] = df["categorieJuridiqueUniteLegale"].astype(str).str[:1]
    df_marchand = df[~df["cat_juridique_prefix"].isin(["7", "9"])].copy()
    print(f"   -> {len(df_marchand):,} unites legales secteur marchand")
    df_marchand["dateCreation"] = pd.to_datetime(df_marchand["dateCreationUniteLegale"], errors="coerce")
    df_marchand["dateCessation"] = pd.to_datetime(df_marchand["dateCessationUniteLegale"], errors="coerce")
    df_marchand["grand_secteur"] = secteur_depuis_naf(df_marchand["activitePrincipaleUniteLegale"])
    df_marchand["section_naf"] = df_marchand["activitePrincipaleUniteLegale"].astype(str).str[:2].str.upper()
    return df_marchand


def charger_etablissements() -> pd.DataFrame:
    buffer = telecharger_fichier(URL_ETABLISSEMENTS, "Etablissements")
    print("Lecture du fichier etablissements...")
    df = lire_parquet_ou_zip(buffer, COLS_ETAB)
    print(f"   -> {len(df):,} etablissements charges")
    df_actif = df[df["etatAdministratifEtablissement"] == "A"].copy()
    print(f"   -> {len(df_actif):,} etablissements actifs")
    df_actif["grand_secteur"] = secteur_depuis_naf(df_actif["activitePrincipaleEtablissement"])
    return df_actif


# ---------------------------------------------------------------------------
# Agregations
# ---------------------------------------------------------------------------

def agreger_creations(df: pd.DataFrame) -> pd.DataFrame:
    print("\n Agregation : creations par annee...")
    df_ok = df[df["dateCreation"].notna() & (df["etatAdministratifUniteLegale"].isin(["A", "C"]))].copy()
    df_ok["annee"] = df_ok["dateCreation"].dt.year.astype("Int64")
    df_ok = df_ok[df_ok["annee"].between(1990, pd.Timestamp.now().year)]
    result = (
        df_ok.groupby(["annee", "grand_secteur", "categorieJuridiqueUniteLegale", "trancheEffectifsUniteLegale"], dropna=False)
        .size().reset_index(name="nb_creations")
    )
    result.columns = ["annee", "grand_secteur", "categorie_juridique", "tranche_effectifs", "nb_creations"]
    print(f"   -> {len(result):,} lignes")
    return result


def agreger_cessations(df: pd.DataFrame) -> pd.DataFrame:
    print("\n Agregation : cessations par mois...")
    df_ok = df[df["dateCessation"].notna() & df["grand_secteur"].isin(SECTEURS_CIBLES)].copy()
    df_ok["annee"] = df_ok["dateCessation"].dt.year.astype("Int64")
    df_ok["mois"] = df_ok["dateCessation"].dt.month.astype("Int64")
    df_ok["annee_mois"] = df_ok["dateCessation"].dt.to_period("M").astype(str)
    df_ok = df_ok[df_ok["annee"].between(2010, pd.Timestamp.now().year)]
    result = df_ok.groupby(["annee_mois", "annee", "mois", "grand_secteur"]).size().reset_index(name="nb_cessations")
    print(f"   -> {len(result):,} lignes")
    return result


def agreger_naf(df: pd.DataFrame) -> pd.DataFrame:
    print("\n Agregation : repartition NAF...")
    result = (
        df[df["etatAdministratifUniteLegale"] == "A"]
        .groupby(["section_naf", "grand_secteur"]).size()
        .reset_index(name="nb_entreprises")
        .sort_values("nb_entreprises", ascending=False)
    )
    print(f"   -> {len(result):,} lignes")
    return result


def agreger_taille(df: pd.DataFrame) -> pd.DataFrame:
    print("\n Agregation : repartition par taille...")
    tranches = {
        "NN": "Non employeur", "00": "0 salarie", "01": "1-2 salaries",
        "02": "3-5 salaries", "03": "6-9 salaries", "11": "10-19 salaries",
        "12": "20-49 salaries", "21": "50-99 salaries", "22": "100-199 salaries",
        "31": "200-249 salaries", "32": "250-499 salaries", "41": "500-999 salaries",
        "42": "1 000-1 999 salaries", "51": "2 000-4 999 salaries",
        "52": "5 000-9 999 salaries", "53": "10 000 salaries et plus",
    }
    df_actif = df[df["etatAdministratifUniteLegale"] == "A"].copy()
    df_actif["libelle_taille"] = df_actif["trancheEffectifsUniteLegale"].astype(str).map(tranches).fillna("Non renseigne")
    result = df_actif.groupby(["trancheEffectifsUniteLegale", "libelle_taille", "grand_secteur"]).size().reset_index(name="nb_entreprises")
    print(f"   -> {len(result):,} lignes")
    return result


def agreger_carte(df_etab: pd.DataFrame) -> pd.DataFrame:
    print("\n Agregation : carte par commune...")
    df_ok = df_etab[df_etab["codeCommuneEtablissement"].notna()].copy()
    df_ok["code_commune"] = df_ok["codeCommuneEtablissement"].astype(str).str.zfill(5)
    result = df_ok.groupby(["code_commune", "grand_secteur"]).size().reset_index(name="nb_etablissements")
    total = df_ok.groupby("code_commune").size().reset_index(name="nb_etablissements")
    total["grand_secteur"] = "Tous secteurs"
    result = pd.concat([result, total], ignore_index=True)
    print(f"   -> {len(result):,} lignes ({result['code_commune'].nunique():,} communes)")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  SIRENE Dashboard - Preparation des donnees")
    print("=" * 60)
    df_ul = charger_unites_legales()
    df_etab = charger_etablissements()
    df_creations = agreger_creations(df_ul)
    df_cessations = agreger_cessations(df_ul)
    df_naf = agreger_naf(df_ul)
    df_taille = agreger_taille(df_ul)
    df_carte = agreger_carte(df_etab)
    print("\n Sauvegarde des fichiers agreges...")
    df_creations.to_parquet(DATA_DIR / "creations_annee.parquet", index=False)
    df_cessations.to_parquet(DATA_DIR / "cessations_mois.parquet", index=False)
    df_naf.to_parquet(DATA_DIR / "repartition_naf.parquet", index=False)
    df_taille.to_parquet(DATA_DIR / "repartition_taille.parquet", index=False)
    df_carte.to_parquet(DATA_DIR / "carte_commune.parquet", index=False)
    print("\n Fichiers generes dans ./data/ :")
    for f in DATA_DIR.glob("*.parquet"):
        taille_mo = f.stat().st_size / 1_048_576
        print(f"   {f.name:<35} {taille_mo:.1f} Mo")
    print("\n Preparation terminee ! Lance maintenant : streamlit run app.py")


if __name__ == "__main__":
    main()
