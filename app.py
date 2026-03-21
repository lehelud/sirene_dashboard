"""
app.py - Dashboard SIRENE : entreprises du secteur marchand
"""

import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from auth import verifier_authentification
from naf_comparaison import afficher_onglet_naf

warnings.filterwarnings("ignore")

DATA_DIR = Path("data")

COLOR_MAP = {
    "Agriculture": "#2ecc71",
    "Industrie": "#3498db",
    "Construction": "#e67e22",
    "Commerce / Transport / HCR": "#9b59b6",
    "Services aux entreprises": "#e74c3c",
    "Services publics / Sante": "#1abc9c",
    "Autres": "#95a5a6",
}

ORDRE_TAILLE = [
    "Non employeur", "0 salarie", "1-2 salaries", "3-5 salaries",
    "6-9 salaries", "10-19 salaries", "20-49 salaries", "50-99 salaries",
    "100-199 salaries", "200-249 salaries", "250-499 salaries",
    "500-999 salaries", "1 000-1 999 salaries", "2 000-4 999 salaries",
    "5 000-9 999 salaries", "10 000 salaries et plus", "Non renseigne",
]


@st.cache_data(show_spinner="Chargement des donnees...")
def charger_toutes_donnees():
    fichiers = [
        "creations_annee.parquet", "cessations_mois.parquet",
        "repartition_naf.parquet", "repartition_taille.parquet", "carte_commune.parquet",
    ]
    manquants = [f for f in fichiers if not (DATA_DIR / f).exists()]
    if manquants:
        return None, manquants
    return {
        "creations": pd.read_parquet(DATA_DIR / "creations_annee.parquet"),
        "cessations": pd.read_parquet(DATA_DIR / "cessations_mois.parquet"),
        "naf": pd.read_parquet(DATA_DIR / "repartition_naf.parquet"),
        "taille": pd.read_parquet(DATA_DIR / "repartition_taille.parquet"),
        "carte": pd.read_parquet(DATA_DIR / "carte_commune.parquet"),
    }, []


@st.cache_data(show_spinner="Chargement des communes...")
def charger_communes():
    url = "https://geo.api.gouv.fr/communes?fields=code,nom,codeDepartement,codeRegion,centre&format=json&geometry=centre"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        rows = []
        for c in data:
            coords = c.get("centre", {}).get("coordinates", [None, None])
            rows.append({"code_commune": c["code"], "nom_commune": c["nom"],
                         "code_departement": c.get("codeDepartement", ""),
                         "code_region": c.get("codeRegion", ""),
                         "lon": coords[0], "lat": coords[1]})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def afficher_sidebar(data: dict) -> dict:
    st.sidebar.title("Filtres")
    df_c = data["creations"]
    annees = sorted(df_c["annee"].dropna().unique().tolist())
    secteurs = sorted(df_c["grand_secteur"].dropna().unique().tolist())
    annee_min, annee_max = int(min(annees)), int(max(annees))
    plage_annee = st.sidebar.slider("Periode de creation", min_value=annee_min,
        max_value=annee_max, value=(max(annee_min, annee_max - 10), annee_max))
    secteurs_choisis = st.sidebar.multiselect("Grands secteurs", options=secteurs, default=secteurs)
    formes = sorted(df_c["categorie_juridique"].dropna().unique().tolist())
    formes_choisies = st.sidebar.multiselect("Categorie juridique", options=formes,
        default=formes[:10] if len(formes) > 10 else formes)
    df_communes = charger_communes()
    if not df_communes.empty:
        depts = sorted(df_communes["code_departement"].dropna().unique().tolist())
        depts_choisis = st.sidebar.multiselect("Departements (carte)", options=depts,
            default=[], placeholder="Tous les departements")
    else:
        depts_choisis = []
    st.sidebar.markdown("---")
    st.sidebar.caption("Donnees : Base SIRENE - data.gouv.fr")
    return {"annee_min": plage_annee[0], "annee_max": plage_annee[1],
            "secteurs": secteurs_choisis, "formes": formes_choisies, "depts": depts_choisis}


def afficher_kpis(data: dict, filtres: dict):
    df_c = data["creations"]
    df_cess = data["cessations"]
    mask_c = (df_c["annee"].between(filtres["annee_min"], filtres["annee_max"])
              & df_c["grand_secteur"].isin(filtres["secteurs"]))
    total_creations = int(df_c[mask_c]["nb_creations"].sum())
    annee_max = filtres["annee_max"]
    creations_an = int(df_c[(df_c["annee"] == annee_max) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    creations_an_prec = int(df_c[(df_c["annee"] == annee_max - 1) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    delta_pct = ((creations_an - creations_an_prec) / creations_an_prec * 100) if creations_an_prec else 0
    total_cess = int(df_cess[df_cess["grand_secteur"].isin(filtres["secteurs"])]["nb_cessations"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Creations (periode)", f"{total_creations:,}".replace(",", " "))
    c2.metric(f"Creations {annee_max}", f"{creations_an:,}".replace(",", " "), f"{delta_pct:+.1f}% vs {annee_max-1}")
    c3.metric("Cessations totales", f"{total_cess:,}".replace(",", " "))
    c4.metric("Secteurs suivis", len(filtres["secteurs"]))


def plot_creations_annee(data: dict, filtres: dict):
    df = data["creations"]
    mask = (df["annee"].between(filtres["annee_min"], filtres["annee_max"])
            & df["grand_secteur"].isin(filtres["secteurs"]))
    df_f = df[mask].groupby(["annee", "grand_secteur"])["nb_creations"].sum().reset_index()
    fig = px.bar(df_f, x="annee", y="nb_creations", color="grand_secteur",
        color_discrete_map=COLOR_MAP,
        title="Creations d'entreprises par annee et grand secteur",
        labels={"annee": "Annee", "nb_creations": "Nb creations", "grand_secteur": "Secteur"},
        barmode="stack")

    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02), hovermode="x unified")
    fig.update_traces(hovertemplate="%{fullData.name} : %{y:,.0f}<extra></extra>")
    return fig


def plot_cessations_mois(data: dict, filtres: dict):
    df = data["cessations"]
    df_f = df[df["grand_secteur"].isin(filtres["secteurs"])].copy()
    df_f = df_f.groupby(["annee_mois", "grand_secteur"])["nb_cessations"].sum().reset_index()
    df_f = df_f.sort_values("annee_mois")
    annees_recentes = sorted(df_f["annee_mois"].unique())[-60:]
    df_f = df_f[df_f["annee_mois"].isin(annees_recentes)]
    fig = px.line(df_f, x="annee_mois", y="nb_cessations", color="grand_secteur",
        color_discrete_map=COLOR_MAP, title="Cessations d'entreprises par mois et grand secteur",
        labels={"annee_mois": "Mois", "nb_cessations": "Nb cessations", "grand_secteur": "Secteur"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified", xaxis=dict(tickangle=45))
    return fig


def plot_repartition_naf(data: dict, filtres: dict):
    df = data["naf"]
    df_f = df[df["grand_secteur"].isin(filtres["secteurs"])].copy()
    df_f = df_f.groupby("grand_secteur")["nb_entreprises"].sum().reset_index().sort_values("nb_entreprises", ascending=True)
    fig = px.bar(df_f, x="nb_entreprises", y="grand_secteur", orientation="h",
        color="grand_secteur", color_discrete_map=COLOR_MAP,
        title="Repartition des entreprises actives par grand secteur",
        labels={"grand_secteur": "Secteur", "nb_entreprises": "Nb entreprises"}, text="nb_entreprises")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} entreprises<extra></extra>")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, xaxis=dict(showgrid=False))
    return fig


def plot_repartition_taille(data: dict, filtres: dict):
    df = data["taille"]
    df_f = df[df["grand_secteur"].isin(filtres["secteurs"])].copy()
    df_f = df_f.groupby("libelle_taille")["nb_entreprises"].sum().reset_index()
    df_f["ordre"] = df_f["libelle_taille"].map({v: i for i, v in enumerate(ORDRE_TAILLE)}).fillna(99)
    df_f = df_f.sort_values("ordre")
    fig = px.bar(df_f, x="libelle_taille", y="nb_entreprises",
        color_discrete_sequence=["#3498db"],
        title="Repartition des entreprises actives par taille (effectif)",
        labels={"libelle_taille": "Tranche d'effectif", "nb_entreprises": "Nb entreprises"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=45, showgrid=False), yaxis=dict(showgrid=False))
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,.0f} entreprises<extra></extra>")
    return fig


def plot_carte(data: dict, filtres: dict):
    df_carte = data["carte"]
    df_communes = charger_communes()
    if df_communes.empty:
        st.warning("Referentiel communes non disponible.")
        return None
    if filtres["depts"]:
        communes_depts = df_communes[df_communes["code_departement"].isin(filtres["depts"])]["code_commune"].tolist()
        df_carte = df_carte[df_carte["code_commune"].isin(communes_depts)]
    df_total = df_carte[df_carte["grand_secteur"] == "Tous secteurs"].copy()
    df_total = df_total.merge(df_communes[["code_commune","nom_commune","code_departement","lat","lon"]],
        on="code_commune", how="left").dropna(subset=["lat","lon"])
    fig = px.scatter_mapbox(df_total, lat="lat", lon="lon", size="nb_etablissements",
        color="nb_etablissements", hover_name="nom_commune",
        hover_data={"nb_etablissements": True, "code_departement": True, "lat": False, "lon": False},
        color_continuous_scale="Viridis", size_max=25, zoom=4.8,
        center={"lat": 46.5, "lon": 2.5}, title="Etablissements actifs par commune",
        labels={"nb_etablissements": "Nb etablissements"})
    fig.update_layout(mapbox_style="carto-positron", margin=dict(l=0,r=0,t=40,b=0), height=600)
    return fig


def page_donnees_manquantes(manquants: list):
    st.error("Donnees non preparees")
    st.markdown("Fichiers manquants dans ./data/ :\n" + "\n".join(f"- {f}" for f in manquants))
    st.info("Lance d'abord : python prep_data.py")


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    verifier_authentification()
    result, manquants = charger_toutes_donnees()
    if result is None:
        page_donnees_manquantes(manquants)
        return
    data = result
    filtres = afficher_sidebar(data)
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : Base SIRENE, data.gouv.fr - Secteur marchand uniquement")
    st.divider()
    afficher_kpis(data, filtres)
    st.divider()
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Creations", "Cessations", "Secteurs NAF", "Taille", "Carte", "NAF 2008 -> 2025"])
    with tab1:
        st.plotly_chart(plot_creations_annee(data, filtres), use_container_width=True)
    with tab2:
        st.plotly_chart(plot_cessations_mois(data, filtres), use_container_width=True)
    with tab3:
        st.plotly_chart(plot_repartition_naf(data, filtres), use_container_width=True)
    with tab4:
        st.plotly_chart(plot_repartition_taille(data, filtres), use_container_width=True)
    with tab5:
        fig_carte = plot_carte(data, filtres)
        if fig_carte:
            st.plotly_chart(fig_carte, use_container_width=True)
    with tab6:
        afficher_onglet_naf(data["naf"])


if __name__ == "__main__":
    main()
