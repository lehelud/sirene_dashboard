# app.py - Dashboard SIRENE
import warnings
import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
warnings.filterwarnings("ignore")
DATA_DIR = Path("data")

COLOR_MAP = {"Agriculture":"#27ae60","Industrie":"#2980b9","Construction":"#d35400","Commerce / Transport / HCR":"#8e44ad","Services aux entreprises":"#c0392b","Services publics / Sante":"#16a085","Autres":"#95a5a6"}
COLOR_EMP = {"Employeur":"#007ACC","Employeur occasionnel":"#f9a825","Non-employeur / NC":"#b0bec5","Non renseigne":"#eceff1"}
ORDRE_TAILLE = ["Non-employeur / NC","0 sal. au 31/12","1-2","3-5","6-9","10-19","20-49","50-99","100-199","200-249","250-499","500-999","1000-1999","2000-4999","5000-9999","10000+","Non renseigne"]
DEPT_COORDS = {"01":(46.2,5.2),"02":(49.5,3.6),"03":(46.3,3.1),"04":(44.1,6.2),"05":(44.7,6.3),"06":(43.9,7.1),"07":(44.8,4.5),"08":(49.7,4.7),"09":(42.9,1.5),"10":(48.3,4.1),"11":(43.2,2.3),"12":(44.4,2.6),"13":(43.5,5.4),"14":(49.1,-0.4),"15":(45.0,2.6),"16":(45.7,0.2),"17":(45.8,-0.7),"18":(47.1,2.4),"19":(45.4,1.9),"21":(47.4,4.9),"22":(48.3,-3.0),"23":(46.1,2.0),"24":(45.1,0.7),"25":(47.2,6.4),"26":(44.7,5.0),"27":(49.1,1.2),"28":(48.4,1.4),"29":(48.2,-4.0),"30":(44.0,4.2),"31":(43.6,1.4),"32":(43.7,0.6),"33":(44.9,-0.6),"34":(43.6,3.9),"35":(48.1,-1.7),"36":(46.8,1.6),"37":(47.2,0.7),"38":(45.2,5.7),"39":(46.7,5.6),"40":(43.9,-0.8),"41":(47.6,1.3),"42":(45.5,4.2),"43":(45.1,3.9),"44":(47.3,-1.5),"45":(47.9,2.1),"46":(44.5,1.6),"47":(44.4,0.5),"48":(44.5,3.5),"49":(47.4,-0.6),"50":(49.1,-1.3),"51":(49.1,4.1),"52":(48.1,5.1),"53":(48.1,-0.6),"54":(48.7,6.2),"55":(48.9,5.1),"56":(47.9,-2.9),"57":(49.1,6.2),"58":(47.2,3.7),"59":(50.5,3.1),"60":(49.4,2.4),"61":(48.6,0.1),"62":(50.5,2.6),"63":(45.8,3.1),"64":(43.3,-0.4),"65":(43.1,0.2),"66":(42.7,2.6),"67":(48.6,7.6),"68":(47.8,7.3),"69":(45.8,4.8),"70":(47.6,6.2),"71":(46.6,4.5),"72":(48.0,0.2),"73":(45.5,6.4),"74":(46.0,6.4),"75":(48.9,2.3),"76":(49.7,1.1),"77":(48.6,3.0),"78":(48.8,1.8),"79":(46.6,-0.3),"80":(49.9,2.3),"81":(43.9,2.2),"82":(44.0,1.4),"83":(43.4,6.2),"84":(43.9,5.0),"85":(46.7,-1.4),"86":(46.6,0.4),"87":(45.8,1.3),"88":(48.2,6.5),"89":(47.9,3.6),"90":(47.6,6.9),"91":(48.5,2.2),"92":(48.9,2.2),"93":(48.9,2.5),"94":(48.8,2.5),"95":(49.1,2.1),"2A":(41.6,9.0),"2B":(42.3,9.3)}
DEPT_NOM = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-HP","05":"Htes-Alpes","06":"Alpes-Mar.","07":"Ardeche","08":"Ardennes","09":"Ariege","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhone","14":"Calvados","15":"Cantal","16":"Charente","17":"Char.-Maritime","18":"Cher","19":"Correze","21":"Cote-d-Or","22":"Cotes-d-Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drome","27":"Eure","28":"Eure-et-Loir","29":"Finistere","30":"Gard","31":"Hte-Garonne","32":"Gers","33":"Gironde","34":"Herault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isere","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Hte-Loire","44":"Loire-Atl.","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozere","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Hte-Marne","53":"Mayenne","54":"M.-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nievre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dome","64":"Pyr.-Atl.","65":"Htes-Pyr.","66":"Pyr.-Or.","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhone","70":"Hte-Saone","71":"Saone-et-Loire","72":"Sarthe","73":"Savoie","74":"Hte-Savoie","75":"Paris","76":"Seine-Maritime","77":"S.-et-Marne","78":"Yvelines","79":"Deux-Sevres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendee","86":"Vienne","87":"Hte-Vienne","88":"Vosges","89":"Yonne","90":"Ter.-Belfort","91":"Essonne","92":"Hts-de-Seine","93":"Seine-St-Denis","94":"Val-de-Marne","95":"Val-d-Oise","2A":"Corse-du-Sud","2B":"Hte-Corse"}
NAF_CHANGEMENTS = [("01","Culture et prod. animale","01","Production agricole","Recode"),("02","Sylviculture","02","Sylviculture","Identique"),("10","Industries alimentaires","10","Industries alimentaires","Identique"),("26","Fab. produits electroniques","26","Electronique","Recode"),("41","Construction batiments","41","Construction batiments","Identique"),("42","Genie civil","42","Genie civil","Identique"),("43","Travaux specialises","43","Travaux specialises","Identique"),("45","Commerce auto","45","Commerce auto","Identique"),("46","Commerce gros","46","Commerce gros","Identique"),("47","Commerce detail","47","Commerce detail","Identique"),("49","Transports terrestres","49","Transports terrestres","Identique"),("55","Hebergement","55","Hebergement","Identique"),("56","Restauration","56","Restauration","Identique"),("62","Programmation, conseil IT","62","Act. informatiques","Recode"),("63","Services information","62","Act. informatiques","Fusion"),("64","Act. financieres","64","Act. financieres","Identique"),("68","Act. immobilieres","68","Act. immobilieres","Identique"),("69","Juridique, comptabilite","69","Juridique, compta","Identique"),("70","Conseil gestion","70","Conseil gestion","Identique"),("71","Architecture, ingenierie","71","Architecture","Identique"),("72","R&D","72","R&D","Identique"),("73","Publicite","73","Publicite","Identique"),("74","Autres act. specialisees","74","Autres spec.","Recode"),("75","Veterinaire","75","Veterinaire","Identique"),("77","Location","77","Location","Identique"),("78","Emploi","78","Emploi","Identique"),("80","Securite","80","Securite","Identique"),("81","Services batiments","81","Services batiments","Identique"),("82","Services administratifs","82","Services admin.","Recode"),("85","Enseignement","85","Enseignement","Identique"),("86","Act. sante humaine","86","Sante humaine","Recode"),("88","Action sociale","88","Action sociale","Identique"),("90","Arts, spectacles","90","Arts, spectacles","Identique"),("93","Sports, loisirs","93","Sports, loisirs","Identique"),("95","Reparation","95","Reparation","Identique"),("96","Services perso","96","Services perso","Identique")]
COULEURS_NAF = {"Identique":"#27ae60","Recode":"#f39c12","Fusion":"#e74c3c","Division":"#2980b9"}


@st.cache_data(ttl=86_400, show_spinner=False)
def charger_donnees():
    req = ["creations_mensuel","stock_actives","formes_juridiques","employeurs","taille_effectifs","departements","survie","naf_detail"]
    manquants = [n for n in req if not (DATA_DIR/f"{n}.parquet").exists()]
    if manquants: return None, manquants
    return {n: pd.read_parquet(DATA_DIR/f"{n}.parquet") for n in req}, []


def fmt(n): return f"{int(n):,}".replace(",","\u202f")


def graphique(fig, h=400):
    """Style sobre : fond blanc force, textes noirs forces, compatible theme sombre Streamlit."""
    fig.update_layout(
        template="plotly_white",
        height=h,
        margin=dict(t=40, b=30, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#222222", size=12),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    font=dict(size=11, color="#222222"),
                    bgcolor="white"),
        xaxis=dict(showgrid=False, linecolor="#cccccc", linewidth=1,
                   tickfont=dict(color="#222222"), title_font=dict(color="#222222")),
        yaxis=dict(showgrid=False, linecolor="#cccccc", linewidth=1,
                   tickfont=dict(color="#222222"), title_font=dict(color="#222222")),
    )
    # Forcer la couleur sur tous les axes supplementaires (yaxis2, xaxis2, etc.)
    for ax in ['xaxis2','yaxis2','xaxis3','yaxis3']:
        fig.update_layout(**{ax: dict(tickfont=dict(color="#222222"), title_font=dict(color="#222222"))})
    return fig


def page_vue_ensemble(data, sects):
    sa=data["stock_actives"]; cm=data["creations_mensuel"]; emp=data["employeurs"]
    sa_f=sa[sa["grand_secteur"].isin(sects)]; total=sa_f["nb"].sum()
    nb_emp=emp[(emp["grand_secteur"].isin(sects))&(emp["statut_employeur"]=="Employeur")]["nb"].sum()
    annee_courante=datetime.datetime.now().year
    annees=sorted([int(a) for a in cm["annee"].dropna().unique() if int(a)<annee_courante])
    ay=annees[-1] if annees else annee_courante-1
    ay1=annees[-2] if len(annees)>=2 else ay-1
    an=cm[(cm["annee"]==ay)&cm["grand_secteur"].isin(sects)]["nb_creations"].sum()
    an1=cm[(cm["annee"]==ay1)&cm["grand_secteur"].isin(sects)]["nb_creations"].sum()
    delta=(an-an1)/an1*100 if an1 else 0
    an_cur=cm[(cm["annee"]==annee_courante)&cm["grand_secteur"].isin(sects)]["nb_creations"].sum()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entreprises actives",fmt(total))
    c2.metric(f"Creations {ay} (annee complete)",fmt(an),f"{delta:+.1f}% vs {ay1}")
    c3.metric(f"Creations {annee_courante} (en cours)",fmt(an_cur))
    c4.metric("Dont employeurs declares",fmt(nb_emp),f"{nb_emp/total*100:.1f}% — sous-estime")
    st.info("**ESS** : selon la liste officielle ESS France (data.gouv.fr), environ 1,1 million d'organisations relevent de l'ESS (cooperatives, mutuelles, associations, fondations). La variable ESS dans SIRENE est sous-renseignee.")
    st.markdown("---")
    st.subheader("Repartition des entreprises actives par grand secteur")
    st.caption("Chaque rectangle est proportionnel au nombre d'entreprises actives.")
    d=sa_f.groupby("grand_secteur")["nb"].sum().reset_index()
    d["pct"]=(d["nb"]/d["nb"].sum()*100).round(1)
    fig=px.treemap(d,path=["grand_secteur"],values="nb",color="grand_secteur",
        color_discrete_map=COLOR_MAP,custom_data=["pct"])
    fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata[0]:.1f}%",
        textfont_size=12,marker_line_width=2,marker_line_color="#fff")
    fig.update_layout(template="plotly_white",margin=dict(t=10,l=0,r=0,b=0),height=400,paper_bgcolor="white",font=dict(color="#222222"))
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("---")
    st.subheader("Statut employeur declare dans SIRENE")
    st.warning("**Limite de la source** : `trancheEffectifsUniteLegale` dans SIRENE est mise a jour avec plusieurs annees de retard. Le code NN regroupe non-employeurs ET entreprises dont l'effectif n'est pas encore declare. Ces chiffres sous-estiment le nombre reel d'employeurs. Pour les effectifs fiables, se referer aux donnees URSSAF/DSN.")
    st.caption("Part des entreprises actives par statut d'effectif declare dans SIRENE.")
    emp_f=emp[emp["grand_secteur"].isin(sects)].copy()
    ordre_emp=["Employeur","Employeur occasionnel","Non-employeur / NC","Non renseigne"]
    tot_s=emp_f.groupby("grand_secteur")["nb"].sum().rename("tot")
    emp_pct=emp_f.merge(tot_s,on="grand_secteur"); emp_pct["pct"]=emp_pct["nb"]/emp_pct["tot"]*100
    fig2=px.bar(emp_pct,x="pct",y="grand_secteur",color="statut_employeur",
        barmode="stack",orientation="h",color_discrete_map=COLOR_EMP,
        category_orders={"statut_employeur":ordre_emp},
        labels={"pct":"%","grand_secteur":"","statut_employeur":"Statut"})
    fig2.update_layout(xaxis=dict(range=[0,100],ticksuffix="%"))
    graphique(fig2,320); fig2.update_layout(yaxis=dict(showgrid=False))
    st.plotly_chart(fig2,use_container_width=True)

def page_tendances(data, sects):
    cm=data["creations_mensuel"]; cm_f=cm[cm["grand_secteur"].isin(sects)]
    d=cm_f.groupby(["mois","grand_secteur"])["nb_creations"].sum().reset_index()
    d=d[d["mois"]>="2015-01"].sort_values("mois")
    d["mm3"]=d.groupby("grand_secteur")["nb_creations"].transform(lambda x:x.rolling(3,min_periods=1).mean())
    fig=go.Figure()
    for sect in sorted(d["grand_secteur"].unique()):
        ds=d[d["grand_secteur"]==sect]; c=COLOR_MAP.get(sect,"#95a5a6")
        fig.add_scatter(x=ds["mois"],y=ds["nb_creations"],name=sect,mode="lines",
            line=dict(color=c,width=1),opacity=0.2,showlegend=False)
        fig.add_scatter(x=ds["mois"],y=ds["mm3"],name=sect,mode="lines",line=dict(color=c,width=2.5))
    graphique(fig,380)
    fig.update_layout(title="Creations mensuelles (trait epais = moyenne mobile 3 mois)",hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Un pic en janvier est normal : beaucoup d'entrepreneurs immatriculent en debut d'annee.")
    st.markdown("---")
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Y a-t-il des mois plus favorables ?")
        st.caption("Ecart a la moyenne mensuelle, toutes annees confondues.")
        cm2=cm.copy(); cm2["num_mois"]=pd.to_numeric(cm2["mois"].str[-2:],errors="coerce")
        sais=cm2.groupby("num_mois")["nb_creations"].mean().reset_index().dropna()
        mnoms={1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sais["mois_nom"]=sais["num_mois"].map(mnoms); moy=sais["nb_creations"].mean()
        sais["ecart"]=((sais["nb_creations"]-moy)/moy*100).round(1)
        fig2=px.bar(sais,x="mois_nom",y="ecart",
            color=sais["ecart"].apply(lambda x:"Au-dessus" if x>=0 else "En-dessous"),
            color_discrete_map={"Au-dessus":"#007ACC","En-dessous":"#e74c3c"},
            labels={"mois_nom":"","ecart":"Ecart (%)","color":""})
        graphique(fig2,300); fig2.update_layout(showlegend=True)
        st.plotly_chart(fig2,use_container_width=True)
    with col2:
        st.subheader("La dynamique s'accelere-t-elle ?")
        st.caption("Taux de croissance annuel. Annee en cours = partielle.")
        ann=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index()
        ann=ann[ann["annee"]>=2015].sort_values(["grand_secteur","annee"])
        ann["g"]=ann.groupby("grand_secteur")["nb_creations"].pct_change()*100
        ann=ann.dropna(subset=["g"])
        fig3=px.line(ann,x="annee",y="g",color="grand_secteur",color_discrete_map=COLOR_MAP,markers=True,
            labels={"annee":"","g":"Croissance (%)","grand_secteur":"Secteur"})
        fig3.add_hline(y=0,line_dash="dash",line_color="#999999")
        graphique(fig3,300); fig3.update_layout(hovermode="x unified")
        st.plotly_chart(fig3,use_container_width=True)
    st.subheader("Intensite des creations par secteur et par annee")
    st.caption("Plus la case est foncee, plus il y a eu de creations cette annee-la.")
    hg=cm_f.groupby(["annee","grand_secteur"])["nb_creations"].sum().reset_index(); hg=hg[hg["annee"]>=2010]
    pv=hg.pivot(index="grand_secteur",columns="annee",values="nb_creations").fillna(0)
    fig4=px.imshow(pv,color_continuous_scale="Blues",labels={"color":"Nb creations"})
    fig4.update_layout(template="plotly_white",plot_bgcolor="white",paper_bgcolor="white",height=280,
        margin=dict(t=10,b=20,l=10,r=10),font=dict(color="#222222"))
    st.plotly_chart(fig4,use_container_width=True)


def page_structure(data, sects):
    sa=data["stock_actives"]; fj=data["formes_juridiques"]; sa_f=sa[sa["grand_secteur"].isin(sects)]
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Sous quelle forme juridique ?")
        fj_g=fj[fj["grand_secteur"].isin(sects)].groupby("forme_jur")["nb"].sum().reset_index().sort_values("nb",ascending=False)
        fig=px.pie(fj_g,values="nb",names="forme_jur",hole=0.45,
            color_discrete_sequence=["#007ACC","#1AA6A6","#2ecc71","#e74c3c","#9b59b6","#f39c12"])
        fig.update_traces(textposition="inside",textinfo="percent+label",textfont_size=11)
        fig.update_layout(template="plotly_white",paper_bgcolor="white",showlegend=False,height=340,margin=dict(t=10,b=10),font=dict(color="#222222"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Quelle est leur taille ?")
        st.caption("Effectifs declares au siege (StockEtablissement, declarations < 3 ans). Plus representatif que la version precedente.")
        taille=data["taille_effectifs"][data["taille_effectifs"]["grand_secteur"].isin(sects)]
        taille_g=taille.groupby("libelle_taille")["nb"].sum().reset_index()
        ordre={v:i for i,v in enumerate(ORDRE_TAILLE)}
        taille_g["ord"]=taille_g["libelle_taille"].map(ordre).fillna(99)
        taille_g=taille_g.sort_values("ord")
        taille_g["pct"]=(taille_g["nb"]/taille_g["nb"].sum()*100).round(1)
        fig2=px.bar(taille_g,x="nb",y="libelle_taille",orientation="h",
            color="libelle_taille",color_discrete_sequence=px.colors.sequential.Blues[2:],
            text=taille_g["pct"].map(lambda x: f"{x:.1f}%"),
            labels={"libelle_taille":"Tranche","nb":"Nb entreprises"})
        fig2.update_traces(textposition="outside")
        graphique(fig2,420)
        fig2.update_layout(showlegend=False,yaxis=dict(showgrid=False,categoryorder="array",categoryarray=ORDRE_TAILLE[::-1]))
        st.plotly_chart(fig2,use_container_width=True)

    st.markdown("---")
    st.subheader("Top 20 divisions NAF les plus representees")
    st.caption("Code NAF a 2 chiffres. Les 20 activites les plus frequentes.")
    top20=data["naf_detail"][data["naf_detail"]["grand_secteur"].isin(sects)].nlargest(20,"nb")
    fig4=px.bar(top20,x="nb",y="div_naf",orientation="h",color="grand_secteur",
        color_discrete_map=COLOR_MAP,labels={"div_naf":"Division NAF","nb":"Nb actives","grand_secteur":"Secteur"})
    fig4.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
    graphique(fig4,620); fig4.update_layout(yaxis=dict(showgrid=False, tickfont=dict(size=10)), xaxis=dict(showgrid=True, gridcolor="#eeeeee"))
    st.plotly_chart(fig4,use_container_width=True)


def page_survie(data):
    df_s=data["survie"]
    if df_s.empty: st.warning("Donnees de survie non disponibles."); return
    st.caption("Ex : un taux a 3 ans de 65% = 65 entreprises sur 100 encore actives 3 ans apres leur creation. Source : calcul INSEE.")
    c1,c2,c3=st.columns(3)
    for dur,col in [(1,c1),(3,c2),(5,c3)]:
        d=df_s[df_s["duree_ans"]==dur]
        if not d.empty: col.metric(f"Survie moyenne a {dur} an{'s' if dur>1 else ''}",f"{d['taux_survie'].mean():.1f}%")
    st.markdown("---")
    st.subheader("Courbe de survie moyenne")
    st.caption("Toutes cohortes confondues : erosion du taux de survie au fil des annees.")
    sa=df_s.groupby("duree_ans")["taux_survie"].mean().reset_index()
    fig2=go.Figure()
    fig2.add_scatter(x=sa["duree_ans"],y=sa["taux_survie"],mode="lines+markers+text",
        text=sa["taux_survie"].map(lambda x:f"{x:.1f}%"),textposition="top center",
        textfont=dict(color="#333333",size=12),
        line=dict(color="#007ACC",width=3),marker=dict(size=10,color="#007ACC"),
        fill="tozeroy",fillcolor="rgba(0,122,204,.1)")
    fig2.update_layout(template="plotly_white",plot_bgcolor="white",paper_bgcolor="white",font=dict(color="#222222"),
        xaxis=dict(title="Annees apres creation",showgrid=False),
        yaxis=dict(title="% encore actives",range=[0,115],showgrid=False),
        height=380,margin=dict(t=20,b=20,l=8,r=8))
    st.plotly_chart(fig2,use_container_width=True)
    s3=df_s[df_s["duree_ans"]==3].sort_values("annee_creation")
    if not s3.empty:
        st.subheader("Le taux de survie a 3 ans s'ameliore-t-il ?")
        fig3=px.line(s3,x="annee_creation",y="taux_survie",markers=True,
            color_discrete_sequence=["#007ACC"],
            labels={"annee_creation":"Annee de creation","taux_survie":"Survie a 3 ans (%)"})
        fig3.add_hline(y=s3["taux_survie"].mean(),line_dash="dash",line_color="#999999",
            annotation_text=f"Moy. {s3['taux_survie'].mean():.1f}%")
        graphique(fig3,280); st.plotly_chart(fig3,use_container_width=True)


def page_carte(data, sects):
    st.caption("**Nombre d'etablissements** : total des etablissements actifs (sieges + etablissements secondaires) declares dans le departement. **Densite sectorielle (%)** : part du secteur choisi dans le total des etablissements du departement — indique la specialisation economique locale.")
    dept=data["departements"]; dept_f=dept[dept["grand_secteur"].isin(sects)].copy()
    col1,col2=st.columns([2,1])
    with col1: mode=st.radio("Afficher",["Nombre d'etablissements","Densite sectorielle (%)"],horizontal=True,key="carte_mode")
    with col2: sf=st.selectbox("Focus secteur",["Tous"]+sorted(sects),key="carte_sf")
    if "Nombre" in mode:
        md=dept_f.groupby("code_dept")["nb_etablissements"].sum().reset_index() if sf=="Tous" else dept_f[dept_f["grand_secteur"]==sf][["code_dept","nb_etablissements"]].copy()
        md.columns=["code_dept","val"]; titre="Etablissements"
    else:
        md=dept_f.sort_values("nb_etablissements",ascending=False).drop_duplicates("code_dept")[["code_dept","pct_secteur"]].copy() if sf=="Tous" else dept_f[dept_f["grand_secteur"]==sf][["code_dept","pct_secteur"]].copy()
        md.columns=["code_dept","val"]; titre="%"
    md["lat"]=md["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[0])
    md["lon"]=md["code_dept"].map(lambda x:DEPT_COORDS.get(x,(None,None))[1])
    md["nom"]=md["code_dept"].map(DEPT_NOM).fillna(md["code_dept"])
    md=md.dropna(subset=["lat","lon"]); vmax=md["val"].max()
    md["txt"]=md.apply(lambda r:f"<b>{r['nom']}</b><br>{titre}: {r['val']:,.0f}",axis=1)
    fig=go.Figure()
    fig.add_scattermapbox(lat=md["lat"],lon=md["lon"],mode="markers",
        marker=go.scattermapbox.Marker(
            size=md["val"].apply(lambda v:max(7,min(38,v/vmax*38)) if vmax else 8),
            color=md["val"],colorscale="Blues",showscale=True,
            colorbar=dict(title=titre,thickness=10),opacity=0.82),
        text=md["txt"],hoverinfo="text")
    fig.update_layout(mapbox=dict(style="carto-positron",center=dict(lat=46.5,lon=2.5),zoom=4.8),
        margin=dict(l=0,r=0,t=0,b=0),height=500,paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("---")
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Top 10 departements")
        t10=md.nlargest(10,"val")[["nom","code_dept","val"]].copy()
        t10.columns=["Departement","Code","Valeur"]; t10["Valeur"]=t10["Valeur"].map(lambda v:f"{v:,.0f}")
        st.dataframe(t10.reset_index(drop=True),use_container_width=True,hide_index=True)
    with col2:
        st.subheader("Mix sectoriel des 12 plus grands departements")
        top12=md.nlargest(12,"val")["code_dept"].tolist()
        dt=dept_f[dept_f["code_dept"].isin(top12)].copy()
        dt["nom"]=dt["code_dept"].map(DEPT_NOM).fillna(dt["code_dept"])
        dtg=dt.groupby(["nom","grand_secteur"])["nb_etablissements"].sum().reset_index()
        fig2=px.bar(dtg,x="nom",y="nb_etablissements",color="grand_secteur",barmode="stack",
            color_discrete_map=COLOR_MAP,labels={"nom":"","nb_etablissements":"Nb","grand_secteur":"Secteur"})
        graphique(fig2,320); fig2.update_layout(xaxis=dict(tickangle=40,showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)


def page_naf(data):
    st.caption("La NAF classe les entreprises par activite. La refonte de 2025 entraine des recodages au 1/1/2027.")
    df_ch=pd.DataFrame(NAF_CHANGEMENTS,columns=["div_2008","lib_2008","div_2025","lib_2025","type"])
    naf_d=data["naf_detail"].copy(); naf_d["div_naf"]=naf_d["div_naf"].astype(str).str.zfill(2)
    df_ch["div_2008"]=df_ch["div_2008"].astype(str).str.zfill(2)
    df_ch=df_ch.merge(naf_d.groupby("div_naf")["nb"].sum().reset_index().rename(columns={"div_naf":"div_2008","nb":"nb_entreprises"}),on="div_2008",how="left").fillna({"nb_entreprises":0})
    df_ch["nb_entreprises"]=df_ch["nb_entreprises"].astype(int)
    total=len(df_ch); ident=(df_ch["type"]=="Identique").sum(); recod=(df_ch["type"]=="Recode").sum()
    fusio=(df_ch["type"]=="Fusion").sum(); nb_imp=df_ch[df_ch["type"]!="Identique"]["nb_entreprises"].sum()
    pct=nb_imp/df_ch["nb_entreprises"].sum()*100 if df_ch["nb_entreprises"].sum() else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Divisions analysees",total); c2.metric("Code inchange",f"{ident}",f"{ident/total*100:.0f}% des div.")
    c3.metric("Code recode",f"{recod}",f"{recod/total*100:.0f}% des div."); c4.metric("Fusions (2->1)",fusio)
    c5.metric("Entreprises concernees",fmt(nb_imp),f"{pct:.1f}% du total")
    st.markdown("---")
    col1,col2=st.columns(2)
    with col1:
        st.subheader("Entreprises par type de changement")
        dt=df_ch.groupby("type").agg(nb_div=("div_2008","count"),nb_ent=("nb_entreprises","sum")).reset_index()
        fig=px.treemap(dt,path=["type"],values="nb_ent",color="type",color_discrete_map=COULEURS_NAF,custom_data=["nb_div"])
        fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f} entreprises<br>%{customdata[0]} divisions",textfont_size=12)
        fig.update_layout(template="plotly_white",margin=dict(t=10,l=0,r=0,b=0),height=300,paper_bgcolor="white",font=dict(color="#222222"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Divisions les plus impactees")
        di=df_ch[df_ch["type"]!="Identique"].nlargest(12,"nb_entreprises")
        fig2=px.bar(di,x="nb_entreprises",y="lib_2008",orientation="h",color="type",
            color_discrete_map=COULEURS_NAF,labels={"lib_2008":"","nb_entreprises":"Nb","type":"Type"})
        graphique(fig2,300); fig2.update_layout(yaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True)
    st.markdown("---")
    c1,c2,c3=st.columns(3)
    with c1: ft=st.multiselect("Type",df_ch["type"].unique().tolist(),default=df_ch["type"].unique().tolist(),key="naf_type")
    with c2: rech=st.text_input("Rechercher",placeholder="ex: 62, informatique...",key="naf_rech")
    with c3: tri=st.selectbox("Trier par",["Nb entreprises","Division 2008","Type"],key="naf_tri")
    df_a=df_ch[df_ch["type"].isin(ft)].copy()
    if rech:
        m=(df_a["div_2008"].str.contains(rech,case=False)|df_a["lib_2008"].str.contains(rech,case=False)|df_a["lib_2025"].str.contains(rech,case=False))
        df_a=df_a[m]
    if tri=="Nb entreprises": df_a=df_a.sort_values("nb_entreprises",ascending=False)
    elif tri=="Division 2008": df_a=df_a.sort_values("div_2008")
    else: df_a=df_a.sort_values("type")
    df_a["nb_entreprises"]=df_a["nb_entreprises"].map(lambda x:fmt(x))
    df_a.columns=["Div.2008","Libelle 2008","Div.2025","Libelle 2025","Type","Nb entreprises"]
    st.dataframe(df_a.style.map(lambda v:f"color:{COULEURS_NAF.get(v,'#333333')};font-weight:600",subset=["Type"]),
        use_container_width=True,height=420,hide_index=True)
    st.caption(f"{len(df_a)} divisions affichees")


def main():
    st.set_page_config(page_title="Dashboard SIRENE",page_icon="",layout="wide",initial_sidebar_state="expanded")
    data,manquants=charger_donnees()
    if data is None:
        st.error(f"Fichiers manquants : {', '.join(manquants)}. Lancez : python prep_data.py"); return
    st.title("Dashboard SIRENE")
    st.markdown("Source des donnees : [Base SIRENE - INSEE / data.gouv.fr](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/)")
    st.sidebar.header("Navigation")
    page=st.sidebar.radio("Page",
        ["Vue d'ensemble","Tendances","Structure","Survie","Carte","NAF 2008 -> 2025"],
        key="nav_radio")
    st.sidebar.markdown("---")
    st.sidebar.header("Filtres")
    all_s=sorted(data["creations_mensuel"]["grand_secteur"].dropna().unique().tolist())
    sects=st.sidebar.multiselect("Secteurs",all_s,
        default=[s for s in all_s if s!="Autres"],key="sects_filter")
    if not sects: st.sidebar.warning("Selectionnez au moins un secteur."); return
    st.sidebar.markdown("---")
    st.sidebar.caption("Source : INSEE / data.gouv.fr")
    st.sidebar.caption("MAJ mensuelle")
    st.header(page)
    if   page=="Vue d'ensemble":    page_vue_ensemble(data,sects)
    elif page=="Tendances":          page_tendances(data,sects)
    elif page=="Structure":          page_structure(data,sects)
    elif page=="Survie":             page_survie(data)
    elif page=="Carte":              page_carte(data,sects)
    elif page=="NAF 2008 -> 2025":   page_naf(data)


if __name__=="__main__": main()
