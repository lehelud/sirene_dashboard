"""
app.py - Dashboard SIRENE
URLs parquet directes depuis data.gouv.fr
"""

import io
import warnings
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

warnings.filterwarnings("ignore")

# URLs correctes des fichiers parquet SIRENE (data.gouv.fr)
URL_UL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet"

COLS_UL = [
    "siren", "dateCreationUniteLegale", "dateCessationUniteLegale",
    "activitePrincipaleUniteLegale", "categorieJuridiqueUniteLegale",
    "trancheEffectifsUniteLegale", "etatAdministratifUniteLegale",
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


def secteur(naf):
    return pd.Series(naf).astype(str).str[0].str.upper().map(GRANDS_SECTEURS).fillna("Autres")


@st.cache_data(ttl=86_400, show_spinner="Telechargement donnees SIRENE (2-5 min)...")
def charger_donnees():
    r = requests.get(URL_UL, timeout=300, stream=True)
    r.raise_for_status()
    buf = io.BytesIO(r.content)
    df = pd.read_parquet(buf, columns=COLS_UL)
    df = df[~df["categorieJuridiqueUniteLegale"].astype(str).str[:1].isin(["7","9"])]
    df["dateCreation"] = pd.to_datetime(df["dateCreationUniteLegale"], errors="coerce")
    df["dateCessation"] = pd.to_datetime(df["dateCessationUniteLegale"], errors="coerce")
    df["grand_secteur"] = secteur(df["activitePrincipaleUniteLegale"])
    df["annee"] = df["dateCreation"].dt.year.astype("Int64")
    df["annee_mois_cess"] = df["dateCessation"].dt.to_period("M").astype(str)
    now = datetime.now().year
    return df[df["annee"].between(2010, now) | df["annee"].isna()]


@st.cache_data(ttl=86_400)
def charger_communes():
    url = "https://geo.api.gouv.fr/communes?fields=code,nom,codeDepartement,centre&format=json&geometry=centre"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        rows = [{
            "code_commune": c["code"], "nom_commune": c["nom"],
            "code_departement": c.get("codeDepartement", ""),
            "lon": c.get("centre", {}).get("coordinates", [None, None])[0],
            "lat": c.get("centre", {}).get("coordinates", [None, None])[1]
        } for c in r.json()]
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()


def agreger_creations(df):
    now = datetime.now().year
    d = df[df["annee"].between(2014, now)]
    return d.groupby(
        ["annee", "grand_secteur", "categorieJuridiqueUniteLegale", "trancheEffectifsUniteLegale"],
        dropna=False
    ).size().reset_index(name="nb_creations").rename(columns={
        "categorieJuridiqueUniteLegale": "categorie_juridique",
        "trancheEffectifsUniteLegale": "tranche_effectifs"
    })


def agreger_cessations(df):
    d = df[df["dateCessation"].notna()].copy()
    d = d.groupby(["annee_mois_cess", "grand_secteur"]).size().reset_index(name="nb_cessations")
    d = d.rename(columns={"annee_mois_cess": "annee_mois"})
    return d.sort_values("annee_mois")


def agreger_naf(df):
    d = df[df["etatAdministratifUniteLegale"] == "A"].copy()
    return d.groupby(["activitePrincipaleUniteLegale", "grand_secteur"]).size().reset_index(name="nb_entreprises")


def agreger_taille(df):
    tranches = {
        "NN":"Non employeur","00":"0 salarie","01":"1-2","02":"3-5","03":"6-9",
        "11":"10-19","12":"20-49","21":"50-99","22":"100-199","31":"200-249",
        "32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999",
        "52":"5000-9999","53":"10000+"
    }
    d = df[df["etatAdministratifUniteLegale"] == "A"].copy()
    d["libelle_taille"] = d["trancheEffectifsUniteLegale"].astype(str).map(tranches).fillna("Non renseigne")
    return d.groupby(["libelle_taille", "grand_secteur"]).size().reset_index(name="nb_entreprises")


def afficher_sidebar(df_creations):
    st.sidebar.title("Filtres")
    annees = sorted(df_creations["annee"].dropna().unique().tolist())
    secteurs = sorted(df_creations["grand_secteur"].dropna().unique().tolist())
    amin, amax = int(min(annees)), int(max(annees))
    plage = st.sidebar.slider("Periode", amin, amax, (max(amin, amax - 5), amax))
    sects = st.sidebar.multiselect("Secteurs", secteurs, default=secteurs)
    formes = sorted(df_creations["categorie_juridique"].dropna().unique().tolist())
    formes_c = st.sidebar.multiselect("Categorie juridique", formes,
        default=formes[:10] if len(formes) > 10 else formes)
    st.sidebar.caption("Source : Base SIRENE - data.gouv.fr")
    return {"amin": plage[0], "amax": plage[1], "secteurs": sects, "formes": formes_c}


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : data.gouv.fr | Secteur marchand uniquement | Mise a jour quotidienne")

    with st.spinner("Chargement des donnees SIRENE (2-5 min au premier lancement)..."):
        df = charger_donnees()

    df_c = agreger_creations(df)
    df_cess = agreger_cessations(df)
    df_naf = agreger_naf(df)
    df_taille = agreger_taille(df)
    filtres = afficher_sidebar(df_c)

    # KPIs
    mask = (df_c["annee"].between(filtres["amin"], filtres["amax"]) &
            df_c["grand_secteur"].isin(filtres["secteurs"]))
    ay = filtres["amax"]
    total = int(df_c[mask]["nb_creations"].sum())
    ca = int(df_c[(df_c["annee"] == ay) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    cp = int(df_c[(df_c["annee"] == ay-1) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    delta = ((ca - cp) / cp * 100) if cp else 0
    tc = int(df_cess[df_cess["grand_secteur"].isin(filtres["secteurs"])]["nb_cessations"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Creations (periode)", f"{total:,}".replace(",", "."))
    c2.metric(f"Creations {ay}", f"{ca:,}".replace(",", "."), f"{delta:+.1f}% vs {ay-1}")
    c3.metric("Cessations totales", f"{tc:,}".replace(",", "."))
    c4.metric("Secteurs suivis", len(filtres["secteurs"]))
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Creations", "Cessations", "Secteurs NAF", "Taille"])

    with tab1:
        d = df_c[mask].groupby(["annee", "grand_secteur"])["nb_creations"].sum().reset_index()
        fig = px.bar(d, x="annee", y="nb_creations", color="grand_secteur",
            color_discrete_map=COLOR_MAP, title="Creations par annee et secteur",
            barmode="stack", labels={"annee":"Annee","nb_creations":"Nb creations","grand_secteur":"Secteur"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        d = df_cess[df_cess["grand_secteur"].isin(filtres["secteurs"])].copy()
        d = d[d["annee_mois"].isin(sorted(d["annee_mois"].unique())[-60:])]
        fig = px.line(d, x="annee_mois", y="nb_cessations", color="grand_secteur",
            color_discrete_map=COLOR_MAP, title="Cessations mensuelles (5 dernières années)",
            labels={"annee_mois":"Mois","nb_cessations":"Nb cessations","grand_secteur":"Secteur"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            hovermode="x unified", xaxis=dict(tickangle=45))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        d = df_naf[df_naf["grand_secteur"].isin(filtres["secteurs"])].groupby(
            "grand_secteur")["nb_entreprises"].sum().reset_index().sort_values("nb_entreprises", ascending=True)
        fig = px.bar(d, x="nb_entreprises", y="grand_secteur", orientation="h",
            color="grand_secteur", color_discrete_map=COLOR_MAP,
            title="Entreprises actives par secteur", text="nb_entreprises",
            labels={"grand_secteur":"Secteur","nb_entreprises":"Nb entreprises"})
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        ordre = ["Non employeur","0 salarie","1-2","3-5","6-9","10-19","20-49",
            "50-99","100-199","200-249","250-499","500-999","1000-1999",
            "2000-4999","5000-9999","10000+","Non renseigne"]
        d = df_taille[df_taille["grand_secteur"].isin(filtres["secteurs"])].groupby(
            "libelle_taille")["nb_entreprises"].sum().reset_index()
        d["ordre"] = d["libelle_taille"].map({v: i for i, v in enumerate(ordre)}).fillna(99)
        d = d.sort_values("ordre")
        fig = px.bar(d, x="libelle_taille", y="nb_entreprises",
            color_discrete_sequence=["#3498db"], title="Repartition par taille d'effectif",
            labels={"libelle_taille":"Effectif","nb_entreprises":"Nb entreprises"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=45))
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
