"""
prep_data.py v4 - Dashboard SIRENE
Effectifs depuis StockEtablissement siege social (annees recentes)
Optimise memoire : sans .copy() inutiles, avec gc.collect()
"""
import gc, io, datetime
from pathlib import Path
import pandas as pd
import requests
from tqdm import tqdm

DATA_DIR = Path("data")
URL_UL   = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"
URL_ETAB = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

COLS_UL = ["siren","dateCreationUniteLegale","etatAdministratifUniteLegale",
           "activitePrincipaleUniteLegale","categorieJuridiqueUniteLegale",
           "economieSocialeSolidaireUniteLegale"]
COLS_ETAB = ["siren","codeCommuneEtablissement","etatAdministratifEtablissement",
             "activitePrincipaleEtablissement","etablissementSiege",
             "trancheEffectifsEtablissement","anneeEffectifsEtablissement"]

TRANCHES = {"NN":"Non-employeur / NC","00":"0 sal. au 31/12","01":"1-2","02":"3-5",
            "03":"6-9","11":"10-19","12":"20-49","21":"50-99","22":"100-199",
            "31":"200-249","32":"250-499","41":"500-999","42":"1000-1999",
            "51":"2000-4999","52":"5000-9999","53":"10000+"}
CAT_JUR = {1:"Entrepreneur individuel",2:"Indivision",3:"Pers. morale etrangere",
           4:"Organisme public",5:"SA / SAS / SARL",6:"Autre pers. morale"}

def div_to_secteur(d):
    try: d=int(d)
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

def statut_employeur(t):
    t = str(t).strip() if pd.notna(t) else ""
    if t=="":    return "Non renseigne"
    if t=="NN":  return "Non-employeur / NC"
    if t=="00":  return "Employeur occasionnel"
    return "Employeur"

def est_oui(s):
    return s.astype(str).str.strip().str.upper().isin(["O","OUI","TRUE","1","YES"])

def telecharger(url, label):
    print(f"\n  Telechargement {label}...")
    r = requests.get(url, stream=True, timeout=300); r.raise_for_status()
    total = int(r.headers.get("content-length",0)); buf = io.BytesIO()
    with tqdm(total=total,unit="B",unit_scale=True,desc=f"  {label}") as bar:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            buf.write(chunk); bar.update(len(chunk))
    buf.seek(0); return buf

def sauver(df, nom):
    p = DATA_DIR/nom; df.to_parquet(p, index=False)
    print(f"  {nom}: {len(df):,} lignes ({p.stat().st_size//1024} Ko)")

def main():
    print("="*60)
    print("  SIRENE Dashboard v4 - Preparation des donnees")
    print("  Effectifs : StockEtablissement siege social")
    print("="*60)
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.datetime.now().year

    # 1. Lecture UL
    buf = telecharger(URL_UL, "StockUniteLegale")
    print("  Lecture parquet UL...")
    df = pd.read_parquet(buf, columns=COLS_UL); del buf; gc.collect()
    print(f"  {len(df):,} unites legales brutes")

    cat_jur = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df = df[~cat_jur.between(7000,9999)].reset_index(drop=True)
    del cat_jur; gc.collect()

    df["cat_jur"]      = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"]        = df["dateCreation"].dt.year.astype("Int64")
    df["mois"]         = df["dateCreation"].dt.to_period("M").astype(str)
    naf = df["activitePrincipaleUniteLegale"].astype(str).str.strip()
    div = naf.str.replace(".","",regex=False).str.extract(r"^(\d{2})",expand=False); del naf
    df["div_naf"]       = div.fillna("00")
    df["grand_secteur"] = div.map(div_to_secteur).fillna("Autres"); del div
    df["forme_jur"]     = df["cat_jur"].map(code_to_forme)
    df["est_ess"]       = est_oui(df["economieSocialeSolidaireUniteLegale"])
    gc.collect()

    mask_act = df["etatAdministratifUniteLegale"] == "A"
    print(f"  {mask_act.sum():,} actives | {len(df):,} total secteur marchand")

    # 2. Creations mensuelles
    print("\n  Agregations UL...")
    mask_cm = df["annee"].between(2010, now) & df["mois"].notna() & df["grand_secteur"].notna()
    cm_cols = df.loc[mask_cm, ["mois","annee","grand_secteur"]]
    cm = pd.DataFrame({"mois":cm_cols["mois"].values,
                       "annee":cm_cols["annee"].astype(int).values,
                       "grand_secteur":cm_cols["grand_secteur"].values})
    del cm_cols, mask_cm; gc.collect()
    sauver(cm.groupby(["mois","annee","grand_secteur"]).size().reset_index(name="nb_creations"),
           "creations_mensuel.parquet")
    del cm; gc.collect()

    # 3. Stock actives
    actives = df.loc[mask_act, ["siren","grand_secteur","forme_jur","div_naf","est_ess"]].reset_index(drop=True)
    del mask_act; gc.collect()
    sauver(actives.groupby(["grand_secteur","forme_jur","div_naf"])
                  .agg(nb=("siren","count"),nb_ess=("est_ess","sum")).reset_index(),
           "stock_actives.parquet")
    sauver(actives.groupby(["forme_jur","grand_secteur"]).size().reset_index(name="nb"),
           "formes_juridiques.parquet")
    sauver(actives.groupby(["div_naf","grand_secteur"]).size().reset_index(name="nb")
                  .sort_values("nb",ascending=False), "naf_detail.parquet")
    siren_actifs = set(actives["siren"].unique())
    del actives; gc.collect()

    # 4. Survie
    cohortes = []
    etat_col = df["etatAdministratifUniteLegale"]
    for annee_c in range(max(2010,now-15), now):
        mask_c = df["annee"] == annee_c
        total  = int(mask_c.sum())
        if total < 100: continue
        for duree in [1,2,3,5,7,10]:
            if annee_c+duree > now: break
            encore = int((mask_c & (etat_col=="A")).sum())
            cohortes.append({"annee_creation":annee_c,"duree_ans":duree,
                             "taux_survie":round(encore/total*100,1),
                             "nb_total":total,"nb_actives":encore})
    del etat_col; sauver(pd.DataFrame(cohortes),"survie.parquet")
    del df; gc.collect()

    # 5. Etablissements
    buf2 = telecharger(URL_ETAB, "StockEtablissement (~2 Go)")
    print("  Lecture parquet etablissements...")
    df_etab = pd.read_parquet(buf2, columns=COLS_ETAB); del buf2; gc.collect()
    print(f"  {len(df_etab):,} etablissements bruts")
    df_etab = df_etab[df_etab["etatAdministratifEtablissement"]=="A"].reset_index(drop=True)
    gc.collect()

    # 6. Effectifs sieges
    print("\n  Calcul effectifs depuis sieges sociaux...")
    mask_s = df_etab["etablissementSiege"].astype(str).str.upper()=="TRUE"
    mask_s &= df_etab["siren"].isin(siren_actifs)
    sieges = df_etab.loc[mask_s, ["siren","activitePrincipaleEtablissement",
                                   "trancheEffectifsEtablissement",
                                   "anneeEffectifsEtablissement"]].reset_index(drop=True)
    del mask_s; gc.collect()
    print(f"  {len(sieges):,} sieges actifs dans le perimetre")

    seuil = now - 3
    sieges["annee_eff"]        = pd.to_numeric(sieges["anneeEffectifsEtablissement"],errors="coerce")
    sieges["statut_employeur"] = sieges["trancheEffectifsEtablissement"].map(statut_employeur)
    sieges["libelle_taille"]   = sieges["trancheEffectifsEtablissement"].map(TRANCHES).fillna("Non renseigne")
    div2 = sieges["activitePrincipaleEtablissement"].astype(str).str.strip()\
        .str.replace(".","",regex=False).str.extract(r"^(\d{2})",expand=False)
    sieges["grand_secteur"] = div2.map(div_to_secteur).fillna("Autres"); del div2

    print("\n  Distribution tous sieges :")
    print(sieges["statut_employeur"].value_counts().to_string())

    mask_rec = sieges["annee_eff"].isna() | (sieges["annee_eff"]>=seuil)
    sieges_rec = sieges[mask_rec].reset_index(drop=True); del sieges, mask_rec; gc.collect()
    print(f"\n  Distribution (annee>={seuil} ou null) :")
    print(sieges_rec["statut_employeur"].value_counts().to_string())
    print(f"  Sieges utilises : {len(sieges_rec):,}")

    emp = sieges_rec.groupby(["grand_secteur","statut_employeur"]).size().reset_index(name="nb")
    tot = sieges_rec.groupby("grand_secteur").size().reset_index(name="nb_total")
    emp = emp.merge(tot, on="grand_secteur"); emp["pct"]=(emp["nb"]/emp["nb_total"]*100).round(1)
    sauver(emp,"employeurs.parquet")
    sauver(sieges_rec.groupby(["grand_secteur","libelle_taille"]).size().reset_index(name="nb"),
           "taille_effectifs.parquet")
    del sieges_rec, emp, tot; gc.collect()

    # 7. Carte
    print("\n  Agregation departements...")
    df_etab["code_dept"] = df_etab["codeCommuneEtablissement"].astype(str).str[:2]\
        .replace({"97":"DOM"})
    div3 = df_etab["activitePrincipaleEtablissement"].astype(str).str.strip()\
        .str.replace(".","",regex=False).str.extract(r"^(\d{2})",expand=False)
    df_etab["grand_secteur"] = div3.map(div_to_secteur).fillna("Autres"); del div3
    dept_agg = df_etab.groupby(["code_dept","grand_secteur"]).size().reset_index(name="nb_etablissements")
    dept_tot = df_etab.groupby("code_dept").size().reset_index(name="nb_total")
    dept_agg = dept_agg.merge(dept_tot, on="code_dept", how="left")
    dept_agg["pct_secteur"] = (dept_agg["nb_etablissements"]/dept_agg["nb_total"]*100).round(1)
    sauver(dept_agg,"departements.parquet")

    print("\n"+"="*60)
    print("  Tous les fichiers generes dans ./data/")
    print("  Lance : python -m streamlit run app.py")
    print("="*60)

if __name__ == "__main__":
    main()
