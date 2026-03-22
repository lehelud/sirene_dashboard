""
app.py - Dashboard SIRENE v3
UX style Power BI / Tableau :
- Navigation laterale radio (pas d-onglets invisibles)
- CSS professionnel : fond clair, cards, accents bleus
- Header fixe avec KPIs
"""
import warnings
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as gogit pull

import streamlit as st
warnings.filterwarnings("ignore")
DATA_DIR = Path("data")

COLOR_MAP = {"Agriculture":"#27ae60","Industrie":"#2980b9","Construction":"#d35400","Commerce / Transport / HCR":"#8e44ad","Services aux entreprises":"#c0392b","Services publics / Sante":"#16a085","Autres":"#95a5a6"}
COLOR_EMP = {"Employeur":"#1a73e8","Employeur occasionnel":"#fbbc04","Non-employeur / NC":"#dadce0","Non renseigne":"#bdc3c7"}
ORDRE_TAILLE = ["Non-employeur / NC","0 sal. au 31/12","1-2","3-5","6-9","10-19","20-49","50-99","100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]
DEPT_COORDS = {"01":(46.2,5.2),"02":(49.5,3.6),"03":(46.3,3.1),"04":(44.1,6.2),"05":(44.7,6.3),"06":(43.9,7.1),"07":(44.8,4.5),"08":(49.7,4.7),"09":(42.9,1.5),"10":(48.3,4.1),"11":(43.2,2.3),"12":(44.4,2.6),"13":(43.5,5.4),"14":(49.1,-0.4),"15":(45.0,2.6),"16":(45.7,0.2),"17":(45.8,-0.7),"18":(47.1,2.4),"19":(45.4,1.9),"21":(47.4,4.9),"22":(48.3,-3.0),"23":(46.1,2.0),"24":(45.1,0.7),"25":(47.2,6.4),"26":(44.7,5.0),"27":(49.1,1.2),"28":(48.4,1.4),"29":(48.2,-4.0),"30":(44.0,4.2),"31":(43.6,1.4),"32":(43.7,0.6),"33":(44.9,-0.6),"34":(43.6,3.9),"35":(48.1,-1.7),"36":(46.8,1.6),"37":(47.2,0.7),"38":(45.2,5.7),"39":(46.7,5.6),"40":(43.9,-0.8),"41":(47.6,1.3),"42":(45.5,4.2),"43":(45.1,3.9),"44":(47.3,-1.5),"45":(47.9,2.1),"46":(44.5,1.6),"47":(44.4,0.5),"48":(44.5,3.5),"49":(47.4,-0.6),"50":(49.1,-1.3),"51":(49.1,4.1),"52":(48.1,5.1),"53":(48.1,-0.6),"54":(48.7,6.2),"55":(48.9,5.1),"56":(47.9,-2.9),"57":(49.1,6.2),"58":(47.2,3.7),"59":(50.5,3.1),"60":(49.4,2.4),"61":(48.6,0.1),"62":(50.5,2.6),"63":(45.8,3.1),"64":(43.3,-0.4),"65":(43.1,0.2),"66":(42.7,2.6),"67":(48.6,7.6),"68":(47.8,7.3),"69":(45.8,4.8),"70":(47.6,6.2),"71":(46.6,4.5),"72":(48.0,0.2),"73":(45.5,6.4),"74":(46.0,6.4),"75":(48.9,2.3),"76":(49.7,1.1),"77":(48.6,3.0),"78":(48.8,1.8),"79":(46.6,-0.3),"80":(49.9,2.3),"81":(43.9,2.2),"82":(44.0,1.4),"83":(43.4,6.2),"84":(43.9,5.0),"85":(46.7,-1.4),"86":(46.6,0.4),"87":(45.8,1.3),"88":(48.2,6.5),"89":(47.9,3.6),"90":(47.6,6.9),"91":(48.5,2.2),"92":(48.9,2.2),"93":(48.9,2.5),"94":(48.8,2.5),"95":(49.1,2.1),"2A":(41.6,9.0),"2B":(42.3,9.3)}
DEPT_NOM = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-HP","05":"Htes-Alpes","06":"Alpes-Mar.","07":"Ardeche","08":"Ardennes","09":"Ariege","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhone","14":"Calvados","15":"Cantal","16":"Charente","17":"Char.-Maritime","18":"Cher","19":"Correze","21":"Cote-d-Or","22":"Cotes-d-Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drome","27":"Eure","28":"Eure-et-Loir","29":"Finistere","30":"Gard","31":"Hte-Garonne","32":"Gers","33":"Gironde","34":"Herault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isere","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Hte-Loire","44":"Loire-Atl.","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozere","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Hte-Marne","53":"Mayenne","54":"M.-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nievre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dome","64":"Pyr.-Atl.","65":"Htes-Pyr.","66":"Pyr.-Or.","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhone","70":"Hte-Saone","71":"Saone-et-Loire","72":"Sarthe","73":"Savoie","74":"Hte-Savoie","75":"Paris","76":"Seine-Maritime","77":"S.-et-Marne","78":"Yvelines","79":"Deux-Sevres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendee","86":"Vienne","87":"Hte-Vienne","88":"Vosges","89":"Yonne","90":"Ter.-Belfort","91":"Essonne","92":"Hts-de-Seine","93":"Seine-St-Denis","94":"Val-de-Marne","95":"Val-d-Oise","2A":"Corse-du-Sud","2B":"Hte-Corse"}

# CSS Power BI / Tableau style
CSS = """
<style>
/* ── Fond et typographie ── */
[data-testid="stAppViewContainer"] { background: #f4f6f9 !important; }
[data-testid="stSidebar"] { background: #1e2d3d !important; }
[data-testid="stSidebar"] * { color: #e8edf2 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* ── Sidebar header ── */
.sb-header {
  background: #1565c0;
  padding: 20px 16px 16px;
  margin-bottom: 8px;
}
.sb-header h2 { color: #fff !important; font-size: 1.1rem; margin: 0; font-weight: 700; letter-spacing: .5px; }
.sb-header p  { color: #90caf9 !important; font-size: .75rem; margin: 4px 0 0; }

/* ── Navigation radio style menu ── */
[data-testid="stSidebar"] .stRadio > label {
  display: none;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 12px;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
  background: transparent;
  border-radius: 8px;
  padding: 10px 14px !important;
  cursor: pointer;
  transition: background .15s;
  display: flex !important;
  align-items: center;
  gap: 10px;
  font-size: .9rem !important;
  font-weight: 500 !important;
  color: #b0bec5 !important;
  border: none !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #fff !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"][aria-checked="true"] {
  background: rgba(21,101,192,0.5) !important;
  color: #fff !important;
  border-left: 3px solid #42a5f5 !important;
}
/* Masquer le cercle radio natif */
[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] .stRadio [class*="radioMarkInner"],
[data-testid="stSidebar"] .stRadio [class*="radioMarkOuter"] { display: none !important; }

/* ── Separateur sidebar ── */
.sb-sep { border-top: 1px solid #2d4a63; margin: 12px 16px; }
.sb-label { font-size: .7rem; color: #607d8b !important; text-transform: uppercase; letter-spacing: 1px; padding: 8px 16px 4px; }

/* ── Filtres sidebar ── */
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
  background: #243447 !important;
  border-color: #2d4a63 !important;
}
[data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
  background: #1565c0 !important;
}

/* ── Page header ── */
.page-header {
  background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
  border-radius: 12px;
  padding: 20px 28px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(21,101,192,.25);
}
.page-header h1 { color: #fff; font-size: 1.5rem; margin: 0; font-weight: 700; }
.page-header p  { color: #90caf9; font-size: .82rem; margin: 4px 0 0; }

/* ── KPI cards ── */
[data-testid="metric-container"] {
  background: #fff !important;
  border-radius: 10px !important;
  padding: 16px 20px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
  border-left: 4px solid #1565c0 !important;
}
[data-testid="stMetricLabel"]  { color: #546e7a !important; font-size: .78rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .5px; }
[data-testid="stMetricValue"]  { color: #1a237e !important; font-size: 1.6rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"]  { font-size: .82rem !important; }

/* ── Contenu principal ── */
.block-container { padding: 1.5rem 2rem 2rem !important; background: #f4f6f9 !important; }

/* ── Titres sections ── */
h2[data-testid="stHeading"], h3[data-testid="stHeading"] {
  color: #1a237e !important;
  font-weight: 700 !important;
  padding-bottom: 6px;
  border-bottom: 2px solid #e8edf5;
  margin-bottom: 16px !important;
}

/* ── Charts ── */
.js-plotly-plot { border-radius: 10px; }

/* ── Divider ── */
hr { border-color: #e0e7ef !important; }

/* ── Caption ── */
.stCaption { color: #78909c !important; font-size: .75rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f4f6f9; }
::-webkit-scrollbar-thumb { background: #b0bec5; border-radius: 3px; }
</style>
"""

# Icones navigation
NAV_PAGES = [
    "Vue d-ensemble",
    "Tendances",
    "Structure",
    "Survie",
    "Carte",
    "NAF 2008 -> 2025",
]
NAV_ICONS = {
    "Vue d-ensemble":   "Overview",
    "Tendances":        "Tendances",
    "Structure":        "Structure",
    "Survie":           "Survie",
    "Carte":            "Carte",
    "NAF 2008 -> 2025": "NAF 2025",
}

@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    req = ["creations_mensuel","stock_actives","formes_juridiques","employeurs","departements","survie","naf_detail"]
    manquants = [n for n in req if not (DATA_DIR/f"{n}.parquet").exists()]
    if manquants: return None, manquants
    return {n: pd.read_parquet(DATA_DIR/f"{n}.parquet") for n in req}, []

def fmt(n): return f"{int(n):,}".replace(",","\u202f")

def bg(): return "rgba(0,0,0,0)"  # fond transparent pour tous les charts

def chart_layout(fig, h=400):
    fig.update_layout(
        plot_bgcolor=bg(), paper_bgcolor=bg(),
        font=dict(family="Inter, system-ui, sans-serif", color="#37474f"),
        height=h,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font_size=11),
        margin=dict(t=40, b=30, l=10, r=10),
        xaxis=dict(showgrid=False, linecolor="#e0e7ef"),
        yaxis=dict(showgrid=True, gridcolor="#f0f4f8", linecolor="#e0e7ef"),
        hoverlabel=dict(bgcolor="#1a237e", font_color="#fff", font_size=12),
    )
    return fig

def page_header(titre, sous_titre=""):
    st.markdown(f'<div class="page-header"><div><h1>{titre}</h1><p>{sous_titre}</p></div></div>', unsafe_allow_html=True)


def onglet_vue_ensemble(data, secteurs_choisis):
    page_header("Vue d-ensemble", "Tissu economique du secteur marchand francais - Base SIRENE")
    sa=data["stock_actives"]; cm=data["creations_mensuel"]; emp=data["employeurs"]
    sa_f=sa[sa["grand_secteur"].isin(secteurs_choisis)]
    total_actives=sa_f["nb"].sum()
    nb_emp=emp[(emp["grand_secteur"].isin(secteurs_choisis))&(emp["statut_employeur"]=="Employeur")]["nb"].sum()
    nb_ess=sa_f["nb_ess"].sum() if "nb_ess" in sa_f.columns else 0
    pct_emp=nb_emp/total_actives*100 if total_actives else 0
    mois_rec=sorted(cm["mois"].dropna().unique())[-12:]
    creations_12m=cm[cm["mois"].isin(mois_rec)&cm["grand_secteur"].isin(secteurs_choisis)]["nb_creations"].sum()
    annee_max=int(cm["annee"].max())
    ann_n=cm[(cm["annee"]==annee_max)&cm["grand_secteur"].isin(secteurs_choisis)]["nb_creations"].sum()
    ann_nm1=cm[(cm["annee"]==annee_max-1)&cm["grand_secteur"].isin(secteurs_choisis)]["nb_creations"].sum()
    delta_ann=(ann_n-ann_nm1)/ann_nm1*100 if ann_nm1 else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Entreprises actives",fmt(total_actives))
    c2.metric("Creations 12 mois",fmt(creations_12m))
    c3.metric(f"Creations {annee_max}",fmt(ann_n),f"{delta_ann:+.1f}% vs {annee_max-1}")
    c4.metric("Employeurs (effectif connu)",fmt(nb_emp),f"{pct_emp:.1f}% des actives")
    c5.metric("Economie sociale (ESS)",fmt(nb_ess))
    st.divider()
    col1,col2=st.columns([3,2])
    with col1:
        d=sa_f.groupby("grand_secteur")["nb"].sum().reset_index()
        d["pct"]=(d["nb"]/d["nb"].sum()*100).round(1)
        fig=px.treemap(d,path=["grand_secteur"],values="nb",color="grand_secteur",
            color_discrete_map=COLOR_MAP,custom_data=["pct"],title="Entreprises actives par secteur")
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]:.1f}%",textfont_size=13)
        fig.update_layout(margin=dict(t=40,l=0,r=0,b=0),height=380,paper_bgcolor=bg())
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        d2=sa_f.groupby("grand_secteur")["nb"].sum().reset_index().sort_values("nb",ascending=True)
        fig2=px.bar(d2,x="nb",y="grand_secteur",orientation="h",color="grand_secteur",
            color_discrete_map=COLOR_MAP,text="nb",labels={"nb":"Actives","grand_secteur":""})
        fig2.update_traces(texttemplate="%{text:,.0f}",textposition="outside")
        chart_layout(fig2,380); fig2.update_layout(showlegend=False,yaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    st.subheader("Structure par rapport a l-emploi")
    st.caption("Note INSEE : code NN = non-employeur OU donnee manquante. La variable caractereEmployeurUniteLegale est abandonnee par l-INSEE depuis 2023.")
    emp_f=emp[emp["grand_secteur"].isin(secteurs_choisis)]
    ordre_emp=["Employeur","Employeur occasionnel","Non-employeur / NC","Non renseigne"]
    fig3=px.bar(emp_f,x="grand_secteur",y="nb",color="statut_employeur",barmode="stack",
        color_discrete_map=COLOR_EMP,category_orders={"statut_employeur":ordre_emp},
        title="Repartition par statut employeur",labels={"nb":"Nb","grand_secteur":"","statut_employeur":"Statut"})
    chart_layout(fig3,350); fig3.update_layout(xaxis=dict(tickangle=15,showgrid=False))
    st.plotly_chart(fig3,use_container_width=True)


def onglet_tendances(data, secteurs_choisis):
    page_header("Tendances","Dynamique de creation - Evolution et saisonnalite")
    cm=data["creations_mensuel"]; cm_f=cm[cm["grand_secteur"].isin(secteurs_choisis)]
    d=cm_f.groupby(["mois","grand_secteur"])["nb_creations"].sum().reset_index()
    d=d[d["mois"]>="2015-01"].sort_values("mois")
    d["mm3"]=d.groupby("grand_secteur")["nb_creations"].transform(lambda x:x.rolling(3,min_periods=1).mean())
    fig=go.Figure()
    for sect in d["grand_secteur"].unique():
        ds=d[d["grand_secteur"]==sect]
        fig.add_scatter(x=ds["mois"],y=ds["nb_creations"],name=sect,mode="lines",
            line=dict(color=COLOR_MAP.get(sect,"#95a5a6"),width=1),opacity=0.2,showlegend=False)
        fig.add_scatter(x=ds["mois"],y=ds["mm3"],name=sect,mode="lines",
            line=dict(color=COLOR_MAP.get(sect,"#95a5a6"),width=2.5))
    chart_layout(fig,380); fig.update_layout(title="Creations mensuelles (trait epais = MM3)",hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True)
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Saisonnalite")
        cm2=cm.copy(); cm2["num_mois"]=pd.to_numeric(cm2["mois"].str[-2:],errors="coerce")
        sais=cm2.groupby("num_mois")["nb_creations"].mean().reset_index().dropna()
        mnoms={1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sais["mois_nom"]=sais["num_mois"].map(mnoms)
        moy=sais["nb_creations"].mean()
        sais["ecart"]=((sais["nb_creations"]-moy)/moy*100).round(1)
        fig2=px.bar(sais,x="mois_nom",y="ecart",
            color=sais["ecart"].apply(lambda x:"Au-dessus" if x>=0 else "En-dessous"),
            color_discrete_map={"Au-dessus":"#27ae60","En-dessous":"#e74c3c"},
            title="Ecart a la moyenne par mois (%)",labels={"mois_nom":"","ecart":"Ecart (%)"})
        chart_layout(fig2,320); fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2,use_container_width=True)
    with col2:
        st.subheader("Croissance annuelle par secteur")
        ann=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
        ann=ann[ann["annee"]>=2015].sort_values(["grand_secteur","annee"])
        ann["croissance"]=ann.groupby("grand_secteur")["nb_creations"].pct_change()*100
        ann=ann.dropna(subset=["croissance"])
        fig3=px.line(ann,x="annee",y="croissance",color="grand_secteur",color_discrete_map=COLOR_MAP,
            markers=True,title="Taux de croissance annuel (%)",
            labels={"annee":"","croissance":"Croissance (%)","grand_secteur":"Secteur"})
        fig3.add_hline(y=0,line_dash="dash",line_color="#cfd8dc",opacity=0.6)
        chart_layout(fig3,320); fig3.update_layout(hovermode="x unified")
        st.plotly_chart(fig3,use_container_width=True)
    st.subheader("Heatmap")
    heat_g=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
    heat_g=heat_g[heat_g["annee"]>=2010]
    pivot=heat_g.pivot(index="grand_secteur",columns="annee",values="nb_creations").fillna(0)
    fig4=px.imshow(pivot,color_continuous_scale="Blues",title="Intensite des creations par annee",labels={"color":"Nb creations"})
    fig4.update_layout(paper_bgcolor=bg(),height=300,margin=dict(t=40,b=20,l=10,r=10))
    st.plotly_chart(fig4,use_container_width=True)

def onglet_carte(data, secteurs_choisis):
    page_header("Carte","Repartition geographique des etablissements par departement")
    dept=data["departements"]; dept_f=dept[dept["grand_secteur"].isin(secteurs_choisis)].copy()
    col1,col2=st.columns([2,1])
    with col1: mode=st.radio("Afficher",["Nombre d-etablissements","Densite sectorielle (%)"],horizontal=True)
    with col2: secteur_focus=st.selectbox("Focus secteur",["Tous"]+sorted(secteurs_choisis))
    if mode=="Nombre d-etablissements":
        if secteur_focus=="Tous":
            map_data=dept_f.groupby("code_dept")["nb_etablissements"].sum().reset_index()
            map_data.columns=["code_dept","valeur"]; titre="Etablissements"
        else:
            map_data=dept_f[dept_f["grand_secteur"]==secteur_focus][["code_dept","nb_etablissements"]].copy()
            map_data.columns=["code_dept","valeur"]; titre=f"Etabl. {secteur_focus}"
    else:
        if secteur_focus=="Tous":
            map_data=dept_f.sort_values("nb_etablissements",ascending=False).drop_duplicates("code_dept")[["code_dept","pct_secteur"]].copy()
            map_data.columns=["code_dept","valeur"]; titre="% secteur dominant"
        else:
            map_data=dept_f[dept_f["grand_secteur"]==secteur_focus][["code_dept","pct_secteur"]].copy()
            map_data.columns=["code_dept","valeur"]; titre=f"% {secteur_focus}"
    map_data["lat"]=map_data["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[0])
    map_data["lon"]=map_data["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[1])
    map_data["nom"]=map_data["code_dept"].map(DEPT_NOM).fillna(map_data["code_dept"])
    map_data=map_data.dropna(subset=["lat","lon"])
    vmax=map_data["valeur"].max()
    map_data["texte"]=map_data.apply(lambda r:f"<b>{r['nom']}</b> ({r['code_dept']})<br>{titre}: {r['valeur']:,.0f}",axis=1)
    fig=go.Figure()
    fig.add_scattermapbox(lat=map_data["lat"],lon=map_data["lon"],mode="markers",
        marker=go.scattermapbox.Marker(
            size=map_data["valeur"].apply(lambda v:max(8,min(40,v/vmax*40)) if vmax else 10),
            color=map_data["valeur"],colorscale="Blues",showscale=True,
            colorbar=dict(title=titre,thickness=12,tickfont=dict(size=11)),opacity=0.85),
        text=map_data["texte"],hoverinfo="text")
    fig.update_layout(mapbox=dict(style="carto-positron",center=dict(lat=46.5,lon=2.5),zoom=4.8),
        margin=dict(l=0,r=0,t=0,b=0),height=520,paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Top 10 departements")
        top10=map_data.nlargest(10,"valeur")[["nom","code_dept","valeur"]].copy()
        top10.columns=["Departement","Code","Valeur"]
        top10["Valeur"]=top10["Valeur"].map(lambda v:f"{v:,.0f}")
        st.dataframe(top10.reset_index(drop=True),use_container_width=True,hide_index=True)
    with col2:
        st.subheader("Mix sectoriel - 15 plus grands departements")
        top15=map_data.nlargest(15,"valeur")["code_dept"].tolist()
        dt=dept_f[dept_f["code_dept"].isin(top15)].copy()
        dt["nom"]=dt["code_dept"].map(DEPT_NOM).fillna(dt["code_dept"])
        dt_g=dt.groupby(["nom","grand_secteur"])["nb_etablissements"].sum().reset_index()
        fig2=px.bar(dt_g,x="nom",y="nb_etablissements",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,labels={"nom":"","nb_etablissements":"Nb","grand_secteur":"Secteur"})
        chart_layout(fig2,350); fig2.update_layout(xaxis=dict(tickangle=45,showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)


NAF_CHANGEMENTS = [
    ("01","Culture et prod. animale","01","Production agricole","Recode"),
    ("02","Sylviculture","02","Sylviculture","Identique"),
    ("10","Industries alimentaires","10","Industries alimentaires","Identique"),
    ("26","Fab. produits electroniques","26","Electronique","Recode"),
    ("41","Construction batiments","41","Construction batiments","Identique"),
    ("42","Genie civil","42","Genie civil","Identique"),
    ("43","Travaux specialises","43","Travaux specialises","Identique"),
    ("45","Commerce auto","45","Commerce auto","Identique"),
    ("46","Commerce gros","46","Commerce gros","Identique"),
    ("47","Commerce detail","47","Commerce detail","Identique"),
    ("49","Transports terrestres","49","Transports terrestres","Identique"),
    ("55","Hebergement","55","Hebergement","Identique"),
    ("56","Restauration","56","Restauration","Identique"),
    ("62","Programmation, conseil IT","62","Act. informatiques","Recode"),
    ("63","Services information","62","Act. informatiques","Fusion"),
    ("64","Act. financieres","64","Act. financieres","Identique"),
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
    ("80","Securite","80","Securite","Identique"),
    ("81","Services batiments","81","Services batiments","Identique"),
    ("82","Services administratifs","82","Services admin.","Recode"),
    ("85","Enseignement","85","Enseignement","Identique"),
    ("86","Act. sante humaine","86","Sante humaine","Recode"),
    ("88","Action sociale","88","Action sociale","Identique"),
    ("90","Arts, spectacles","90","Arts, spectacles","Identique"),
    ("93","Sports, loisirs","93","Sports, loisirs","Identique"),
    ("95","Reparation","95","Reparation","Identique"),
    ("96","Services perso","96","Services perso","Identique"),
]
COULEURS_NAF={"Identique":"#27ae60","Recode":"#f39c12","Fusion":"#e74c3c","Division":"#2980b9"}

def onglet_naf(data):
    page_header("NAF 2008 -> 2025","Impact de la nouvelle nomenclature en vigueur au 1er janvier 2027")
    df_ch=pd.DataFrame(NAF_CHANGEMENTS,columns=["div_2008","lib_2008","div_2025","lib_2025","type"])
    naf_d=data["naf_detail"].copy()
    naf_d["div_naf"]=naf_d["div_naf"].astype(str).str.zfill(2)
    df_ch["div_2008"]=df_ch["div_2008"].astype(str).str.zfill(2)
    df_ch=df_ch.merge(naf_d.groupby("div_naf")["nb"].sum().reset_index().rename(columns={"div_naf":"div_2008","nb":"nb_entreprises"}),on="div_2008",how="left").fillna({"nb_entreprises":0})
    df_ch["nb_entreprises"]=df_ch["nb_entreprises"].astype(int)
    total=len(df_ch); identiques=(df_ch["type"]=="Identique").sum()
    recodes=(df_ch["type"]=="Recode").sum(); fusions=(df_ch["type"]=="Fusion").sum()
    nb_imp=df_ch[df_ch["type"]!="Identique"]["nb_entreprises"].sum(); nb_tot=df_ch["nb_entreprises"].sum()
    pct_imp=nb_imp/nb_tot*100 if nb_tot else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Divisions",total); c2.metric("Identiques",f"{identiques} ({identiques/total*100:.0f}%)")
    c3.metric("Recodes",f"{recodes} ({recodes/total*100:.0f}%)"); c4.metric("Fusions",fusions)
    c5.metric("Entreprises impactees",fmt(nb_imp),f"{pct_imp:.1f}% du total")
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        d_types=df_ch.groupby("type").agg(nb_div=("div_2008","count"),nb_ent=("nb_entreprises","sum")).reset_index()
        fig=px.treemap(d_types,path=["type"],values="nb_ent",color="type",color_discrete_map=COULEURS_NAF,
            title="Entreprises concernees par type de changement",custom_data=["nb_div"])
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]} divisions",textfont_size=12)
        fig.update_layout(margin=dict(t=40,l=0,r=0,b=0),height=320,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        df_imp=df_ch[df_ch["type"]!="Identique"].nlargest(15,"nb_entreprises")
        fig2=px.bar(df_imp,x="nb_entreprises",y="lib_2008",orientation="h",color="type",
            color_discrete_map=COULEURS_NAF,title="Top 15 divisions impactees",
            labels={"lib_2008":"","nb_entreprises":"Nb entreprises","type":"Type"})
        chart_layout(fig2,320); fig2.update_layout(yaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    st.subheader("Table de correspondance")
    c1,c2,c3=st.columns(3)
    with c1: filtre_type=st.multiselect("Type",df_ch["type"].unique().tolist(),default=df_ch["type"].unique().tolist())
    with c2: rech=st.text_input("Rechercher",placeholder="ex: 62, informatique...")
    with c3: tri=st.selectbox("Trier par",["Nb entreprises","Division 2008","Type"])
    df_aff=df_ch[df_ch["type"].isin(filtre_type)].copy()
    if rech:
        mask=(df_aff["div_2008"].str.contains(rech,case=False)|df_aff["lib_2008"].str.contains(rech,case=False)|df_aff["lib_2025"].str.contains(rech,case=False))
        df_aff=df_aff[mask]
    if tri=="Nb entreprises": df_aff=df_aff.sort_values("nb_entreprises",ascending=False)
    elif tri=="Division 2008": df_aff=df_aff.sort_values("div_2008")
    else: df_aff=df_aff.sort_values("type")
    df_aff["nb_entreprises"]=df_aff["nb_entreprises"].map(lambda x:f"{x:,}".replace(",","\u202f"))
    df_aff.columns=["Div. 2008","Libelle 2008","Div. 2025","Libelle 2025","Type","Nb entreprises"]
    st.dataframe(df_aff.style.map(lambda v:f"background-color:{COULEURS_NAF.get(v,'#95a5a6')}22;color:{COULEURS_NAF.get(v,'#37474f')};font-weight:bold",subset=["Type"]),
        use_container_width=True,height=400,hide_index=True)
    st.caption(f"{len(df_aff)} divisions affichees")

def main():
    st.set_page_config(page_title="Dashboard SIRENE",page_icon="",layout="wide",initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)
    data, manquants = charger_donnees()
    if data is None:
        st.error(f"Fichiers manquants : {', '.join(manquants)}")
        st.code("python prep_data.py", language="bash")
        return

    # ── Sidebar ─────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-header"><h2>SIRENE Dashboard</h2><p>Base INSEE - data.gouv.fr</p></div>', unsafe_allow_html=True)

    # Navigation principale
    st.sidebar.markdown('<div class="sb-label">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "Navigation",
        options=NAV_PAGES,
        label_visibility="collapsed",
    )

    st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)

    # Filtres
    st.sidebar.markdown('<div class="sb-label">FILTRES</div>', unsafe_allow_html=True)
    all_secteurs = sorted(data["creations_mensuel"]["grand_secteur"].dropna().unique().tolist())
    secteurs_choisis = st.sidebar.multiselect(
        "Secteurs",
        all_secteurs,
        default=[s for s in all_secteurs if s != "Autres"],
        label_visibility="collapsed",
    )
    if not secteurs_choisis:
        st.sidebar.warning("Selectionnez au moins un secteur.")
        return

    st.sidebar.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
    st.sidebar.caption("Source : INSEE / data.gouv.fr")
    st.sidebar.caption("Mise a jour mensuelle")

    # ── Contenu ──────────────────────────────────────────────────
    if page == "Vue d-ensemble":
        onglet_vue_ensemble(data, secteurs_choisis)
    elif page == "Tendances":
        onglet_tendances(data, secteurs_choisis)
    elif page == "Structure":
        onglet_structure(data, secteurs_choisis)
    elif page == "Survie":
        onglet_survie(data)
    elif page == "Carte":
        onglet_carte(data, secteurs_choisis)
    elif page == "NAF 2008 -> 2025":
        onglet_naf(data)


if __name__ == "__main__":
    main()

def page_tendances(data, sects):
    ph("Tendances","Dynamique de creation - Evolution et saisonnalite")
    cm=data["creations_mensuel"]; cm_f=cm[cm["grand_secteur"].isin(sects)]
    d=cm_f.groupby(["mois","grand_secteur"])["nb_creations"].sum().reset_index()
    d=d[d["mois"]>="2015-01"].sort_values("mois")
    d["mm3"]=d.groupby("grand_secteur")["nb_creations"].transform(lambda x:x.rolling(3,min_periods=1).mean())
    fig=go.Figure()
    for sect in sorted(d["grand_secteur"].unique()):
        ds=d[d["grand_secteur"]==sect]; col=COLOR_MAP.get(sect,"#95a5a6")
        fig.add_scatter(x=ds["mois"],y=ds["nb_creations"],name=sect,mode="lines",
            line=dict(color=col,width=1),opacity=0.18,showlegend=False)
        fig.add_scatter(x=ds["mois"],y=ds["mm3"],name=sect,mode="lines",
            line=dict(color=col,width=2.5))
    T(fig,360); fig.update_layout(title="Creations mensuelles - trait epais = moyenne mobile 3 mois",hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True)
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Saisonnalite")
        cm2=cm.copy(); cm2["num_mois"]=pd.to_numeric(cm2["mois"].str[-2:],errors="coerce")
        sais=cm2.groupby("num_mois")["nb_creations"].mean().reset_index().dropna()
        mnoms={1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sais["mois_nom"]=sais["num_mois"].map(mnoms)
        moy=sais["nb_creations"].mean()
        sais["ecart"]=((sais["nb_creations"]-moy)/moy*100).round(1)
        fig2=px.bar(sais,x="mois_nom",y="ecart",
            color=sais["ecart"].apply(lambda x:"+" if x>=0 else "-"),
            color_discrete_map={"+":"#27ae60","-":"#e74c3c"},
            title="Ecart a la moyenne par mois (%)",labels={"mois_nom":"","ecart":"Ecart (%)"})
        T(fig2,300); fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2,use_container_width=True)
    with col2:
        st.subheader("Croissance annuelle")
        ann=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
        ann=ann[ann["annee"]>=2015].sort_values(["grand_secteur","annee"])
        ann["g"]=ann.groupby("grand_secteur")["nb_creations"].pct_change()*100
        ann=ann.dropna(subset=["g"])
        fig3=px.line(ann,x="annee",y="g",color="grand_secteur",color_discrete_map=COLOR_MAP,
            markers=True,title="Taux de croissance annuel (%)",
            labels={"annee":"","g":"Croissance (%)","grand_secteur":"Secteur"})
        fig3.add_hline(y=0,line_dash="dash",line_color="#b0bec5")
        T(fig3,300); fig3.update_layout(hovermode="x unified")
        st.plotly_chart(fig3,use_container_width=True)
    st.subheader("Heatmap")
    hg=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
    hg=hg[hg["annee"]>=2010]
    pv=hg.pivot(index="grand_secteur",columns="annee",values="nb_creations").fillna(0)
    fig4=px.imshow(pv,color_continuous_scale="Blues",labels={"color":"Creations"})
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=280,margin=dict(t=10,b=20,l=10,r=10))
    st.plotly_chart(fig4,use_container_width=True)


def page_structure(data, sects):
    ph("Structure","Composition du tissu economique - Formes, tailles, concentration")
    sa=data["stock_actives"]; fj=data["formes_juridiques"]; sa_f=sa[sa["grand_secteur"].isin(sects)]
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Formes juridiques")
        fj_g=fj[fj["grand_secteur"].isin(sects)].groupby("forme_jur")["nb"].sum().reset_index().sort_values("nb",ascending=False)
        fig=px.pie(fj_g,values="nb",names="forme_jur",hole=0.45,
            color_discrete_sequence=["#1565c0","#42a5f5","#90caf9","#bbdefb","#e3f2fd"])
        fig.update_traces(textposition="inside",textinfo="percent+label")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=340,margin=dict(t=10,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Taille par effectifs")
        ordre={v:i for i,v in enumerate(ORDRE_TAILLE)}
        tg=sa_f.groupby("libelle_taille")["nb"].sum().reset_index()
        tg["ord"]=tg["libelle_taille"].map(ordre).fillna(99)
        tg=tg.sort_values("ord")
        fig2=px.treemap(tg,path=["libelle_taille"],values="nb",color="nb",color_continuous_scale="Blues")
        fig2.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}",textfont_size=11)
        fig2.update_layout(margin=dict(t=10,l=0,r=0,b=0),height=340,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    st.subheader("Pareto - concentration sectorielle")
    sg=sa_f.groupby("grand_secteur")["nb"].sum().reset_index().sort_values("nb",ascending=False)
    sg["cumul"]=sg["nb"].cumsum()/sg["nb"].sum()*100
    fig3=go.Figure()
    fig3.add_bar(x=sg["grand_secteur"],y=sg["nb"],
        marker_color=[COLOR_MAP.get(s,"#95a5a6") for s in sg["grand_secteur"]],name="Nb actives",yaxis="y")
    fig3.add_scatter(x=sg["grand_secteur"],y=sg["cumul"],name="Cumul %",
        mode="lines+markers",line=dict(color="#1565c0",width=2),yaxis="y2")
    fig3.add_hline(y=80,line_dash="dash",line_color="#e74c3c",annotation_text="80%",yref="y2")
    fig3.update_layout(yaxis=dict(title="Nb",showgrid=False),
        yaxis2=dict(title="Cumul %",overlaying="y",side="right",range=[0,110],showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",height=320,
        margin=dict(t=20,b=20,l=8,r=8),legend=dict(orientation="h",yanchor="bottom",y=1.02),
        xaxis=dict(tickangle=15,showgrid=False))
    st.plotly_chart(fig3,use_container_width=True)
    st.divider()
    st.subheader("Top 20 divisions NAF")
    top20=data["naf_detail"][data["naf_detail"]["grand_secteur"].isin(sects)].nlargest(20,"nb")
    fig4=px.bar(top20,x="nb",y="div_naf",orientation="h",color="grand_secteur",
        color_discrete_map=COLOR_MAP,labels={"div_naf":"Code NAF","nb":"Actives","grand_secteur":"Secteur"})
    T(fig4,480); fig4.update_layout(yaxis=dict(showgrid=False))
    st.plotly_chart(fig4,use_container_width=True)


def page_survie(data):
    ph("Survie","Longevite des entreprises - Taux de survie par cohorte de creation")
    df_s=data["survie"]
    if df_s.empty: st.warning("Donnees de survie non disponibles."); return
    c1,c2,c3=st.columns(3)
    for dur,col in [(1,c1),(3,c2),(5,c3)]:
        d=df_s[df_s["duree_ans"]==dur]
        if not d.empty: col.metric(f"Survie a {dur} an{'s' if dur>1 else ''}",f"{d['taux_survie'].mean():.1f}%")
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Heatmap cohorte x duree")
        pv=df_s.pivot(index="annee_creation",columns="duree_ans",values="taux_survie")
        fig=px.imshow(pv,color_continuous_scale="RdYlGn",
            labels={"color":"Survie %","x":"Duree (ans)","y":"Annee"},zmin=0,zmax=100)
        fig.update_traces(texttemplate="%{z:.0f}%",textfont_size=10)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=400,margin=dict(t=20,b=20))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Courbe de survie moyenne")
        sa=df_s.groupby("duree_ans")["taux_survie"].mean().reset_index()
        fig2=go.Figure()
        fig2.add_scatter(x=sa["duree_ans"],y=sa["taux_survie"],mode="lines+markers+text",
            text=sa["taux_survie"].map(lambda x:f"{x:.1f}%"),textposition="top center",
            line=dict(color="#1565c0",width=3),marker=dict(size=9,color="#1565c0"),
            fill="tozeroy",fillcolor="rgba(21,101,192,.09)")
        fig2.update_layout(xaxis=dict(title="Duree (ans)",showgrid=False),
            yaxis=dict(title="Survie %",range=[0,105],showgrid=True,gridcolor="#eef2f7"),
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",height=400,margin=dict(t=20,b=20,l=8,r=8))
        st.plotly_chart(fig2,use_container_width=True)
    s3=df_s[df_s["duree_ans"]==3].sort_values("annee_creation")
    if not s3.empty:
        st.subheader("Evolution du taux de survie a 3 ans")
        fig3=px.line(s3,x="annee_creation",y="taux_survie",markers=True,
            color_discrete_sequence=["#1565c0"],
            labels={"annee_creation":"Annee de creation","taux_survie":"Survie %"})
        fig3.add_hline(y=s3["taux_survie"].mean(),line_dash="dash",line_color="#e74c3c",
            annotation_text=f"Moy. {s3['taux_survie'].mean():.1f}%")
        T(fig3,280)
        st.plotly_chart(fig3,use_container_width=True)

def page_carte(data, sects):
    ph("Carte","Repartition geographique des etablissements par departement")
    dept=data["departements"]; dept_f=dept[dept["grand_secteur"].isin(sects)].copy()
    col1,col2=st.columns([2,1])
    with col1: mode=st.radio("Afficher",["Nombre d'etablissements","Densite (%)"],horizontal=True)
    with col2: sf=st.selectbox("Focus secteur",["Tous"]+sorted(sects))
    if "Nombre" in mode:
        md=dept_f.groupby("code_dept")["nb_etablissements"].sum().reset_index() if sf=="Tous" else dept_f[dept_f["grand_secteur"]==sf][["code_dept","nb_etablissements"]].copy()
        md.columns=["code_dept","val"]; titre="Etablissements"
    else:
        md=dept_f.sort_values("nb_etablissements",ascending=False).drop_duplicates("code_dept")[["code_dept","pct_secteur"]].copy() if sf=="Tous" else dept_f[dept_f["grand_secteur"]==sf][["code_dept","pct_secteur"]].copy()
        md.columns=["code_dept","val"]; titre="%"
    md["lat"]=md["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[0])
    md["lon"]=md["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[1])
    md["nom"]=md["code_dept"].map(DEPT_NOM).fillna(md["code_dept"])
    md=md.dropna(subset=["lat","lon"])
    vmax=md["val"].max()
    md["txt"]=md.apply(lambda r:f"<b>{r['nom']}</b><br>{titre}: {r['val']:,.0f}",axis=1)
    fig=go.Figure()
    fig.add_scattermapbox(lat=md["lat"],lon=md["lon"],mode="markers",
        marker=go.scattermapbox.Marker(
            size=md["val"].apply(lambda v:max(7,min(38,v/vmax*38)) if vmax else 8),
            color=md["val"],colorscale="Blues",showscale=True,
            colorbar=dict(title=titre,thickness=10),opacity=0.82),
        text=md["txt"],hoverinfo="text")
    fig.update_layout(mapbox=dict(style="carto-positron",center=dict(lat=46.5,lon=2.5),zoom=4.8),
        margin=dict(l=0,r=0,t=0,b=0),height=500,paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Top 10 departements")
        t10=md.nlargest(10,"val")[["nom","code_dept","val"]].copy()
        t10.columns=["Departement","Code","Valeur"]
        t10["Valeur"]=t10["Valeur"].map(lambda v:f"{v:,.0f}")
        st.dataframe(t10.reset_index(drop=True),use_container_width=True,hide_index=True)
    with col2:
        st.subheader("Mix sectoriel - 12 plus grands")
        top12=md.nlargest(12,"val")["code_dept"].tolist()
        dt=dept_f[dept_f["code_dept"].isin(top12)].copy()
        dt["nom"]=dt["code_dept"].map(DEPT_NOM).fillna(dt["code_dept"])
        dtg=dt.groupby(["nom","grand_secteur"])["nb_etablissements"].sum().reset_index()
        fig2=px.bar(dtg,x="nom",y="nb_etablissements",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,labels={"nom":"","nb_etablissements":"Nb","grand_secteur":"Secteur"})
        T(fig2,320); fig2.update_layout(xaxis=dict(tickangle=40,showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)


def page_naf(data):
    ph("NAF 2008 -> 2025","Impact de la nouvelle nomenclature en vigueur au 1er janvier 2027")
    df_ch=pd.DataFrame(NAF_CHANGEMENTS,columns=["div_2008","lib_2008","div_2025","lib_2025","type"])
    naf_d=data["naf_detail"].copy()
    naf_d["div_naf"]=naf_d["div_naf"].astype(str).str.zfill(2)
    df_ch["div_2008"]=df_ch["div_2008"].astype(str).str.zfill(2)
    df_ch=df_ch.merge(naf_d.groupby("div_naf")["nb"].sum().reset_index().rename(columns={"div_naf":"div_2008","nb":"nb_entreprises"}),on="div_2008",how="left").fillna({"nb_entreprises":0})
    df_ch["nb_entreprises"]=df_ch["nb_entreprises"].astype(int)
    total=len(df_ch); ident=(df_ch["type"]=="Identique").sum()
    recod=(df_ch["type"]=="Recode").sum(); fusio=(df_ch["type"]=="Fusion").sum()
    nb_imp=df_ch[df_ch["type"]!="Identique"]["nb_entreprises"].sum()
    nb_tot=df_ch["nb_entreprises"].sum(); pct=nb_imp/nb_tot*100 if nb_tot else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Divisions",total); c2.metric("Identiques",f"{ident} ({ident/total*100:.0f}%)")
    c3.metric("Recodes",f"{recod} ({recod/total*100:.0f}%)"); c4.metric("Fusions",fusio)
    c5.metric("Impactees",fmt(nb_imp),f"{pct:.1f}%")
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        dt=df_ch.groupby("type").agg(nb_div=("div_2008","count"),nb_ent=("nb_entreprises","sum")).reset_index()
        fig=px.treemap(dt,path=["type"],values="nb_ent",color="type",color_discrete_map=COULEURS_NAF,custom_data=["nb_div"])
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]} divisions",textfont_size=12)
        fig.update_layout(margin=dict(t=10,l=0,r=0,b=0),height=300,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        di=df_ch[df_ch["type"]!="Identique"].nlargest(12,"nb_entreprises")
        fig2=px.bar(di,x="nb_entreprises",y="lib_2008",orientation="h",color="type",
            color_discrete_map=COULEURS_NAF,labels={"lib_2008":"","nb_entreprises":"Nb","type":"Type"})
        T(fig2,300); fig2.update_layout(yaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    st.subheader("Table de correspondance")
    c1,c2,c3=st.columns(3)
    with c1: ft=st.multiselect("Type",df_ch["type"].unique().tolist(),default=df_ch["type"].unique().tolist())
    with c2: rech=st.text_input("Rechercher",placeholder="ex: 62, informatique...")
    with c3: tri=st.selectbox("Trier par",["Nb entreprises","Division 2008","Type"])
    df_a=df_ch[df_ch["type"].isin(ft)].copy()
    if rech:
        m=(df_a["div_2008"].str.contains(rech,case=False)|df_a["lib_2008"].str.contains(rech,case=False)|df_a["lib_2025"].str.contains(rech,case=False))
        df_a=df_a[m]
    if tri=="Nb entreprises": df_a=df_a.sort_values("nb_entreprises",ascending=False)
    elif tri=="Division 2008": df_a=df_a.sort_values("div_2008")
    else: df_a=df_a.sort_values("type")
    df_a["nb_entreprises"]=df_a["nb_entreprises"].map(lambda x:fmt(x))
    df_a.columns=["Div.2008","Libelle 2008","Div.2025","Libelle 2025","Type","Nb entreprises"]
    st.dataframe(df_a.style.map(lambda v:f"color:{COULEURS_NAF.get(v,'#37474f')};font-weight:600",subset=["Type"]),
        use_container_width=True,height=420,hide_index=True)
    st.caption(f"{len(df_a)} divisions affichees")


def main():
    st.set_page_config(page_title="Dashboard SIRENE",page_icon="",layout="wide",initial_sidebar_state="expanded")
    st.markdown(CSS,unsafe_allow_html=True)
    data,manquants=charger_donnees()
    if data is None:
        st.error(f"Fichiers manquants : {', '.join(manquants)}")
        st.code("python prep_data.py",language="bash"); return
    st.sidebar.markdown(
        '<div style="background:#1565c0;padding:16px;margin-bottom:6px">'
        '<div style="color:#fff;font-size:1.05rem;font-weight:700">SIRENE Dashboard</div>'
        '<div style="color:#90caf9;font-size:.75rem;margin-top:3px">Base INSEE - data.gouv.fr</div>'
        '</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-lbl">Navigation</div>',unsafe_allow_html=True)
    page=st.sidebar.radio("nav",
        ["Vue d'ensemble","Tendances","Structure","Survie","Carte","NAF 2008 -> 2025"],
        label_visibility="collapsed")
    st.sidebar.markdown('<div class="sb-sep"></div>',unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-lbl">Filtres</div>',unsafe_allow_html=True)
    all_s=sorted(data["creations_mensuel"]["grand_secteur"].dropna().unique().tolist())
    sects=st.sidebar.multiselect("Secteurs",all_s,
        default=[s for s in all_s if s!="Autres"],label_visibility="collapsed")
    if not sects: st.sidebar.warning("Selectionnez au moins un secteur."); return
    st.sidebar.markdown('<div class="sb-sep"></div>',unsafe_allow_html=True)
    st.sidebar.caption("Source : INSEE / data.gouv.fr")
    st.sidebar.caption("Mise a jour mensuelle")
    if   page=="Vue d'ensemble":    page_vue_ensemble(data,sects)
    elif page=="Tendances":          page_tendances(data,sects)
    elif page=="Structure":          page_structure(data,sects)
    elif page=="Survie":             page_survie(data)
    elif page=="Carte":              page_carte(data,sects)
    elif page=="NAF 2008 -> 2025":   page_naf(data)


if __name__=="__main__": main()
