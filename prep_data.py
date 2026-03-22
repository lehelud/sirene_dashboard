"""
prep_data.py v2 - Dashboard SIRENE
7 fichiers parquet generes dans ./data/
"""
import io
import datetime
from pathlib import Path
import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")""""""
prep_data.py v2 - Dashboard SIRENE

Note INSEE sur trancheEffectifsUniteLegale :
  NN = non-employeur OU donnee manquante (entreprise recente sans declaration)
  00 = 0 salarie au 31/12 mais a employe dans l-annee
  01..53 = employeur avec effectif connu
  null = non renseigne (source non disponible)

  caractereEmployeurUniteLegale est TOUJOURS null depuis 2023 (variable abandonnee INSEE)
  -> on utilise trancheEffectifsUniteLegale comme source unique
"""
import io, datetime
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
    "trancheEffectifsUniteLegale","economieSocialeSolidaireUniteLegale",
]
COLS_ETAB = [
    "siren","codeCommuneEtablissement","etatAdministratifEtablissement",
    "activitePrincipaleEtablissement",
]

TRANCHES = {
    "NN":"Non-employeur / NC","00":"0 sal. au 31/12","01":"1-2","02":"3-5","03":"6-9",
    "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
    "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999",
    "52":"5000-9999","53":"10000+",
}

CAT_JUR = {
    1:"Entrepreneur individuel",2:"Indivision",3:"Pers. morale etrangere",
    4:"Organisme public",5:"SA / SAS / SARL",6:"Autre pers. morale",
}

def div_to_secteur(div_str):
    try: d = int(div_str)
    except: return "Autres"
    if 1<=d<=3:   return "Agriculture"
    if 5<=d<=39:  return "Industrie"
    if 41<=d<=43: return "Construction"
    if 45<=d<=56: return "Commerce / Transport / HCR"
    if 58<=d<=66: return "Services aux entreprises"
    if 68<=d<=75: return "Services aux entreprises"
    if 77<=d<=82: return "Services aux entreprises"
    if 84<=d<=88: return "Services publics / Sante"
    return "Autres"

def code_to_forme(cat):
    try: return CAT_JUR.get(int(str(cat)[:1]), "Autre")
    except: return "Autre"

def statut_employeur(tranche):
    """
    3 categories selon la doc INSEE :
    - Employeur (effectif connu)  : codes 01 a 53
    - Employeur occasionnel       : code 00 (employe dans l-annee, 0 au 31/12)
    - Non-employeur               : code NN (sans salarie declare)
    - Non renseigne               : null/NaN (entreprise recente ou donnee absente)
    """
    t = str(tranche).strip() if pd.notna(tranche) else ""
    if t == "":               return "Non renseigne"
    if t == "NN":             return "Non-employeur"
    if t == "00":             return "Employeur occasionnel"
    return "Employeur"

def est_oui(serie):
    return serie.astype(str).str.strip().str.upper().isin(["O","OUI","TRUE","1","YES"])

def telecharger(url, label):
    print(f"\n  Telechargement {label}...")
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=f"  {label}") as bar:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            buf.write(chunk); bar.update(len(chunk))
    buf.seek(0)
    return buf

def sauver(df, nom):
    p = DATA_DIR / nom
    df.to_parquet(p, index=False)
    print(f"  {nom}: {len(df):,} lignes  ({p.stat().st_size//1024} Ko)")

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
    df["tranche_brute"] = df["trancheEffectifsUniteLegale"].astype(str).str.strip()
    df["libelle_taille"]= df["trancheEffectifsUniteLegale"].map(TRANCHES).fillna("Non renseigne")
    # Statut employeur avec 4 categories distinctes
    df["statut_employeur"] = df["trancheEffectifsUniteLegale"].map(statut_employeur)
    df["est_ess"] = est_oui(df["economieSocialeSolidaireUniteLegale"])
    # Diagnostic
    print("  Distribution statut employeur:")
    print(df["statut_employeur"].value_counts().to_string())
    return df

prep_data.py v2 - Dashboard SIRENE
7 fichiers parquet generes dans ./data/
Fix: detection robuste employeurs (O/N/True/False/1/0)
"""
import io, datetime
from pathlib import Path
import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")
URL_UL   = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"
URL_ETAB = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

COLS_UL  = ["siren","dateCreationUniteLegale","etatAdministratifUniteLegale",
            "activitePrincipaleUniteLegale","categorieJuridiqueUniteLegale",
            "trancheEffectifsUniteLegale","caractereEmployeurUniteLegale",
            "economieSocialeSolidaireUniteLegale"]
COLS_ETAB= ["siren","codeCommuneEtablissement","etatAdministratifEtablissement",
            "activitePrincipaleEtablissement"]

TRANCHES = {
    "NN":"Non employeur","00":"0 sal.","01":"1-2","02":"3-5","03":"6-9",
    "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
    "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999",
    "52":"5000-9999","53":"10000+",
}
CAT_JUR = {
    1:"Entrepreneur individuel",2:"Indivision",3:"Pers. morale etrangere",
    4:"Organisme public",5:"SA / SAS / SARL",6:"Autre pers. morale",
}

def div_to_secteur(div_str):
    try: d = int(div_str)
    except: return "Autres"
    if 1<=d<=3:   return "Agriculture"
    if 5<=d<=39:  return "Industrie"
    if 41<=d<=43: return "Construction"
    if 45<=d<=56: return "Commerce / Transport / HCR"
    if 58<=d<=66: return "Services aux entreprises"
    if 68<=d<=75: return "Services aux entreprises"
    if 77<=d<=82: return "Services aux entreprises"
    if 84<=d<=88: return "Services publics / Sante"
    return "Autres"

def code_to_forme(cat):
    try: return CAT_JUR.get(int(str(cat)[:1]), "Autre")
    except: return "Autre"

def est_oui(serie):
    """Detection robuste O/N, True/False, 1/0, oui/non."""
    s = serie.astype(str).str.strip().str.upper()
    return s.isin(["O", "OUI", "TRUE", "1", "YES"])

def telecharger(url, label):
    print(f"\n  Telechargement {label}...")
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=f"  {label}") as bar:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            buf.write(chunk); bar.update(len(chunk))
    buf.seek(0)
    return buf

def sauver(df, nom):
    p = DATA_DIR / nom
    df.to_parquet(p, index=False)
    print(f"  {nom}: {len(df):,} lignes  ({p.stat().st_size//1024} Ko)")

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
    df["libelle_taille"]= df["trancheEffectifsUniteLegale"].astype(str).map(TRANCHES).fillna("Non renseigne")
    # Detection robuste employeurs
    df["est_employeur"] = est_oui(df["caractereEmployeurUniteLegale"])
    df["est_ess"]       = est_oui(df["economieSocialeSolidaireUniteLegale"])
    # Diagnostic
    n_emp = df["est_employeur"].sum()
    print(f"  Employe urs detectes : {n_emp:,}")
    if n_emp == 0:
        vals = df["caractereEmployeurUniteLegale"].value_counts().head(5)
        print(f"  ATTENTION valeurs trouvees : {vals.to_dict()}")
    return df

URL_UL   = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"
URL_ETAB = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

COLS_UL  = ["siren","dateCreationUniteLegale","etatAdministratifUniteLegale","activitePrincipaleUniteLegale","categorieJuridiqueUniteLegale","trancheEffectifsUniteLegale","caractereEmployeurUniteLegale","economieSocialeSolidaireUniteLegale"]
COLS_ETAB= ["siren","codeCommuneEtablissement","etatAdministratifEtablissement","activitePrincipaleEtablissement"]
TRANCHES = {"NN":"Non employeur","00":"0 sal.","01":"1-2","02":"3-5","03":"6-9","11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249","32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999","52":"5000-9999","53":"10000+"}
CAT_JUR  = {1:"Entrepreneur individuel",2:"Indivision / Fiducie",3:"Pers. morale etrangere",4:"Organisme public",5:"SA / SAS / SARL",6:"Autre pers. morale"}

def div_to_secteur(div_str):
    try: d=int(div_str)
    except: return "Autres"
    if 1<=d<=3:   return "Agriculture"
    if 5<=d<=39:  return "Industrie"
    if 41<=d<=43: return "Construction"
    if 45<=d<=56: return "Commerce / Transport / HCR"
    if 58<=d<=66: return "Services aux entreprises"
    if 68<=d<=75: return "Services aux entreprises"
    if 77<=d<=82: return "Services aux entreprises"
    if 84<=d<=88: return "Services publics / Sante"
    return "Autres"

def code_to_forme(cat):
    try: return CAT_JUR.get(int(str(cat)[:1]),"Autre")
    except: return "Autre"

def telecharger(url, label):
    print(f"\n  Telechargement {label}...")
    r=requests.get(url,stream=True,timeout=300); r.raise_for_status()
    total=int(r.headers.get("content-length",0))
    buf=io.BytesIO()
    with tqdm(total=total,unit="B",unit_scale=True,desc=f"  {label}") as bar:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            buf.write(chunk); bar.update(len(chunk))
    buf.seek(0); return buf

def sauver(df, nom):
    p=DATA_DIR/nom; df.to_parquet(p,index=False)
    print(f"  {nom}: {len(df):,} lignes  ({p.stat().st_size//1024} Ko)")

def enrichir_ul(df):
    df=df.copy()
    df["cat_jur"]=df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df=df[~df["cat_jur"].between(7000,9999)]
    df["dateCreation"]=pd.to_datetime(df["dateCreationUniteLegale"],errors="coerce")
    df["annee"]=df["dateCreation"].dt.year.astype("Int64")
    df["mois"]=df["dateCreation"].dt.to_period("M").astype(str)
    naf=df["activitePrincipaleUniteLegale"].astype(str).str.strip()
    div=naf.str.replace(".",  "",regex=False).str.extract(r"^(\d{2})",expand=False)
    df["div_naf"]=div.fillna("00")
    df["grand_secteur"]=div.map(div_to_secteur).fillna("Autres")
    df["forme_jur"]=df["cat_jur"].map(code_to_forme)
    df["libelle_taille"]=df["trancheEffectifsUniteLegale"].astype(str).map(TRANCHES).fillna("Non renseigne")
    df["est_employeur"]=df["caractereEmployeurUniteLegale"].astype(str).isin(["O"])
    df["est_ess"]=df["economieSocialeSolidaireUniteLegale"].astype(str).isin(["O"])
    return df

def main():
    print("=" * 60)
    print("  SIRENE Dashboard v2 - Preparation des donnees")
    print("=" * 60)
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now().year

    # 1. StockUniteLegale
    buf=telecharger(URL_UL,"StockUniteLegale")
    print("  Lecture parquet...")
    df_raw=pd.read_parquet(buf,columns=COLS_UL)
    print(f"  {len(df_raw):,} unites legales"); buf=None
    df=enrichir_ul(df_raw); del df_raw
    actives=df[df["etatAdministratifUniteLegale"]=="A"]
    print(f"  {len(actives):,} actives, {len(df):,} total secteur marchand")

    print("\n  Agregations...")
    sauver(df[df["annee"].between(2010,now)].groupby(["mois","annee","grand_secteur"],dropna=False).size().reset_index(name="nb_creations"), "creations_mensuel.parquet")
    sauver(actives.groupby(["grand_secteur","forme_jur","libelle_taille","div_naf"]).agg(nb=("siren","count"),nb_employeurs=("est_employeur","sum"),nb_ess=("est_ess","sum")).reset_index(), "stock_actives.parquet")
    sauver(actives.groupby(["forme_jur","grand_secteur"]).size().reset_index(name="nb"), "formes_juridiques.parquet")
    sauver(actives.groupby(["grand_secteur","est_employeur"]).size().reset_index(name="nb"), "employeurs.parquet")
    sauver(actives.groupby(["div_naf","grand_secteur"]).size().reset_index(name="nb").sort_values("nb",ascending=False), "naf_detail.parquet")

    cohortes=[]
    for annee_c in range(max(2010,now-15),now):
        cohort=df[df["annee"]==annee_c]; total=len(cohort)
        if total<100: continue
        for duree in [1,2,3,5,7,10]:
            if annee_c+duree>now: break
            encore=len(cohort[cohort["etatAdministratifUniteLegale"]=="A"])
            cohortes.append({"annee_creation":annee_c,"duree_ans":duree,"taux_survie":round(encore/total*100,1),"nb_total":total,"nb_actives":encore})
    sauver(pd.DataFrame(cohortes),"survie.parquet")
    del df, actives

    # 2. StockEtablissement pour geographie
    buf2=telecharger(URL_ETAB,"StockEtablissement (~2 Go)")
    print("  Lecture parquet etablissements...")
    df_etab=pd.read_parquet(buf2,columns=COLS_ETAB); buf2=None
    print(f"  {len(df_etab):,} etablissements")
    df_etab=df_etab[df_etab["etatAdministratifEtablissement"]=="A"].copy()
    df_etab["code_dept"]=df_etab["codeCommuneEtablissement"].astype(str).str[:2].replace({"97":"DOM"})
    div2=df_etab["activitePrincipaleEtablissement"].astype(str).str.strip().str.replace(".",  "",regex=False).str.extract(r"^(\d{2})",expand=False)
    df_etab["grand_secteur"]=div2.map(div_to_secteur).fillna("Autres")
    dept_agg=df_etab.groupby(["code_dept","grand_secteur"]).size().reset_index(name="nb_etablissements")
    dept_tot=df_etab.groupby("code_dept").size().reset_index(name="nb_total")
    dept_agg=dept_agg.merge(dept_tot,on="code_dept",how="left")
    dept_agg["pct_secteur"]=(dept_agg["nb_etablissements"]/dept_agg["nb_total"]*100).round(1)
    sauver(dept_agg,"departements.parquet")

    print("\n" + "="*60)
    print("  Tous les fichiers generes dans ./data/")
    print("  Lance : python -m streamlit run app.py")
    print("="*60)


if __name__ == "__main__":
    main()

def main():
    print("=" * 60)
    print("  SIRENE Dashboard v2 - Preparation des donnees")
    print("=" * 60)
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now().year

    buf = telecharger(URL_UL, "StockUniteLegale")
    print("  Lecture parquet...")
    df_raw = pd.read_parquet(buf, columns=COLS_UL); buf = None
    print(f"  {len(df_raw):,} unites legales brutes")
    df = enrichir_ul(df_raw); del df_raw
    actives = df[df["etatAdministratifUniteLegale"] == "A"]
    print(f"  {len(actives):,} actives | {len(df):,} total secteur marchand")

    print("\n  Agregations...")

    # Creations mensuelles
    sauver(
        df[df["annee"].between(2010, now)]
          .groupby(["mois","annee","grand_secteur"], dropna=False)
          .size().reset_index(name="nb_creations"),
        "creations_mensuel.parquet"
    )

    # Stock actives enrichi
    sauver(
        actives.groupby(["grand_secteur","forme_jur","libelle_taille","div_naf"])
               .agg(nb=("siren","count"),
                    nb_employeurs=("est_employeur","sum"),
                    nb_ess=("est_ess","sum"))
               .reset_index(),
        "stock_actives.parquet"
    )

    # Formes juridiques
    sauver(
        actives.groupby(["forme_jur","grand_secteur"]).size().reset_index(name="nb"),
        "formes_juridiques.parquet"
    )

    # Employeurs - stocker les valeurs brutes par secteur
    emp = actives.groupby("grand_secteur").agg(
        nb_total=("siren","count"),
        nb_employeurs=("est_employeur","sum"),
        nb_ess=("est_ess","sum"),
    ).reset_index()
    emp["pct_employeurs"] = (emp["nb_employeurs"] / emp["nb_total"] * 100).round(1)
    sauver(emp, "employeurs.parquet")

    # NAF detail
    sauver(
        actives.groupby(["div_naf","grand_secteur"]).size().reset_index(name="nb")
               .sort_values("nb", ascending=False),
        "naf_detail.parquet"
    )

    # Survie par cohorte
    cohortes = []
    for annee_c in range(max(2010, now-15), now):
        cohort = df[df["annee"] == annee_c]; total = len(cohort)
        if total < 100: continue
        for duree in [1, 2, 3, 5, 7, 10]:
            if annee_c + duree > now: break
            encore = len(cohort[cohort["etatAdministratifUniteLegale"] == "A"])
            cohortes.append({"annee_creation":annee_c,"duree_ans":duree,
                             "taux_survie":round(encore/total*100,1),
                             "nb_total":total,"nb_actives":encore})
    sauver(pd.DataFrame(cohortes), "survie.parquet")
    del df, actives

    # Geographie via etablissements
    buf2 = telecharger(URL_ETAB, "StockEtablissement (~2 Go)")
    print("  Lecture parquet etablissements...")
    df_etab = pd.read_parquet(buf2, columns=COLS_ETAB); buf2 = None
    print(f"  {len(df_etab):,} etablissements")
    df_etab = df_etab[df_etab["etatAdministratifEtablissement"] == "A"].copy()
    df_etab["code_dept"] = df_etab["codeCommuneEtablissement"].astype(str).str[:2]
    df_etab["code_dept"] = df_etab["code_dept"].replace({"97":"DOM"})
    div2 = df_etab["activitePrincipaleEtablissement"].astype(str).str.strip()\
               .str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df_etab["grand_secteur"] = div2.map(div_to_secteur).fillna("Autres")
    dept_agg = df_etab.groupby(["code_dept","grand_secteur"]).size().reset_index(name="nb_etablissements")
    dept_tot = df_etab.groupby("code_dept").size().reset_index(name="nb_total")
    dept_agg = dept_agg.merge(dept_tot, on="code_dept", how="left")
    dept_agg["pct_secteur"] = (dept_agg["nb_etablissements"] / dept_agg["nb_total"] * 100).round(1)
    sauver(dept_agg, "departements.parquet")

    print("\n" + "="*60)
    print("  Tous les fichiers generes dans ./data/")
    print("  Lance : python -m streamlit run app.py")
    print("="*60)


if __name__ == "__main__":
    main()

def main():
    print("=" * 60)
    print("  SIRENE Dashboard v2 - Preparation des donnees")
    print("=" * 60)
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now().year

    buf = telecharger(URL_UL, "StockUniteLegale")
    print("  Lecture parquet...")
    df_raw = pd.read_parquet(buf, columns=COLS_UL); buf = None
    print(f"  {len(df_raw):,} unites legales brutes")
    df = enrichir_ul(df_raw); del df_raw
    actives = df[df["etatAdministratifUniteLegale"] == "A"]
    print(f"  {len(actives):,} actives | {len(df):,} total secteur marchand")

    print("\n  Agregations...")

    sauver(
        df[df["annee"].between(2010, now)]
          .groupby(["mois","annee","grand_secteur"], dropna=False)
          .size().reset_index(name="nb_creations"),
        "creations_mensuel.parquet"
    )

    sauver(
        actives.groupby(["grand_secteur","forme_jur","libelle_taille","div_naf"])
               .agg(nb=("siren","count"), nb_ess=("est_ess","sum"))
               .reset_index(),
        "stock_actives.parquet"
    )

    sauver(
        actives.groupby(["forme_jur","grand_secteur"]).size().reset_index(name="nb"),
        "formes_juridiques.parquet"
    )

    # Employeurs : 4 categories avec note de fiabilite
    emp = actives.groupby(["grand_secteur","statut_employeur"])\
                 .size().reset_index(name="nb")
    # Calcul pct par secteur
    tot = actives.groupby("grand_secteur").size().reset_index(name="nb_total")
    emp = emp.merge(tot, on="grand_secteur")
    emp["pct"] = (emp["nb"] / emp["nb_total"] * 100).round(1)
    sauver(emp, "employeurs.parquet")

    sauver(
        actives.groupby(["div_naf","grand_secteur"]).size().reset_index(name="nb")
               .sort_values("nb", ascending=False),
        "naf_detail.parquet"
    )

    cohortes = []
    for annee_c in range(max(2010, now-15), now):
        cohort = df[df["annee"] == annee_c]; total = len(cohort)
        if total < 100: continue
        for duree in [1, 2, 3, 5, 7, 10]:
            if annee_c + duree > now: break
            encore = len(cohort[cohort["etatAdministratifUniteLegale"] == "A"])
            cohortes.append({"annee_creation":annee_c,"duree_ans":duree,
                             "taux_survie":round(encore/total*100,1),
                             "nb_total":total,"nb_actives":encore})
    sauver(pd.DataFrame(cohortes), "survie.parquet")
    del df, actives

    buf2 = telecharger(URL_ETAB, "StockEtablissement (~2 Go)")
    print("  Lecture parquet etablissements...")
    df_etab = pd.read_parquet(buf2, columns=COLS_ETAB); buf2 = None
    print(f"  {len(df_etab):,} etablissements")
    df_etab = df_etab[df_etab["etatAdministratifEtablissement"] == "A"].copy()
    df_etab["code_dept"] = df_etab["codeCommuneEtablissement"].astype(str).str[:2]\
                               .replace({"97":"DOM"})
    div2 = df_etab["activitePrincipaleEtablissement"].astype(str).str.strip()\
               .str.replace(".", "", regex=False).str.extract(r"^(\d{2})", expand=False)
    df_etab["grand_secteur"] = div2.map(div_to_secteur).fillna("Autres")
    dept_agg = df_etab.groupby(["code_dept","grand_secteur"]).size().reset_index(name="nb_etablissements")
    dept_tot = df_etab.groupby("code_dept").size().reset_index(name="nb_total")
    dept_agg = dept_agg.merge(dept_tot, on="code_dept", how="left")
    dept_agg["pct_secteur"] = (dept_agg["nb_etablissements"] / dept_agg["nb_total"] * 100).round(1)
    sauver(dept_agg, "departements.parquet")

    print("\n" + "="*60)
    print("  Tous les fichiers generes dans ./data/")
    print("  Lance : python -m streamlit run app.py")
    print("="*60)


if __name__ == "__main__":
    main()
