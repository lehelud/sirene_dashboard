"""
app.py - Dashboard SIRENE
Colonnes verifiees sur data.gouv.fr - StockUniteLegale Mars 2026
"""
import io
import warnings
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

warnings.filterwarnings("ignore")

# URL directe du parquet unites legales (verifie sur data.gouv.fr)
URL_UL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"

# Colonnes exactes du fichier StockUniteLegale (verifiees)
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


@st.cache_data(ttl=86_400, show_spinner="Telechargement SIRENE (~2 min)...")
def charger_donnees():
    st.write("Telechargement unites legales (~650 Mo)...")
    r = requests.get(URL_UL, timeout=300)
    r.raise_for_status()
    st.write("Lecture du fichier parquet...")
    df = pd.read_parquet(io.BytesIO(r.content), columns=COLS_UL)
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["grand_secteur"] = df["activitePrincipaleUniteLegale"].astype(str).str[0].str.upper().map(GRANDS_SECTEURS).fillna("Autres")
    # Filtrer secteur marchand (exclut cat juridiques 7xxx et 9xxx = asso/admin)
    df = df[~df["categorieJuridiqueUniteLegale"].astype(str).str[:1].isin(["7","9"])]
    now = datetime.now().year
    return df[df["annee"].between(2000, now) | df["annee"].isna()]


@st.cache_data(ttl=86_400)
def charger_communes():
    url = "https://geo.api.gouv.fr/communes?fields=code,nom,codeDepartement,centre&format=json&geometry=centre"
    try:
        r = requests.get(url, timeout=30); r.raise_for_status()
        rows = [{"code":c["code"],"nom":c["nom"],"dept":c.get("codeDepartement",""),
                 "lon":c.get("centre",{}).get("coordinates",[None,None])[0],
                 "lat":c.get("centre",{}).get("coordinates",[None,None])[1]} for c in r.json()]
        return pd.DataFrame(rows)
    except: return pd.DataFrame()


def afficher_sidebar(df):
    st.sidebar.title("Filtres")
    annees = sorted(df["annee"].dropna().unique().tolist())
    amin, amax = int(min(annees)), int(max(annees))
    plage = st.sidebar.slider("Periode", amin, amax, (max(amin, amax-10), amax))
    secteurs = sorted(df["grand_secteur"].dropna().unique().tolist())
    sects = st.sidebar.multiselect("Secteurs", secteurs, default=secteurs)
    formes = sorted(df["categorieJuridiqueUniteLegale"].dropna().astype(str).unique().tolist())
    formes_c = st.sidebar.multiselect("Cat. juridique", formes,
        default=formes[:10] if len(formes)>10 else formes)
    st.sidebar.caption("Source : Base SIRENE - data.gouv.fr")
    return {"amin":plage[0],"amax":plage[1],"secteurs":sects,"formes":formes_c}


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : data.gouv.fr | Mise a jour mensuelle | Secteur marchand uniquement")

    with st.spinner("Chargement des donnees SIRENE (2-3 min au premier lancement)..."):
        df = charger_donnees()

    filtres = afficher_sidebar(df)
    mask = (df["annee"].between(filtres["amin"],filtres["amax"])
            & df["grand_secteur"].isin(filtres["secteurs"])
            & df["categorieJuridiqueUniteLegale"].astype(str).isin(filtres["formes"]))
    df_f = df[mask]
    ay = filtres["amax"]

    # KPIs
    total = len(df_f)
    ca = len(df_f[df_f["annee"]==ay])
    cp = len(df_f[df_f["annee"]==ay-1])
    delta = ((ca-cp)/cp*100) if cp else 0
    actives = len(df[df["etatAdministratifUniteLegale"]=="A"])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Entreprises (periode)", f"{total:,}".replace(",","."))
    c2.metric(f"Creees en {ay}", f"{ca:,}".replace(",","."), f"{delta:+.1f}% vs {ay-1}")
    c3.metric("Actives (total)", f"{actives:,}".replace(",","."))
    c4.metric("Secteurs suivis", len(filtres["secteurs"]))
    st.divider()

    tab1,tab2,tab3,tab4 = st.tabs(["Creations","Secteurs NAF","Taille","Carte"])

    with tab1:
        d = df_f.groupby(["annee","grand_secteur"]).size().reset_index(name="nb")
        fig = px.bar(d,x="annee",y="nb",color="grand_secteur",
            color_discrete_map=COLOR_MAP,title="Creations par annee et secteur",barmode="stack",
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
            labels={"grand_secteur":"Secteur","nb":"Nb entreprises"})
        fig.update_traces(texttemplate="%{text:,.0f}",textposition="outside")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

    with tab3:
        tranches = {"NN":"Non employeur","00":"0 salarie","01":"1-2","02":"3-5","03":"6-9",
            "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
            "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999","52":"5000-9999","53":"10000+"}
        ordre = list(tranches.values()) + ["Non renseigne"]
        d = df[df["etatAdministratifUniteLegale"]=="A"].copy()
        d["taille"] = d["trancheEffectifsUniteLegale"].astype(str).map(tranches).fillna("Non renseigne")
        d = d.groupby("taille").size().reset_index(name="nb")
        d["ord"] = d["taille"].map({v:i for i,v in enumerate(ordre)}).fillna(99)
        d = d.sort_values("ord")
        fig = px.bar(d,x="taille",y="nb",color_discrete_sequence=["#3498db"],
            title="Repartition par taille (entreprises actives)",
            labels={"taille":"Effectif","nb":"Nb entreprises"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=45))
        st.plotly_chart(fig,use_container_width=True)

    with tab4:
        st.info("La carte par commune necessite le fichier etablissements (2 Go). Disponible dans une prochaine version.")
        # Vue alternative : top departements par siren (3 premiers chiffres)
        d = df[df["etatAdministratifUniteLegale"]=="A"].copy()
        d["dept_approx"] = d["siren"].astype(str).str[:2]
        d = d.groupby("dept_approx").size().reset_index(name="nb").sort_values("nb",ascending=False).head(20)
        fig = px.bar(d,x="dept_approx",y="nb",title="Top 20 departements (approximation via SIREN)",
            labels={"dept_approx":"Departement","nb":"Nb entreprises"},
            color_discrete_sequence=["#3498db"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)


if __name__ == "__main__":
    main()
