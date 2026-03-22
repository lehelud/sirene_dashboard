"""
app.py - Dashboard SIRENE v2 - Tableau de bord ambitieux
6 onglets thematiques + carte interactive par departement
"""
import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")
DATA_DIR = Path("data")

COLOR_MAP = {
    "Agriculture":"#27ae60","Industrie":"#2980b9","Construction":"#d35400",
    "Commerce / Transport / HCR":"#8e44ad","Services aux entreprises":"#c0392b",
    "Services publics / Sante":"#16a085","Autres":"#7f8c8d",
}
ORDRE_TAILLE = ["Non employeur","0 sal.","1-2","3-5","6-9","10-19","20-49","50-99","100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]

DEPT_COORDS = {
    "01":(46.2,5.2),"02":(49.5,3.6),"03":(46.3,3.1),"04":(44.1,6.2),"05":(44.7,6.3),"06":(43.9,7.1),
    "07":(44.8,4.5),"08":(49.7,4.7),"09":(42.9,1.5),"10":(48.3,4.1),"11":(43.2,2.3),"12":(44.4,2.6),
    "13":(43.5,5.4),"14":(49.1,-0.4),"15":(45.0,2.6),"16":(45.7,0.2),"17":(45.8,-0.7),"18":(47.1,2.4),
    "19":(45.4,1.9),"21":(47.4,4.9),"22":(48.3,-3.0),"23":(46.1,2.0),"24":(45.1,0.7),"25":(47.2,6.4),
    "26":(44.7,5.0),"27":(49.1,1.2),"28":(48.4,1.4),"29":(48.2,-4.0),"30":(44.0,4.2),"31":(43.6,1.4),
    "32":(43.7,0.6),"33":(44.9,-0.6),"34":(43.6,3.9),"35":(48.1,-1.7),"36":(46.8,1.6),"37":(47.2,0.7),
    "38":(45.2,5.7),"39":(46.7,5.6),"40":(43.9,-0.8),"41":(47.6,1.3),"42":(45.5,4.2),"43":(45.1,3.9),
    "44":(47.3,-1.5),"45":(47.9,2.1),"46":(44.5,1.6),"47":(44.4,0.5),"48":(44.5,3.5),"49":(47.4,-0.6),
    "50":(49.1,-1.3),"51":(49.1,4.1),"52":(48.1,5.1),"53":(48.1,-0.6),"54":(48.7,6.2),"55":(48.9,5.1),
    "56":(47.9,-2.9),"57":(49.1,6.2),"58":(47.2,3.7),"59":(50.5,3.1),"60":(49.4,2.4),"61":(48.6,0.1),
    "62":(50.5,2.6),"63":(45.8,3.1),"64":(43.3,-0.4),"65":(43.1,0.2),"66":(42.7,2.6),"67":(48.6,7.6),
    "68":(47.8,7.3),"69":(45.8,4.8),"70":(47.6,6.2),"71":(46.6,4.5),"72":(48.0,0.2),"73":(45.5,6.4),
    "74":(46.0,6.4),"75":(48.9,2.3),"76":(49.7,1.1),"77":(48.6,3.0),"78":(48.8,1.8),"79":(46.6,-0.3),
    "80":(49.9,2.3),"81":(43.9,2.2),"82":(44.0,1.4),"83":(43.4,6.2),"84":(43.9,5.0),"85":(46.7,-1.4),
    "86":(46.6,0.4),"87":(45.8,1.3),"88":(48.2,6.5),"89":(47.9,3.6),"90":(47.6,6.9),"91":(48.5,2.2),
    "92":(48.9,2.2),"93":(48.9,2.5),"94":(48.8,2.5),"95":(49.1,2.1),"2A":(41.6,9.0),"2B":(42.3,9.3),
}
DEPT_NOM = {
    "01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-H-P","05":"Htes-Alpes","06":"Alpes-Mar.",
    "07":"Ardeche","08":"Ardennes","09":"Ariege","10":"Aube","11":"Aude","12":"Aveyron",
    "13":"Bouches-du-Rhone","14":"Calvados","15":"Cantal","16":"Charente","17":"Char.-Maritime",
    "18":"Cher","19":"Correze","21":"Cote-d-Or","22":"Cotes-d-Armor","23":"Creuse","24":"Dordogne",
    "25":"Doubs","26":"Drome","27":"Eure","28":"Eure-et-Loir","29":"Finistere","30":"Gard",
    "31":"Hte-Garonne","32":"Gers","33":"Gironde","34":"Herault","35":"Ille-et-Vilaine","36":"Indre",
    "37":"Indre-et-Loire","38":"Isere","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire",
    "43":"Hte-Loire","44":"Loire-Atl.","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozere",
    "49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Hte-Marne","53":"Mayenne","54":"M.-et-Moselle",
    "55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nievre","59":"Nord","60":"Oise","61":"Orne",
    "62":"Pas-de-Calais","63":"Puy-de-Dome","64":"Pyr.-Atl.","65":"Htes-Pyr.","66":"Pyr.-Or.",
    "67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhone","70":"Hte-Saone","71":"Saone-et-Loire",
    "72":"Sarthe","73":"Savoie","74":"Hte-Savoie","75":"Paris","76":"Seine-Maritime",
    "77":"S.-et-Marne","78":"Yvelines","79":"Deux-Sevres","80":"Somme","81":"Tarn",
    "82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendee","86":"Vienne",
    "87":"Hte-Vienne","88":"Vosges","89":"Yonne","90":"Ter.-Belfort","91":"Essonne",
    "92":"Hts-de-Seine","93":"Seine-St-Denis","94":"Val-de-Marne","95":"Val-d-Oise",
    "2A":"Corse-du-Sud","2B":"Hte-Corse",
}

@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    required = ["creations_mensuel","stock_actives","formes_juridiques","employeurs","departements","survie","naf_detail"]
    manquants = [n for n in required if not (DATA_DIR / f"{n}.parquet").exists()]
    if manquants: return None, manquants
    return {n: pd.read_parquet(DATA_DIR / f"{n}.parquet") for n in required}, []

def fmt(n): return f"{int(n):,}".replace(",","\u202f")

def onglet_vue_ensemble(data):
    st.header("Vue d'ensemble du tissu economique francais")
    sa=data["stock_actives"]; cm=data["creations_mensuel"]
    total_actives=sa["nb"].sum(); total_employeurs=sa["nb_employeurs"].sum(); total_ess=sa["nb_ess"].sum()
    pct_emp=total_employeurs/total_actives*100 if total_actives else 0
    pct_ess=total_ess/total_actives*100 if total_actives else 0
    mois_rec=sorted(cm["mois"].dropna().unique())[-12:]
    creations_12m=cm[cm["mois"].isin(mois_rec)]["nb_creations"].sum()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entreprises actives",fmt(total_actives))
    c2.metric("Creations (12 mois)",fmt(creations_12m))
    c3.metric("Dont employeurs",fmt(total_employeurs),f"{pct_emp:.1f}%")
    c4.metric("Economie sociale (ESS)",fmt(total_ess),f"{pct_ess:.1f}%")
    st.divider()
    col1,col2=st.columns([3,2])
    with col1:
        d=sa.groupby("grand_secteur")["nb"].sum().reset_index()
        d["pct"]=(d["nb"]/d["nb"].sum()*100).round(1)
        fig=px.treemap(d,path=["grand_secteur"],values="nb",color="grand_secteur",
            color_discrete_map=COLOR_MAP,custom_data=["pct"],title="Actives par secteur")
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]:.1f}%",textfont_size=13)
        fig.update_layout(margin=dict(t=40,l=0,r=0,b=0),height=380,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        d2=sa.groupby("grand_secteur")["nb"].sum().reset_index().sort_values("nb",ascending=True)
        fig2=px.bar(d2,x="nb",y="grand_secteur",orientation="h",color="grand_secteur",
            color_discrete_map=COLOR_MAP,text="nb",labels={"nb":"Actives","grand_secteur":"Secteur"})
        fig2.update_traces(texttemplate="%{text:,.0f}",textposition="outside")
        fig2.update_layout(showlegend=False,height=380,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    emp=data["employeurs"].copy(); emp["statut"]=emp["est_employeur"].map({True:"Employeurs",False:"Non employeurs"})
    emp_g=emp.groupby(["grand_secteur","statut"])["nb"].sum().reset_index()
    fig3=px.bar(emp_g,x="grand_secteur",y="nb",color="statut",barmode="stack",
        color_discrete_sequence=["#2ecc71","#bdc3c7"],title="Structure employeurs / non-employeurs",
        labels={"nb":"Nb","grand_secteur":"Secteur","statut":"Statut"})
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h",yanchor="bottom",y=1.02),xaxis=dict(tickangle=20,showgrid=False))
    st.plotly_chart(fig3,use_container_width=True)

def onglet_tendances(data, secteurs_choisis):
    st.header("Dynamique de creation - Tendances et saisonnalite")
    cm=data["creations_mensuel"]; cm=cm[cm["grand_secteur"].isin(secteurs_choisis)]
    d=cm.groupby(["mois","grand_secteur"])["nb_creations"].sum().reset_index()
    d=d[d["mois"]>="2015-01"]
    fig=px.line(d,x="mois",y="nb_creations",color="grand_secteur",color_discrete_map=COLOR_MAP,
        title="Creations mensuelles par secteur (2015-aujourd-hui)",
        labels={"mois":"Mois","nb_creations":"Creations","grand_secteur":"Secteur"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",legend=dict(orientation="h",yanchor="bottom",y=1.02),xaxis=dict(showgrid=False))
    st.plotly_chart(fig,use_container_width=True)
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Saisonnalite - Quel mois creer ?")
        cm2=data["creations_mensuel"].copy()
        cm2["num_mois"]=cm2["mois"].str[-2:]
        cm2["num_mois"]=pd.to_numeric(cm2["num_mois"],errors="coerce")
        sais=cm2.groupby("num_mois")["nb_creations"].mean().reset_index().dropna()
        mois_noms={1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sais["mois_nom"]=sais["num_mois"].map(mois_noms)
        fig2=px.bar(sais,x="mois_nom",y="nb_creations",color_discrete_sequence=["#3498db"],
            title="Creations moyennes par mois",labels={"mois_nom":"Mois","nb_creations":"Nb moyen"})
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    with col2:
        st.subheader("Evolution annuelle par secteur")
        ann=data["creations_mensuel"].copy()
        ann=ann[ann["grand_secteur"].isin(secteurs_choisis)]
        ann_g=ann.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
        ann_g=ann_g[ann_g["annee"]>=2010]
        fig3=px.line(ann_g,x="annee",y="nb_creations",color="grand_secteur",
            color_discrete_map=COLOR_MAP,markers=True,title="Creations annuelles",
            labels={"annee":"Annee","nb_creations":"Nb","grand_secteur":"Secteur"})
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",legend=dict(orientation="h",yanchor="bottom",y=1.02),xaxis=dict(showgrid=False))
        st.plotly_chart(fig3,use_container_width=True)
    st.subheader("Heatmap : intensite creations par annee et secteur")
    heat=data["creations_mensuel"].copy()
    heat=heat[heat["grand_secteur"].isin(secteurs_choisis)]
    heat_g=heat.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
    heat_g=heat_g[heat_g["annee"]>=2010]
    heat_pivot=heat_g.pivot(index="grand_secteur",columns="annee",values="nb_creations").fillna(0)
    fig4=px.imshow(heat_pivot,color_continuous_scale="Blues",
        title="Intensite des creations (plus c-est fonce = plus c-est eleve)",labels={"color":"Nb creations"})
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=350)
    st.plotly_chart(fig4,use_container_width=True)


def onglet_structure(data, secteurs_choisis):
    st.header("Structure du tissu economique")
    sa=data["stock_actives"]; fj=data["formes_juridiques"]
    sa_f=sa[sa["grand_secteur"].isin(secteurs_choisis)]
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Formes juridiques")
        fj_f=fj[fj["grand_secteur"].isin(secteurs_choisis)]
        fj_g=fj_f.groupby("forme_jur")["nb"].sum().reset_index().sort_values("nb",ascending=False)
        fig=px.pie(fj_g,values="nb",names="forme_jur",title="Repartition par forme juridique",
            hole=0.4,color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition="inside",textinfo="percent+label")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=380)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Taille par effectifs (treemap)")
        ordre={v:i for i,v in enumerate(ORDRE_TAILLE)}
        taille_g=sa_f.groupby("libelle_taille")["nb"].sum().reset_index()
        taille_g["ord"]=taille_g["libelle_taille"].map(ordre).fillna(99)
        taille_g=taille_g.sort_values("ord")
        fig2=px.treemap(taille_g,path=["libelle_taille"],values="nb",
            color="nb",color_continuous_scale="Blues",title="Repartition par taille")
        fig2.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}",textfont_size=11)
        fig2.update_layout(margin=dict(t=40,l=0,r=0,b=0),height=380,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2,use_container_width=True)
    st.divider()
    st.subheader("Courbe de Pareto - Concentration sectorielle")
    sa_g=sa_f.groupby("grand_secteur")["nb"].sum().reset_index().sort_values("nb",ascending=False)
    sa_g["cumul_pct"]=sa_g["nb"].cumsum()/sa_g["nb"].sum()*100
    fig3=go.Figure()
    fig3.add_bar(x=sa_g["grand_secteur"],y=sa_g["nb"],
        marker_color=[COLOR_MAP.get(s,"#7f8c8d") for s in sa_g["grand_secteur"]],name="Nb actives",yaxis="y")
    fig3.add_scatter(x=sa_g["grand_secteur"],y=sa_g["cumul_pct"],name="Cumul %",
        mode="lines+markers",line=dict(color="#e74c3c",width=2),yaxis="y2")
    fig3.add_hline(y=80,line_dash="dash",line_color="#e74c3c",annotation_text="80%",yref="y2")
    fig3.update_layout(title="Pareto : quels secteurs representent 80% des entreprises ?",
        yaxis=dict(title="Nb",showgrid=False),
        yaxis2=dict(title="Cumul %",overlaying="y",side="right",range=[0,110],showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h",yanchor="bottom",y=1.02),xaxis=dict(tickangle=20,showgrid=False))
    st.plotly_chart(fig3,use_container_width=True)
    st.divider()
    st.subheader("Top 20 divisions NAF les plus representees")
    naf_d=data["naf_detail"]
    top20=naf_d[naf_d["grand_secteur"].isin(secteurs_choisis)].nlargest(20,"nb")
    fig4=px.bar(top20,x="nb",y="div_naf",orientation="h",color="grand_secteur",
        color_discrete_map=COLOR_MAP,title="Top 20 divisions NAF",
        labels={"div_naf":"Code NAF","nb":"Nb actives","grand_secteur":"Secteur"})
    fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",xaxis=dict(showgrid=False))
    st.plotly_chart(fig4,use_container_width=True)

def onglet_survie(data):
    st.header("Survie & longevite des entreprises")
    st.caption("Taux de survie = % d-entreprises encore actives apres N annees (proxy via etat administratif actuel).")
    df_s=data["survie"]
    if df_s.empty: st.warning("Donnees de survie non disponibles."); return
    col1,col2,col3=st.columns(3)
    for duree,col in [(1,col1),(3,col2),(5,col3)]:
        d=df_s[df_s["duree_ans"]==duree]
        if not d.empty: col.metric(f"Survie a {duree} an{'s' if duree>1 else ''}",f"{d['taux_survie'].mean():.1f}%")
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Heatmap survie : cohorte x duree")
        pivot=df_s.pivot(index="annee_creation",columns="duree_ans",values="taux_survie")
        fig=px.imshow(pivot,color_continuous_scale="RdYlGn",
            title="Taux de survie (%) par cohorte et duree",
            labels={"color":"Survie %","x":"Duree (ans)","y":"Annee creation"},zmin=0,zmax=100)
        fig.update_traces(texttemplate="%{z:.0f}%",textfont_size=10)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=420)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Courbe de survie moyenne")
        sa=df_s.groupby("duree_ans")["taux_survie"].mean().reset_index()
        fig2=go.Figure()
        fig2.add_scatter(x=sa["duree_ans"],y=sa["taux_survie"],mode="lines+markers+text",
            text=sa["taux_survie"].map(lambda x:f"{x:.1f}%"),textposition="top center",
            line=dict(color="#3498db",width=3),marker=dict(size=10),
            fill="tozeroy",fillcolor="rgba(52,152,219,0.15)")
        fig2.update_layout(title="Taux de survie moyen toutes cohortes",
            xaxis=dict(title="Duree (ans)",showgrid=False),
            yaxis=dict(title="Survie %",range=[0,105],showgrid=False),
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",height=420)
        st.plotly_chart(fig2,use_container_width=True)
    st.subheader("Evolution du taux de survie a 3 ans selon l-annee de creation")
    s3=df_s[df_s["duree_ans"]==3].sort_values("annee_creation")
    if not s3.empty:
        fig3=px.line(s3,x="annee_creation",y="taux_survie",markers=True,
            title="Survie a 3 ans des entreprises creees entre 2010 et 2020",
            labels={"annee_creation":"Annee creation","taux_survie":"Survie %"})
        fig3.add_hline(y=s3["taux_survie"].mean(),line_dash="dash",
            annotation_text=f"Moyenne {s3['taux_survie'].mean():.1f}%")
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),yaxis=dict(showgrid=False))
        st.plotly_chart(fig3,use_container_width=True)


def onglet_carte(data, secteurs_choisis):
    st.header("Carte - Repartition geographique par departement")
    dept=data["departements"]
    dept_f=dept[dept["grand_secteur"].isin(secteurs_choisis)].copy()
    col1,col2=st.columns([2,1])
    with col1:
        mode=st.radio("Afficher",["Nombre d-etablissements","Densite sectorielle (%)"],horizontal=True)
    with col2:
        secteur_focus=st.selectbox("Focus secteur",["Tous"]+sorted(secteurs_choisis))
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
    fig.add_scattermapbox(
        lat=map_data["lat"],lon=map_data["lon"],mode="markers",
        marker=go.scattermapbox.Marker(
            size=map_data["valeur"].apply(lambda v:max(8,min(40,v/vmax*40)) if vmax else 10),
            color=map_data["valeur"],colorscale="Viridis",showscale=True,
            colorbar=dict(title=titre,thickness=12),opacity=0.85),
        text=map_data["texte"],hoverinfo="text")
    fig.update_layout(
        mapbox=dict(style="carto-positron",center=dict(lat=46.5,lon=2.5),zoom=4.8),
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
        st.subheader("Mix sectoriel des 15 plus grands departements")
        top15=map_data.nlargest(15,"valeur")["code_dept"].tolist()
        dt=dept_f[dept_f["code_dept"].isin(top15)].copy()
        dt["nom"]=dt["code_dept"].map(DEPT_NOM).fillna(dt["code_dept"])
        dt_g=dt.groupby(["nom","grand_secteur"])["nb_etablissements"].sum().reset_index()
        fig2=px.bar(dt_g,x="nom",y="nb_etablissements",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,labels={"nom":"Dept","nb_etablissements":"Nb etabl.","grand_secteur":"Secteur"})
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=45,showgrid=False),legend=dict(orientation="h",yanchor="bottom",y=1.02))
        st.plotly_chart(fig2,use_container_width=True)

NAF_CHANGEMENTS = [
    ("01","Culture et prod. animale","01","Production agricole","Recode"),
    ("02","Sylviculture","02","Sylviculture","Identique"),
    ("03","Peche, aquaculture","03","Peche, aquaculture","Identique"),
    ("10","Industries alimentaires","10","Industries alimentaires","Identique"),
    ("14","Articles habillement","14","Articles habillement","Identique"),
    ("26","Fab. produits electroniques","26","Electronique","Recode"),
    ("28","Fab. machines","28","Machines","Identique"),
    ("29","Ind. automobile","29","Automobile","Identique"),
    ("38","Gestion dechets","38","Gestion dechets","Recode"),
    ("41","Construction batiments","41","Construction batiments","Identique"),
    ("42","Genie civil","42","Genie civil","Identique"),
    ("43","Travaux specialises","43","Travaux specialises","Identique"),
    ("45","Commerce auto","45","Commerce auto","Identique"),
    ("46","Commerce gros","46","Commerce gros","Identique"),
    ("47","Commerce detail","47","Commerce detail","Identique"),
    ("49","Transports terrestres","49","Transports terrestres","Identique"),
    ("55","Hebergement","55","Hebergement","Identique"),
    ("56","Restauration","56","Restauration","Identique"),
    ("58","Edition","58","Edition","Identique"),
    ("61","Telecommunications","61","Telecommunications","Identique"),
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
    ("85","Enseignement","85","Enseignement","Identique"),
    ("86","Act. sante humaine","86","Sante humaine","Recode"),
    ("87","Hebergement medico","87","Hebergement medico","Identique"),
    ("88","Action sociale","88","Action sociale","Identique"),
    ("90","Arts, spectacles","90","Arts, spectacles","Identique"),
    ("93","Sports, loisirs","93","Sports, loisirs","Identique"),
    ("95","Reparation","95","Reparation","Identique"),
    ("96","Services perso","96","Services perso","Identique"),
]
COULEURS_NAF={"Identique":"#27ae60","Recode":"#f39c12","Fusion":"#e74c3c","Division":"#2980b9"}

def onglet_naf(data):
    st.header("NAF 2008 -> NAF 2025 - Impact de la nouvelle nomenclature")
    st.caption("La NAF 2025 entre en vigueur au 1er janvier 2027. Elle remplace la NAF rev.2 (2008).")
    df_ch=pd.DataFrame(NAF_CHANGEMENTS,columns=["div_2008","lib_2008","div_2025","lib_2025","type"])
    naf_d=data["naf_detail"].copy()
    naf_d["div_naf"]=naf_d["div_naf"].astype(str).str.zfill(2)
    df_ch["div_2008"]=df_ch["div_2008"].astype(str).str.zfill(2)
    df_ch=df_ch.merge(naf_d.groupby("div_naf")["nb"].sum().reset_index().rename(columns={"div_naf":"div_2008","nb":"nb_entreprises"}),on="div_2008",how="left").fillna({"nb_entreprises":0})
    df_ch["nb_entreprises"]=df_ch["nb_entreprises"].astype(int)
    total=len(df_ch); identiques=(df_ch["type"]=="Identique").sum(); recodes=(df_ch["type"]=="Recode").sum(); fusions=(df_ch["type"]=="Fusion").sum()
    nb_imp=df_ch[df_ch["type"]!="Identique"]["nb_entreprises"].sum(); nb_tot=df_ch["nb_entreprises"].sum()
    pct_imp=nb_imp/nb_tot*100 if nb_tot else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Divisions",total); c2.metric("Identiques",f"{identiques} ({identiques/total*100:.0f}%)")
    c3.metric("Recodes",f"{recodes} ({recodes/total*100:.0f}%)")
    c4.metric("Fusions",fusions); c5.metric("Entreprises impactees",fmt(nb_imp),f"{pct_imp:.1f}% du total")
    st.divider()
    col1,col2=st.columns(2)
    with col1:
        d_types=df_ch.groupby("type").agg(nb_div=("div_2008","count"),nb_ent=("nb_entreprises","sum")).reset_index()
        fig=px.treemap(d_types,path=["type"],values="nb_ent",color="type",color_discrete_map=COULEURS_NAF,
            title="Entreprises concernees par type de changement",custom_data=["nb_div"])
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f} entreprises<br>%{customdata[0]} divisions",textfont_size=12)
        fig.update_layout(margin=dict(t=40,l=0,r=0,b=0),height=350,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        df_imp=df_ch[df_ch["type"]!="Identique"].nlargest(15,"nb_entreprises")
        fig2=px.bar(df_imp,x="nb_entreprises",y="lib_2008",orientation="h",color="type",
            color_discrete_map=COULEURS_NAF,title="Top 15 divisions impactees",
            labels={"lib_2008":"Division 2008","nb_entreprises":"Nb entreprises","type":"Type"})
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",height=350,xaxis=dict(showgrid=False))
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
    st.dataframe(df_aff.style.map(lambda v:f"background-color:{COULEURS_NAF.get(v,'#95a5a6')}33;font-weight:bold",subset=["Type"]),
        use_container_width=True,height=400,hide_index=True)
    st.caption(f"{len(df_aff)} divisions affichees")


def main():
    st.set_page_config(page_title="Dashboard SIRENE",page_icon="",layout="wide",initial_sidebar_state="expanded")
    st.markdown("<style>.block-container{padding-top:1.5rem}[data-testid='metric-container']{background:rgba(255,255,255,0.04);border-radius:8px;padding:12px 16px}</style>",unsafe_allow_html=True)
    data,manquants=charger_donnees()
    if data is None:
        st.error(f"Fichiers manquants dans data/ : {', '.join(manquants)}")
        st.code("python prep_data.py",language="bash")
        st.info("Ce script telecharge les donnees SIRENE et genere les agregats. Duree : ~15 min.")
        return
    st.sidebar.title("Dashboard SIRENE")
    st.sidebar.caption("Base SIRENE - data.gouv.fr")
    st.sidebar.divider()
    all_secteurs=sorted(data["creations_mensuel"]["grand_secteur"].dropna().unique().tolist())
    secteurs_choisis=st.sidebar.multiselect("Secteurs a analyser",all_secteurs,
        default=[s for s in all_secteurs if s!="Autres"])
    if not secteurs_choisis:
        st.sidebar.warning("Selectionnez au moins un secteur."); return
    st.sidebar.divider()
    st.sidebar.caption("Source : INSEE / data.gouv.fr | Mise a jour mensuelle")
    tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
        "Vue d-ensemble","Tendances","Structure","Survie","Carte","NAF 2008->2025"])
    with tab1: onglet_vue_ensemble(data)
    with tab2: onglet_tendances(data,secteurs_choisis)
    with tab3: onglet_structure(data,secteurs_choisis)
    with tab4: onglet_survie(data)
    with tab5: onglet_carte(data,secteurs_choisis)
    with tab6: onglet_naf(data)

if __name__=="__main__": main()
