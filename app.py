"""
app.py - Dashboard SIRENE
- Treemap etat des entreprises
- Onglet comparaison NAF 2008 -> NAF 2025
- Sans auth, sans geopandas
"""
import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

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

COULEURS_CHANGEMENT = {
    "Identique": "#2ecc71",
    "Recode": "#f39c12",
    "Fusion": "#e74c3c",
    "Division": "#3498db",
}

# Correspondance NAF 2008 -> 2025 par division (2 chiffres)
NAF_CHANGEMENTS = [
    ("01","Culture et prod. animale","01","Production agricole","Recode"),
    ("02","Sylviculture","02","Sylviculture","Identique"),
    ("03","Peche, aquaculture","03","Peche, aquaculture","Identique"),
    ("10","Industries alimentaires","10","Industries alimentaires","Identique"),
    ("14","Fab. articles habill.","14","Articles habillement","Identique"),
    ("26","Fab. produits electroniques","26","Electronique","Recode"),
    ("41","Construction batiments","41","Construction batiments","Identique"),
    ("42","Genie civil","42","Genie civil","Identique"),
    ("43","Travaux specialises","43","Travaux specialises","Identique"),
    ("45","Commerce et rep. auto","45","Commerce auto","Identique"),
    ("46","Commerce gros","46","Commerce gros","Identique"),
    ("47","Commerce detail","47","Commerce detail","Identique"),
    ("49","Transports terrestres","49","Transports terrestres","Identique"),
    ("55","Hebergement","55","Hebergement","Identique"),
    ("56","Restauration","56","Restauration","Identique"),
    ("58","Edition","58","Edition","Identique"),
    ("62","Programmation, conseil IT","62","Act. informatiques","Recode"),
    ("63","Services information","62","Act. informatiques","Fusion"),
    ("64","Act. financieres","64","Act. financieres","Identique"),
    ("65","Assurance","65","Assurance","Identique"),
    ("68","Act. immobilieres","68","Act. immobilieres","Identique"),
    ("69","Juridique, comptabilite","69","Juridique, compta","Identique"),
    ("70","Conseil gestion","70","Conseil gestion","Identique"),
    ("71","Architecture, ingenierie","71","Architecture","Identique"),
    ("72","R&D","72","R&D","Identique"),
    ("73","Publicite","73","Publicite","Identique"),
    ("74","Autres act. specialisees","74","Autres spec.","Recode"),
    ("75","Veterinaire","75","Veterinaire","Identique"),
    ("77","Location","77","Location","Identique"),
    ("78","Emploi","78","Emploi","Identique"),
    ("79","Voyage, tourisme","79","Voyage, tourisme","Identique"),
    ("80","Securite","80","Securite","Identique"),
    ("81","Services batiments","81","Services batiments","Identique"),
    ("82","Services administratifs","82","Services admin.","Recode"),
    ("84","Admin. publique","84","Admin. publique","Identique"),
    ("85","Enseignement","85","Enseignement","Identique"),
    ("86","Act. sante humaine","86","Sante humaine","Recode"),
    ("87","Hebergement medico-social","87","Hebergement medico","Identique"),
    ("88","Action sociale","88","Action sociale","Identique"),
    ("90","Arts, spectacles","90","Arts, spectacles","Identique"),
    ("93","Sports, loisirs","93","Sports, loisirs","Identique"),
    ("95","Reparation","95","Reparation","Identique"),
    ("96","Autres services perso","96","Services perso","Identique"),
]


@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    fichiers = {
        "creations": DATA_DIR / "creations_annee.parquet",
        "naf": DATA_DIR / "repartition_naf.parquet",
        "taille": DATA_DIR / "repartition_taille.parquet",
        "cessations": DATA_DIR / "cessations_mois.parquet",
    }
    manquants = [n for n, p in fichiers.items() if not p.exists()]
    if manquants:
        return None, manquants
    return {k: pd.read_parquet(v) for k, v in fichiers.items()}, []


def afficher_sidebar(data):
    st.sidebar.title("Filtres")
    df_c = data["creations"]
    annees = sorted(df_c["annee"].dropna().unique().tolist())
    amin, amax = int(min(annees)), int(max(annees))
    plage = st.sidebar.slider("Periode", amin, amax, (max(amin, amax - 10), amax))
    secteurs = sorted(df_c["grand_secteur"].dropna().unique().tolist())
    sects = st.sidebar.multiselect("Secteurs", secteurs, default=secteurs)
    st.sidebar.caption("Source : Base SIRENE - data.gouv.fr")
    return {"amin": plage[0], "amax": plage[1], "secteurs": sects}


def onglet_creations(data, filtres):
    df_c = data["creations"]
    mask = (df_c["annee"].between(filtres["amin"], filtres["amax"])
            & df_c["grand_secteur"].isin(filtres["secteurs"]))
    d = df_c[mask].groupby(["annee", "grand_secteur"])["nb_creations"].sum().reset_index()
    fig = px.bar(d, x="annee", y="nb_creations", color="grand_secteur",
                 barmode="stack", color_discrete_map=COLOR_MAP,
                 title="Creations par annee et secteur",
                 labels={"annee": "Annee", "nb_creations": "Nb", "grand_secteur": "Secteur"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

def onglet_etat_entreprises(data, filtres):
    st.subheader("Etat actuel des entreprises")
    st.caption("Treemap : surface proportionnelle au nombre d'entreprises actives")
    df_naf = data["naf"]
    df_taille = data["taille"]
    d = df_naf[df_naf["grand_secteur"].isin(filtres["secteurs"])].copy()
    d["pct"] = (d["nb_entreprises"] / d["nb_entreprises"].sum() * 100).round(1)
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.treemap(
            d, path=["grand_secteur"], values="nb_entreprises",
            color="grand_secteur", color_discrete_map=COLOR_MAP,
            title="Entreprises actives par secteur (treemap)",
            custom_data=["pct"],
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]:.1f}%",
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} entreprises<br>%{customdata[0]:.1f}%<extra></extra>",
            textfont_size=13,
        )
        fig.update_layout(margin=dict(t=50,l=5,r=5,b=5), height=450, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**Entreprises actives**")
        for _, row in d.sort_values("nb_entreprises", ascending=False).iterrows():
            color = COLOR_MAP.get(row["grand_secteur"], "#95a5a6")
            st.markdown(
                f"<div style='display:flex;align-items:center;margin:4px 0'>"
                f"<div style='width:12px;height:12px;background:{color};border-radius:2px;margin-right:8px;flex-shrink:0'></div>"
                f"<div style='font-size:0.85rem'><b>{row['grand_secteur']}</b><br>"
                f"{row['nb_entreprises']:,.0f} ({row['pct']:.1f}%)</div></div>",
                unsafe_allow_html=True,
            )
    st.divider()
    st.subheader("Repartition par taille (entreprises actives)")
    ordre = ["Non employeur","0 salarie","1-2","3-5","6-9","10-19","20-49","50-99",
             "100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]
    df_t = data["taille"][data["taille"]["grand_secteur"].isin(filtres["secteurs"])].copy()
    df_t = df_t.groupby("libelle_taille")["nb_entreprises"].sum().reset_index()
    df_t["ord"] = df_t["libelle_taille"].map({v: i for i, v in enumerate(ordre)}).fillna(99)
    df_t = df_t.sort_values("ord")
    fig2 = px.treemap(
        df_t, path=["libelle_taille"], values="nb_entreprises",
        color="nb_entreprises", color_continuous_scale="Blues",
        title="Repartition par taille d'effectif",
    )
    fig2.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,.0f}",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
        textfont_size=12,
    )
    fig2.update_layout(margin=dict(t=50,l=5,r=5,b=5), height=400, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)


def onglet_secteurs(data, filtres):
    d = (data["naf"][data["naf"]["grand_secteur"].isin(filtres["secteurs"])]
         .groupby("grand_secteur")["nb_entreprises"].sum().reset_index()
         .sort_values("nb_entreprises", ascending=True))
    fig = px.bar(d, x="nb_entreprises", y="grand_secteur", orientation="h",
                 color="grand_secteur", color_discrete_map=COLOR_MAP,
                 title="Entreprises actives par secteur", text="nb_entreprises",
                 labels={"grand_secteur":"Secteur","nb_entreprises":"Nb"})
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def onglet_taille(data, filtres):
    ordre = ["Non employeur","0 salarie","1-2","3-5","6-9","10-19","20-49","50-99",
             "100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]
    df_t = data["taille"][data["taille"]["grand_secteur"].isin(filtres["secteurs"])].copy()
    d = df_t.groupby("libelle_taille")["nb_entreprises"].sum().reset_index()
    d["ord"] = d["libelle_taille"].map({v: i for i, v in enumerate(ordre)}).fillna(99)
    d = d.sort_values("ord")
    fig = px.bar(d, x="libelle_taille", y="nb_entreprises",
                 color_discrete_sequence=["#3498db"], title="Repartition par taille",
                 labels={"libelle_taille":"Effectif","nb_entreprises":"Nb"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickangle=45))
    st.plotly_chart(fig, use_container_width=True)


def onglet_naf_comparaison(data):
    st.subheader("Comparaison NAF 2008 -> NAF 2025")
    st.caption("La NAF 2025 remplace la NAF rev.2 (2008) au 1er janvier 2027. Principaux changements par division (2 chiffres).")
    df_ch = pd.DataFrame(NAF_CHANGEMENTS, columns=["div_2008","lib_2008","div_2025","lib_2025","type"])
    total = len(df_ch)
    identiques = len(df_ch[df_ch["type"]=="Identique"])
    recodes = len(df_ch[df_ch["type"]=="Recode"])
    fusions = len(df_ch[df_ch["type"]=="Fusion"])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Divisions analysees", total)
    c2.metric("Identiques", identiques, f"{identiques/total*100:.0f}%")
    c3.metric("Recodes", recodes, f"{recodes/total*100:.0f}%")
    c4.metric("Fusions", fusions)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        d_types = df_ch.groupby("type").size().reset_index(name="nb")
        fig = px.treemap(d_types, path=["type"], values="nb",
                         color="type", color_discrete_map=COULEURS_CHANGEMENT,
                         title="Types de changement NAF 2008 -> 2025")
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value} divisions", textfont_size=13)
        fig.update_layout(margin=dict(t=50,l=5,r=5,b=5), height=350, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        d_bar = df_ch.groupby("type").size().reset_index(name="nb")
        fig2 = px.bar(d_bar, x="type", y="nb", color="type",
                      color_discrete_map=COULEURS_CHANGEMENT,
                      title="Nb divisions par type", text="nb",
                      labels={"type":"Type","nb":"Nb divisions"})
        fig2.update_traces(textposition="outside")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           showlegend=False, height=350, xaxis=dict(tickangle=20))
        st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    st.subheader("Detail des changements par division")
    filtre_type = st.multiselect("Filtrer par type", df_ch["type"].unique().tolist(),
                                  default=df_ch["type"].unique().tolist())
    recherche = st.text_input("Rechercher (code ou libelle)", placeholder="Ex: 62, informatique...")
    df_aff = df_ch[df_ch["type"].isin(filtre_type)].copy()
    if recherche:
        mask = (df_aff["div_2008"].str.contains(recherche, case=False, na=False)
                | df_aff["lib_2008"].str.contains(recherche, case=False, na=False)
                | df_aff["lib_2025"].str.contains(recherche, case=False, na=False))
        df_aff = df_aff[mask]
    df_aff.columns = ["Div. 2008","Libelle 2008","Div. 2025","Libelle 2025","Type"]
    st.dataframe(
        df_aff.style.map(lambda v: f"background-color:{COULEURS_CHANGEMENT.get(v,'#95a5a6')}33;font-weight:bold", subset=["Type"]),
        use_container_width=True, height=400,
    )
    st.caption(f"{len(df_aff)} divisions affichees")
    with st.expander("Legende"):
        desc = {"Identique":"Code et perimetre inchanges","Recode":"Libelle ou code modifie",
                "Fusion":"Plusieurs divisions 2008 -> une seule 2025","Division":"Une division 2008 -> plusieurs 2025"}
        for t, c in COULEURS_CHANGEMENT.items():
            st.markdown(f"<span style='color:{c};font-weight:bold'>&#9632; {t}</span> : {desc.get(t,'')}", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Dashboard SIRENE", page_icon="", layout="wide")
    st.title("Entreprises du secteur marchand - Base SIRENE")
    st.caption("Source : data.gouv.fr | Secteur marchand | Mise a jour mensuelle")
    data, manquants = charger_donnees()
    if data is None:
        st.error(f"Fichiers manquants dans data/ : {', '.join(manquants)}")
        st.info("Lance d'abord : python prep_data.py")
        return
    filtres = afficher_sidebar(data)
    df_c = data["creations"]
    mask = df_c["annee"].between(filtres["amin"], filtres["amax"]) & df_c["grand_secteur"].isin(filtres["secteurs"])
    ay = filtres["amax"]
    total = int(df_c[mask]["nb_creations"].sum())
    ca = int(df_c[(df_c["annee"]==ay) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    cp = int(df_c[(df_c["annee"]==ay-1) & df_c["grand_secteur"].isin(filtres["secteurs"])]["nb_creations"].sum())
    delta = ((ca-cp)/cp*100) if cp else 0
    actives = int(data["naf"][data["naf"]["grand_secteur"].isin(filtres["secteurs"])]["nb_entreprises"].sum())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Creations (periode)", f"{total:,}".replace(",","."))
    c2.metric(f"Creees en {ay}", f"{ca:,}".replace(",","."), f"{delta:+.1f}%")
    c3.metric("Actives", f"{actives:,}".replace(",","."))
    c4.metric("Secteurs", len(filtres["secteurs"]))
    st.divider()
    tab1,tab2,tab3,tab4,tab5 = st.tabs([
        "Creations","Etat des entreprises","Secteurs NAF","Taille","NAF 2008 -> 2025"
    ])
    with tab1: onglet_creations(data, filtres)
    with tab2: onglet_etat_entreprises(data, filtres)
    with tab3: onglet_secteurs(data, filtres)
    with tab4: onglet_taille(data, filtres)
    with tab5: onglet_naf_comparaison(data)


if __name__ == "__main__":
    main()
