"""
app.py - Dashboard SIRENE
Lit les fichiers parquet pre-agréges (generes par prep_data.py)
Si absent : tente le telechargement depuis data.gouv.fr (Streamlit Cloud)
"""
import io
import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

warnings.filterwarnings("ignore")

DATA_DIR = Path("data")
URL_UL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"

COLS_UL = [
    "siren","dateCreationUniteLegale","etatAdministratifUniteLegale",
    "activitePrincipaleUniteLegale","categorieJuridiqueUniteLegale",
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
COLOR_MAP = {
    "Agriculture":"#2ecc71","Industrie":"#3498db","Construction":"#e67e22",
    "Commerce / Transport / HCR":"#9b59b6","Services aux entreprises":"#e74c3c",
    "Services publics / Sante":"#1abc9c","Autres":"#95a5a6",
}
TRANCHES = {
    "NN":"Non employeur","00":"0 salarie","01":"1-2","02":"3-5","03":"6-9",
    "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
    "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999","52":"5000-9999","53":"10000+",
}


@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    """Lit depuis data/ si disponible, sinon telecharge depuis data.gouv.fr"""
    f_creations = DATA_DIR / "creations_annee.parquet"
    f_naf = DATA_DIR / "repartition_naf.parquet"
    f_taille = DATA_DIR / "repartition_taille.parquet"
    f_cessations = DATA_DIR / "cessations_mois.parquet"

    if all(f.exists() for f in [f_creations, f_naf, f_taille]):
        # Mode local ou Cloud avec fichiers pré-agrégés
        return {
            "creations": pd.read_parquet(f_creations),
            "naf": pd.read_parquet(f_naf),
            "taille": pd.read_parquet(f_taille),
            "cessations": pd.read_parquet(f_cessations) if f_cessations.exists() else pd.DataFrame(),
            "mode": "local"
        }
    else:
        # Mode Cloud sans fichiers : telecharge et agrege a la volee
        return _charger_depuis_web()


def _charger_depuis_web():
    prog = st.progress(0, "Telechargement SIRENE (~650 Mo)...")
    r = requests.get(URL_UL, timeout=300, stream=True)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    downloaded = 0
    for chunk in r.iter_content(chunk_size=10*1024*1024):
        buf.write(chunk); downloaded += len(chunk)
        if total > 0:
            prog.progress(min(downloaded/total*0.7, 0.7),
                f"{downloaded//1024//1024} Mo / {total//1024//1024} Mo")
    buf.seek(0)
    prog.progress(0.75, "Lecture parquet...")
    import pyarrow.parquet as pq
    df = pq.read_table(buf, columns=COLS_UL).to_pandas()
    prog.progress(0.85, "Agregation...")
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    df = df[~df["cat_jur"].between(7000, 9999)].copy()
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["grand_secteur"] = df["activitePrincipaleUniteLegale"].astype(str).str[0].str.upper().map(GRANDS_SECTEURS).fillna("Autres")
    df["libelle_taille"] = df["trancheEffectifsUniteLegale"].astype(str).map(TRANCHES).fillna("Non renseigne")
    creations = df[df["annee"].between(2010, 2026)].groupby(["annee","grand_secteur"]).size().reset_index(name="nb_creations")
    naf = df[df["etatAdministratifUniteLegale"]=="A"].groupby(["grand_secteur"]).size().reset_index(name="nb_entreprises")
    taille = df[df["etatAdministratifUniteLegale"]=="A"].groupby(["libelle_taille","grand_secteur"]).size().reset_index(name="nb_entreprises")
    prog.progress(1.0, "Pret !"); prog.empty()
    return {"creations":creations,"naf":naf,"taille":taille,"cessations":pd.DataFrame(),"mode":"web"}


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : data.gouv.fr | Secteur marchand | Mise a jour mensuelle")

    with st.spinner("Chargement des donnees..."):
        data = charger_donnees()

    if data["mode"] == "local":
        st.sidebar.success("Donnees locales chargees")
    else:
        st.sidebar.info("Donnees telechar geees depuis data.gouv.fr")

    df_c = data["creations"]
    df_naf = data["naf"]
    df_taille = data["taille"]

    # Sidebar filtres
    st.sidebar.title("Filtres")
    annees = sorted(df_c["annee"].dropna().unique().tolist())
    amin, amax = int(min(annees)), int(max(annees))
    plage = st.sidebar.slider("Periode", amin, amax, (max(amin, amax-10), amax))
    secteurs = sorted(df_c["grand_secteur"].dropna().unique().tolist())
    sects = st.sidebar.multiselect("Secteurs", secteurs, default=secteurs)
    st.sidebar.caption("Source : Base SIRENE - data.gouv.fr")

    # KPIs
    mask = df_c["annee"].between(plage[0],plage[1]) & df_c["grand_secteur"].isin(sects)
    ay = plage[1]
    total = int(df_c[mask]["nb_creations"].sum())
    ca = int(df_c[(df_c["annee"]==ay) & df_c["grand_secteur"].isin(sects)]["nb_creations"].sum())
    cp = int(df_c[(df_c["annee"]==ay-1) & df_c["grand_secteur"].isin(sects)]["nb_creations"].sum())
    delta = ((ca-cp)/cp*100) if cp else 0
    actives = int(df_naf[df_naf["grand_secteur"].isin(sects)]["nb_entreprises"].sum())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Creations (periode)", f"{total:,}".replace(",","."))
    c2.metric(f"Creees en {ay}", f"{ca:,}".replace(",","."), f"{delta:+.1f}%")
    c3.metric("Actives", f"{actives:,}".replace(",","."))
    c4.metric("Secteurs", len(sects))
    st.divider()

    tab1,tab2,tab3 = st.tabs(["Creations","Secteurs NAF","Taille"])

    with tab1:
        d = df_c[mask].groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
        fig = px.bar(d,x="annee",y="nb_creations",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,title="Creations par annee et secteur",
            labels={"annee":"Annee","nb_creations":"Nb entreprises","grand_secteur":"Secteur"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h",yanchor="bottom",y=1.02),hovermode="x unified")
        st.plotly_chart(fig,use_container_width=True)

    with tab2:
        d = df_naf[df_naf["grand_secteur"].isin(sects)].groupby("grand_secteur")["nb_entreprises"].sum().reset_index().sort_values("nb_entreprises",ascending=True)
        fig = px.bar(d,x="nb_entreprises",y="grand_secteur",orientation="h",
            color="grand_secteur",color_discrete_map=COLOR_MAP,
            title="Entreprises actives par secteur",text="nb_entreprises",
            labels={"grand_secteur":"Secteur","nb_entreprises":"Nb"})
        fig.update_traces(texttemplate="%{text:,.0f}",textposition="outside")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

    with tab3:
        ordre = ["Non employeur","0 salarie","1-2","3-5","6-9","10-19","20-49","50-99",
            "100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]
        d = df_taille[df_taille["grand_secteur"].isin(sects)].groupby("libelle_taille")["nb_entreprises"].sum().reset_index()
        d["ord"] = d["libelle_taille"].map({v:i for i,v in enumerate(ordre)}).fillna(99)
        d = d.sort_values("ord")
        fig = px.bar(d,x="libelle_taille",y="nb_entreprises",color_discrete_sequence=["#3498db"],
            title="Repartition par taille",labels={"libelle_taille":"Effectif","nb_entreprises":"Nb"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis=dict(tickangle=45))
        st.plotly_chart(fig,use_container_width=True)


if __name__ == "__main__":
    main()
