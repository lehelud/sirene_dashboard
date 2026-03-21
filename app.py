"""
app.py - Dashboard SIRENE
Lecture streaming par chunks pour eviter timeout Streamlit Cloud
Colonnes et types verifies dans les logs : categorieJuridiqueUniteLegale=int64
"""
import io
import warnings
from datetime import datetime

import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
import requests
import streamlit as st

warnings.filterwarnings("ignore")

URL_UL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"

# Types verifies dans les logs Streamlit
# categorieJuridiqueUniteLegale: int64 (pas string !)
# etatAdministratifUniteLegale: string
# activitePrincipaleUniteLegale: string
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

COLOR_MAP = {
    "Agriculture":"#2ecc71","Industrie":"#3498db","Construction":"#e67e22",
    "Commerce / Transport / HCR":"#9b59b6","Services aux entreprises":"#e74c3c",
    "Services publics / Sante":"#1abc9c","Autres":"#95a5a6",
}


@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    """
    Lecture par chunks avec pyarrow pour eviter le timeout.
    Le fichier parquet supporte la lecture colonnaire directe depuis URL.
    """
    prog = st.progress(0, "Telechargement SIRENE (~650 Mo)...")
    r = requests.get(URL_UL, timeout=300, stream=True)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    buf = io.BytesIO()
    downloaded = 0
    for chunk in r.iter_content(chunk_size=10*1024*1024):  # 10 Mo par chunk
        buf.write(chunk)
        downloaded += len(chunk)
        if total > 0:
            prog.progress(min(downloaded/total, 0.9), f"Telechargement... {downloaded//1024//1024} Mo / {total//1024//1024} Mo")
    prog.progress(0.92, "Lecture du fichier parquet...")
    buf.seek(0)
    # Lecture pyarrow avec colonnes specifiques
    table = pq.read_table(buf, columns=COLS_UL)
    prog.progress(0.96, "Traitement des donnees...")
    df = table.to_pandas()
    # categorieJuridiqueUniteLegale est int64 - exclure 7xxx et 9xxx
    df["cat_jur"] = df["categorieJuridiqueUniteLegale"].fillna(0).astype(int)
    # Secteur marchand = exclure associations (7000-7999) et administration (9000-9999)
    df = df[~df["cat_jur"].between(7000, 9999)]
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["grand_secteur"] = df["activitePrincipaleUniteLegale"].astype(str).str[0].str.upper().map(GRANDS_SECTEURS).fillna("Autres")
    now = datetime.now().year
    prog.progress(1.0, "Donnees chargees !")
    prog.empty()
    return df[df["annee"].between(2000, now) | df["annee"].isna()]


def afficher_sidebar(df):
    st.sidebar.title("Filtres")
    annees = sorted([int(a) for a in df["annee"].dropna().unique()])
    amin, amax = min(annees), max(annees)
    plage = st.sidebar.slider("Periode", amin, amax, (max(amin, amax-10), amax))
    secteurs = sorted(df["grand_secteur"].dropna().unique().tolist())
    sects = st.sidebar.multiselect("Secteurs", secteurs, default=secteurs)
    st.sidebar.caption("Source : Base SIRENE - data.gouv.fr")
    return {"amin":plage[0],"amax":plage[1],"secteurs":sects}


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : data.gouv.fr | Secteur marchand | Mise a jour mensuelle")

    with st.spinner("Chargement SIRENE (2-4 min au premier lancement)..."):
        df = charger_donnees()

    filtres = afficher_sidebar(df)
    mask = (df["annee"].between(filtres["amin"], filtres["amax"])
            & df["grand_secteur"].isin(filtres["secteurs"]))
    df_f = df[mask]
    ay = filtres["amax"]

    # KPIs
    ca = len(df_f[df_f["annee"]==ay])
    cp = len(df_f[df_f["annee"]==ay-1])
    delta = ((ca-cp)/cp*100) if cp else 0
    actives = len(df[df["etatAdministratifUniteLegale"]=="A"])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Entreprises (periode)", f"{len(df_f):,}".replace(",","."))
    c2.metric(f"Creees en {ay}", f"{ca:,}".replace(",","."), f"{delta:+.1f}% vs {ay-1}")
    c3.metric("Actives (total)", f"{actives:,}".replace(",","."))
    c4.metric("Secteurs", len(filtres["secteurs"]))
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Creations","Secteurs NAF","Taille","Top departements"])

    with tab1:
        d = df_f.groupby(["annee","grand_secteur"]).size().reset_index(name="nb")
        fig = px.bar(d,x="annee",y="nb",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,title="Creations par annee et secteur",
            labels={"annee":"Annee","nb":"Nb entreprises","grand_secteur":"Secteur"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h",yanchor="bottom",y=1.02),hovermode="x unified")
        st.plotly_chart(fig,use_container_width=True)

    with tab2:
        d = (df[df["etatAdministratifUniteLegale"]=="A"]
             .groupby("grand_secteur").size().reset_index(name="nb")
             .sort_values("nb",ascending=True))
        fig = px.bar(d,x="nb",y="grand_secteur",orientation="h",
            color="grand_secteur",color_discrete_map=COLOR_MAP,
            title="Entreprises actives par secteur",text="nb",
            labels={"grand_secteur":"Secteur","nb":"Nb"})
        fig.update_traces(texttemplate="%{text:,.0f}",textposition="outside")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

    with tab3:
        tranches = {"NN":"Non employeur","00":"0 salarie","01":"1-2","02":"3-5","03":"6-9",
            "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
            "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999","52":"5000+","53":"10000+"}
        ordre = list(tranches.values())+["Non renseigne"]
        d = df[df["etatAdministratifUniteLegale"]=="A"].copy()
        d["taille"] = d["trancheEffectifsUniteLegale"].astype(str).map(tranches).fillna("Non renseigne")
        d = d.groupby("taille").size().reset_index(name="nb")
        d["ord"] = d["taille"].map({v:i for i,v in enumerate(ordre)}).fillna(99)
        d = d.sort_values("ord")
        fig = px.bar(d,x="taille",y="nb",color_discrete_sequence=["#3498db"],
            title="Repartition par taille",labels={"taille":"Effectif","nb":"Nb"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=45))
        st.plotly_chart(fig,use_container_width=True)

    with tab4:
        d = df[df["etatAdministratifUniteLegale"]=="A"].copy()
        d["dept"] = d["siren"].astype(str).str[:2]
        d = d.groupby("dept").size().reset_index(name="nb").sort_values("nb",ascending=False).head(20)
        fig = px.bar(d,x="dept",y="nb",title="Top 20 departements (via SIREN)",
            labels={"dept":"Dept","nb":"Nb"},color_discrete_sequence=["#3498db"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)


if __name__ == "__main__":
    main()
