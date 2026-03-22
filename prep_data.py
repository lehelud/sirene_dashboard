"""
prep_data.py v3 - Dashboard SIRENE

Changement v3 : effectifs lus depuis StockEtablissement (siege social)
au lieu de StockUniteLegale.

Pourquoi :
- trancheEffectifsEtablissement est mise a jour plus frequemment
- anneeEffectifsEtablissement permet de filtrer les donnees recentes
- On utilise uniquement les sieges sociaux (etablissementSiege="true")
  pour avoir 1 effectif par entreprise, comparable a l'approche UL
- On filtre anneeEffectifsEtablissement >= annee_courante - 3
  pour ne garder que les declarations recentes et eviter les zombies

Note INSEE sur trancheEffectifsEtablissement :
  NN = non-employeur OU donnee manquante
  00 = employe dans l-annee, zero au 31/12
  codes positifs = effectif connu
  null = non renseigne (souvent entreprise tres recente)
"""

import io, datetime
from pathlib import Path
import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")

URL_UL   = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"
URL_ETAB = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

# Colonnes UL - on ne prend plus trancheEffectifsUniteLegale
COLS_UL = [
    "siren", "dateCreationUniteLegale", "etatAdministratifUniteLegale",
    "activitePrincipaleUniteLegale", "categorieJuridiqueUniteLegale",
    "economieSocialeSolidaireUniteLegale",
]

# Colonnes Etablissement - on ajoute les champs effectifs + siege
COLS_ETAB = [
    "siren", "siret", "codeCommuneEtablissement",
    "etatAdministratifEtablissement", "activitePrincipaleEtablissement",
    "etablissementSiege",
    "trancheEffectifsEtablissement",
    "anneeEffectifsEtablissement",
]

TRANCHES = {
    "NN": "Non-employeur / NC",
    "00": "0 sal. au 31/12",
    "01": "1-2",
    "02": "3-5",
    "03": "6-9",
    "11": "10-19",
    "12": "20-49",
    "21": "50-99",
    "22": "100-199",
    "31": "200-249",
    "32": "250-499",
    "41": "500-999",
    "42": "1000-1999",
    "51": "2000-4999",
    "52": "5000-9999",
    "53": "10000+",
}

CAT_JUR = {
    1: "Entrepreneur individuel",
    2: "Indivision",
    3: "Pers. morale etrangere",
    4: "Organisme public",
    5: "SA / SAS / SARL",
    6: "Autre pers. morale",
}


def div_to_secteur(div_str):
    try:
        d = int(div_str)
    except:
        return "Autres"
    if 1  <= d <= 3:  return "Agriculture"
    if 5  <= d <= 39: return "Industrie"
    if 41 <= d <= 43: return "Construction"
    if 45 <= d <= 56: return "Commerce / Transport / HCR"
    if 58 <= d <= 66: return "Services aux entreprises"
    if 68 <= d <= 75: return "Services aux entreprises"
    if 77 <= d <= 82: return "Services aux entreprises"
    if 84 <= d <= 88: return "Services publics / Sante"
    return "Autres"


def code_to_forme(cat):
    try:
        return CAT_JUR.get(int(str(cat)[:1]), "Autre")
    except:
        return "Autre"


def statut_employeur(tranche):
    t = str(tranche).strip() if pd.notna(tranche) else ""
    if t == "":   return "Non renseigne"
    if t == "NN": return "Non-employeur / NC"
    if t == "00": return "Employeur occasionnel"
    return "Employeur"


def est_oui(serie):
    return serie.astype(str).str.strip().str.upper().isin(["O", "OUI", "TRUE", "1", "YES"])


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
    print(f"  {nom}: {len(df):,} lignes ({p.stat().st_size // 1024} Ko)")


def enrichir_ul(df):
    df = df.copy()
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df = df[~df["cat_jur"].between(7000, 9999)]
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["mois"]  = df["dateCreation"].dt.to_period("M").astype(str)
    naf = df["activitePrincipaleUniteLegale"].astype(str).str.strip()
    div = naf.str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df["div_naf"]       = div.fillna("00")
    df["grand_secteur"] = div.map(div_to_secteur).fillna("Autres")
    df["forme_jur"]     = df["cat_jur"].map(code_to_forme)
    df["est_ess"]       = est_oui(df["economieSocialeSolidaireUniteLegale"])
    return df

def main():
    print("=" * 60)
    print("  SIRENE Dashboard v3 - Preparation des donnees")
    print("  Effectifs : StockEtablissement siege social (annees recentes)")
    print("=" * 60)
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now().year

    # 1. Unites legales
    buf = telecharger(URL_UL, "StockUniteLegale")
    print("  Lecture parquet UL...")
    df_raw = pd.read_parquet(buf, columns=COLS_UL)
    buf = None
    print(f"  {len(df_raw):,} unites legales brutes")

    df = enrichir_ul(df_raw)
    del df_raw

    actives = df[df["etatAdministratifUniteLegale"] == "A"][["siren","grand_secteur","forme_jur","div_naf","est_ess"]].copy()
    print(f"  {len(actives):,} actives | {len(df):,} total secteur marchand")

    # 2. Agregations depuis UL
    print("\n  Agregations UL...")

    mask_cm = df["annee"].between(2010, now) & df["mois"].notna() & df["grand_secteur"].notna()
    _cm = df.loc[mask_cm, ["mois","annee","grand_secteur"]].reset_index(drop=True)
    _cm["annee"] = _cm["annee"].astype(int)
    del mask_cm
    sauver(
        _cm.groupby(["mois", "annee", "grand_secteur"])
           .size().reset_index(name="nb_creations"),
        "creations_mensuel.parquet"
    )
    del _cm
    import gc; gc.collect()

    sauver(
        actives.groupby(["grand_secteur", "forme_jur", "div_naf"])
               .agg(nb=("siren", "count"), nb_ess=("est_ess", "sum"))
               .reset_index(),
        "stock_actives.parquet"
    )

    sauver(
        actives.groupby(["forme_jur", "grand_secteur"]).size().reset_index(name="nb"),
        "formes_juridiques.parquet"
    )

    sauver(
        actives.groupby(["div_naf", "grand_secteur"]).size().reset_index(name="nb")
               .sort_values("nb", ascending=False),
        "naf_detail.parquet"
    )

    # Survie
    cohortes = []
    for annee_c in range(max(2010, now - 15), now):
        cohort = df[df["annee"] == annee_c]
        total  = len(cohort)
        if total < 100:
            continue
        for duree in [1, 2, 3, 5, 7, 10]:
            if annee_c + duree > now:
                break
            encore = len(cohort[cohort["etatAdministratifUniteLegale"] == "A"])
            cohortes.append({
                "annee_creation": annee_c, "duree_ans": duree,
                "taux_survie": round(encore / total * 100, 1),
                "nb_total": total, "nb_actives": encore,
            })
    sauver(pd.DataFrame(cohortes), "survie.parquet")
    del df
    import gc; gc.collect()

    siren_actifs = set(actives["siren"].unique())
    del df, actives

    # 3. Etablissements
    buf2 = telecharger(URL_ETAB, "StockEtablissement (~2 Go)")
    print("  Lecture parquet etablissements...")
    df_etab = pd.read_parquet(buf2, columns=COLS_ETAB)
    buf2 = None
    print(f"  {len(df_etab):,} etablissements bruts")

    df_etab = df_etab[df_etab["etatAdministratifEtablissement"] == "A"].copy()

    # 4. Effectifs depuis les sieges sociaux
    print("\n  Calcul effectifs depuis sieges sociaux...")

    sieges = df_etab[df_etab["etablissementSiege"].astype(str).str.upper() == "TRUE"].copy()
    print(f"  {len(sieges):,} sieges sociaux actifs")

    seuil_annee = now - 3
    sieges["annee_eff"] = pd.to_numeric(sieges["anneeEffectifsEtablissement"], errors="coerce")
    sieges = sieges[sieges["siren"].isin(siren_actifs)]
    sieges["statut_employeur"] = sieges["trancheEffectifsEtablissement"].map(statut_employeur)
    sieges["libelle_taille"]   = sieges["trancheEffectifsEtablissement"].map(TRANCHES).fillna("Non renseigne")

    div2 = sieges["activitePrincipaleEtablissement"].astype(str).str.strip()\
        .str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    sieges["grand_secteur"] = div2.map(div_to_secteur).fillna("Autres")

    print("\n  Distribution effectifs (TOUS sieges actifs) :")
    print(sieges["statut_employeur"].value_counts().to_string())

    # Filtre : garder annee recente OU null (entreprise recente sans declaration)
    sieges_rec = sieges[
        sieges["annee_eff"].isna() |
        (sieges["annee_eff"] >= seuil_annee)
    ]
    print(f"\n  Distribution effectifs (annee >= {seuil_annee} OU null) :")
    print(sieges_rec["statut_employeur"].value_counts().to_string())
    print(f"  Total sieges utilises : {len(sieges_rec):,} / {len(sieges):,}")
    print(f"  Exclus (declarations obsoletes anterieures a {seuil_annee}) : {len(sieges) - len(sieges_rec):,}")

    emp = sieges_rec.groupby(["grand_secteur", "statut_employeur"])\
        .size().reset_index(name="nb")
    tot = sieges_rec.groupby("grand_secteur").size().reset_index(name="nb_total")
    emp = emp.merge(tot, on="grand_secteur")
    emp["pct"] = (emp["nb"] / emp["nb_total"] * 100).round(1)
    sauver(emp, "employeurs.parquet")

    taille = sieges_rec.groupby(["grand_secteur", "libelle_taille"])\
        .size().reset_index(name="nb")
    sauver(taille, "taille_effectifs.parquet")

    # 5. Carte par departement
    print("\n  Agregation departements...")
    df_etab["code_dept"] = df_etab["codeCommuneEtablissement"].astype(str).str[:2]\
        .replace({"97": "DOM"})
    div3 = df_etab["activitePrincipaleEtablissement"].astype(str).str.strip()\
        .str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df_etab["grand_secteur"] = div3.map(div_to_secteur).fillna("Autres")

    dept_agg = df_etab.groupby(["code_dept", "grand_secteur"])\
        .size().reset_index(name="nb_etablissements")
    dept_tot = df_etab.groupby("code_dept").size().reset_index(name="nb_total")
    dept_agg = dept_agg.merge(dept_tot, on="code_dept", how="left")
    dept_agg["pct_secteur"] = (dept_agg["nb_etablissements"] / dept_agg["nb_total"] * 100).round(1)
    sauver(dept_agg, "departements.parquet")

    print("\n" + "=" * 60)
    print("  Tous les fichiers generes dans ./data/")
    print("  Lance : python -m streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
