

@st.cache_data(ttl=86_400, show_spinner="Chargement table NAF...")
def charger_table_correspondance() -> pd.DataFrame:
    if CHEMIN_TABLE.exists():
        return pd.read_parquet(CHEMIN_TABLE)
    DATA_DIR.mkdir(exist_ok=True)
    df_raw = _telecharger_table_insee()
    if not df_raw.empty:
        df = _normaliser_table_insee(df_raw)
    else:
        df = _construire_table_synthetique()
    df = _enrichir_table(df)
    df.to_parquet(CHEMIN_TABLE, index=False)
    return df


def _normaliser_table_insee(df_raw: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    for col in df_raw.columns:
        col_lower = col.lower().replace(" ", "_")
        if "2008" in col_lower and "code" in col_lower: col_map[col] = "code_2008"
        elif "2008" in col_lower and ("lib" in col_lower or "intit" in col_lower): col_map[col] = "lib_2008"
        elif "2025" in col_lower and "code" in col_lower: col_map[col] = "code_2025"
        elif "2025" in col_lower and ("lib" in col_lower or "intit" in col_lower): col_map[col] = "lib_2025"
        elif "type" in col_lower or "nature" in col_lower: col_map[col] = "type_raw"
    df = df_raw.rename(columns=col_map)
    for col in ["code_2008", "lib_2008", "code_2025", "lib_2025"]:
        if col not in df.columns: df[col] = ""
    return df


def _enrichir_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["code_2008"] = df["code_2008"].astype(str).str.strip().str.replace("_", ".")
    df["code_2025"] = df["code_2025"].astype(str).str.strip().str.replace("_", ".")

    def extraire_groupe(code):
        match = re.match(r"^(\d{2})[.\-]?(\d{2})", str(code).strip())
        return f"{match.group(1)}.{match.group(2)}" if match else str(code)[:4]

    df["groupe_2008"] = df["code_2008"].apply(extraire_groupe)
    df["groupe_2025"] = df["code_2025"].apply(extraire_groupe)

    def code_vers_section(code):
        try:
            div = int(str(code).replace(".", "")[:2])
            for lettre, (deb, fin) in {
                "A": (1,3), "B": (5,9), "C": (10,33), "D": (35,35), "E": (36,39),
                "F": (41,43), "G": (45,47), "H": (49,53), "I": (55,56),
                "J": (58,63), "K": (64,66), "L": (68,68), "M": (69,75),
                "N": (77,82), "O": (84,84), "P": (85,85), "Q": (86,88),
                "R": (90,93), "S": (94,96), "T": (97,98), "U": (99,99),
            }.items():
                if deb <= div <= fin: return lettre
        except Exception: pass
        return "?"

    df["section_2008"] = df["groupe_2008"].apply(code_vers_section)
    df["section_2025"] = df["groupe_2025"].apply(code_vers_section)
    df["lib_section_2008"] = df["section_2008"].map(SECTIONS_NAF).fillna("Inconnu")

    if "type" not in df.columns:
        comptage_2008 = df.groupby("groupe_2008")["groupe_2025"].nunique()
        comptage_2025 = df.groupby("groupe_2025")["groupe_2008"].nunique()
        def classifier_type(row):
            n_dest = comptage_2008.get(row["groupe_2008"], 1)
            n_src = comptage_2025.get(row["groupe_2025"], 1)
            if row["groupe_2008"] == row["groupe_2025"]:
                return "1->1 Identique" if row.get("lib_2008","") == row.get("lib_2025","") else "1->1 Recode"
            elif n_src > 1 and n_dest == 1: return "N->1 Fusion"
            elif n_dest > 1 and n_src == 1: return "1->N Division"
            else: return "Rearrangement"
        df["type"] = df.apply(classifier_type, axis=1)
    else:
        df["type"] = df["type"].fillna("1->1 Identique")
    return df


def enrichir_avec_sirene(df_corr: pd.DataFrame, df_naf_sirene: pd.DataFrame) -> pd.DataFrame:
    if df_naf_sirene.empty:
        df_corr["nb_entreprises_2008"] = 0
        return df_corr
    df_grp = df_naf_sirene.copy()
    df_grp["groupe"] = df_grp["section_naf"].str[:4].str.replace(r"(\d{2})(\d{2})", r"\1.\2", regex=True)
    df_grp = df_grp.groupby("groupe")["nb_entreprises"].sum().reset_index()
    df_grp.columns = ["groupe_2008", "nb_entreprises_2008"]
    df_enrichi = df_corr.merge(df_grp, on="groupe_2008", how="left")
    df_enrichi["nb_entreprises_2008"] = df_enrichi["nb_entreprises_2008"].fillna(0).astype(int)
    return df_enrichi


def plot_sankey(df: pd.DataFrame, section_filtre: str = "Toutes") -> go.Figure:
    df_f = df.copy()
    if section_filtre != "Toutes":
        df_f = df_f[df_f["section_2008"] == section_filtre]
    df_flux = (
        df_f.groupby(["groupe_2008","lib_2008","groupe_2025","lib_2025","type"])
        .agg(nb=("nb_entreprises_2008","sum")).reset_index()
    )
    top_src = df_flux.groupby("groupe_2008")["nb"].sum().nlargest(30).index
    df_flux = df_flux[df_flux["groupe_2008"].isin(top_src)]
    if df_flux.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee pour cette section", showarrow=False)
        return fig
    labels_src = [f"{r['groupe_2008']} - {str(r['lib_2008'])[:35]}" for _, r in df_flux.iterrows()]
    labels_dst = [f"{r['groupe_2025']} - {str(r['lib_2025'])[:35]}" for _, r in df_flux.iterrows()]
    all_labels = list(dict.fromkeys(labels_src + labels_dst))
    label_idx = {l: i for i, l in enumerate(all_labels)}
    type_colors = {
        "1->1 Identique": "rgba(46,204,113,0.5)", "1->1 Recode": "rgba(52,152,219,0.5)",
        "N->1 Fusion": "rgba(230,126,34,0.5)", "1->N Division": "rgba(231,76,60,0.5)",
        "Rearrangement": "rgba(155,89,182,0.5)",
    }
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(pad=15, thickness=15, line=dict(color="white", width=0.5),
                  label=all_labels, color="#2c3e50"),
        link=dict(
            source=[label_idx[l] for l in labels_src],
            target=[label_idx[l] for l in labels_dst],
            value=df_flux["nb"].clip(lower=1).tolist(),
            color=[type_colors.get(t, "rgba(150,150,150,0.4)") for t in df_flux["type"]],
            hovertemplate="<b>%{source.label}</b><br>-> <b>%{target.label}</b><br>Entreprises : %{value:,.0f}<extra></extra>",
        ),
    ))
    fig.update_layout(
        title=f"Flux de correspondance NAF 2008 -> NAF 2025" + (f" - Section {section_filtre}" if section_filtre != "Toutes" else ""),
        font_size=11, height=600, paper_bgcolor="rgba(0,0,0,0)")
    return fig


@st.cache_data(ttl=86_400, show_spinner="Chargement table NAF...")
def charger_table_correspondance() -> pd.DataFrame:
    if CHEMIN_TABLE.exists():
        return pd.read_parquet(CHEMIN_TABLE)
    DATA_DIR.mkdir(exist_ok=True)
    df_raw = _telecharger_table_insee()
    df = _normaliser_table_insee(df_raw) if not df_raw.empty else _construire_table_synthetique()
    df = _enrichir_table(df)
    df.to_parquet(CHEMIN_TABLE, index=False)
    return df


def _normaliser_table_insee(df_raw: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    for col in df_raw.columns:
        c = col.lower().replace(" ", "_")
        if "2008" in c and "code" in c: col_map[col] = "code_2008"
        elif "2008" in c and ("lib" in c or "intit" in c): col_map[col] = "lib_2008"
        elif "2025" in c and "code" in c: col_map[col] = "code_2025"
        elif "2025" in c and ("lib" in c or "intit" in c): col_map[col] = "lib_2025"
    df = df_raw.rename(columns=col_map)
    for col in ["code_2008","lib_2008","code_2025","lib_2025"]:
        if col not in df.columns: df[col] = ""
    return df


def _enrichir_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["code_2008"] = df["code_2008"].astype(str).str.strip().str.replace("_",".")
    df["code_2025"] = df["code_2025"].astype(str).str.strip().str.replace("_",".")
    def extraire_groupe(code):
        m = re.match(r"^(\d{2})[.\-]?(\d{2})", str(code).strip())
        return f"{m.group(1)}.{m.group(2)}" if m else str(code)[:4]
    df["groupe_2008"] = df["code_2008"].apply(extraire_groupe)
    df["groupe_2025"] = df["code_2025"].apply(extraire_groupe)
    def vers_section(code):
        try:
            d = int(str(code).replace(".","")[:2])
            for l,(a,b) in {"A":(1,3),"B":(5,9),"C":(10,33),"D":(35,35),"E":(36,39),
                "F":(41,43),"G":(45,47),"H":(49,53),"I":(55,56),"J":(58,63),
                "K":(64,66),"L":(68,68),"M":(69,75),"N":(77,82),"O":(84,84),
                "P":(85,85),"Q":(86,88),"R":(90,93),"S":(94,96),"T":(97,98),"U":(99,99)}.items():
                if a <= d <= b: return l
        except: pass
        return "?"
    df["section_2008"] = df["groupe_2008"].apply(vers_section)
    df["section_2025"] = df["groupe_2025"].apply(vers_section)
    df["lib_section_2008"] = df["section_2008"].map(SECTIONS_NAF).fillna("Inconnu")
    if "type" not in df.columns:
        c2008 = df.groupby("groupe_2008")["groupe_2025"].nunique()
        c2025 = df.groupby("groupe_2025")["groupe_2008"].nunique()
        def classify(row):
            nd = c2008.get(row["groupe_2008"],1); ns = c2025.get(row["groupe_2025"],1)
            if row["groupe_2008"]==row["groupe_2025"]:
                return "1->1 Identique" if row.get("lib_2008","")==row.get("lib_2025","") else "1->1 Recode"
            elif ns>1 and nd==1: return "N->1 Fusion"
            elif nd>1 and ns==1: return "1->N Division"
            return "Rearrangement"
        df["type"] = df.apply(classify, axis=1)
    else:
        df["type"] = df["type"].fillna("1->1 Identique")
    return df


def enrichir_avec_sirene(df_corr, df_naf):
    if df_naf.empty:
        df_corr["nb_entreprises_2008"] = 0; return df_corr
    dg = df_naf.copy()
    dg["groupe"] = dg["section_naf"].str[:4].str.replace(r"(\d{2})(\d{2})",r"\1.\2",regex=True)
    dg = dg.groupby("groupe")["nb_entreprises"].sum().reset_index()
    dg.columns = ["groupe_2008","nb_entreprises_2008"]
    df = df_corr.merge(dg, on="groupe_2008", how="left")
    df["nb_entreprises_2008"] = df["nb_entreprises_2008"].fillna(0).astype(int)
    return df


def plot_sankey(df, section_filtre="Toutes"):
    df_f = df[df["section_2008"]==section_filtre].copy() if section_filtre!="Toutes" else df.copy()
    flux = df_f.groupby(["groupe_2008","lib_2008","groupe_2025","lib_2025","type"]).agg(nb=("nb_entreprises_2008","sum")).reset_index()
    top = flux.groupby("groupe_2008")["nb"].sum().nlargest(30).index
    flux = flux[flux["groupe_2008"].isin(top)]
    if flux.empty:
        fig=go.Figure(); fig.add_annotation(text="Aucune donnee",showarrow=False); return fig
    lsrc=[f"{r['groupe_2008']} - {str(r['lib_2008'])[:35]}" for _,r in flux.iterrows()]
    ldst=[f"{r['groupe_2025']} - {str(r['lib_2025'])[:35]}" for _,r in flux.iterrows()]
    all_l=list(dict.fromkeys(lsrc+ldst)); idx={l:i for i,l in enumerate(all_l)}
    tc={"1->1 Identique":"rgba(46,204,113,0.5)","1->1 Recode":"rgba(52,152,219,0.5)",
        "N->1 Fusion":"rgba(230,126,34,0.5)","1->N Division":"rgba(231,76,60,0.5)","Rearrangement":"rgba(155,89,182,0.5)"}
    fig=go.Figure(go.Sankey(arrangement="snap",
        node=dict(pad=15,thickness=15,line=dict(color="white",width=0.5),label=all_l,color="#2c3e50"),
        link=dict(source=[idx[l] for l in lsrc],target=[idx[l] for l in ldst],
            value=flux["nb"].clip(lower=1).tolist(),
            color=[tc.get(t,"rgba(150,150,150,0.4)") for t in flux["type"]],
            hovertemplate="<b>%{source.label}</b><br>-> %{target.label}<br>%{value:,.0f}<extra></extra>")))
    fig.update_layout(title=f"Flux NAF 2008 -> 2025"+(f" - {section_filtre}" if section_filtre!="Toutes" else ""),
        font_size=11,height=600,paper_bgcolor="rgba(0,0,0,0)")
    return fig


def plot_types_changement(df):
    dt=df.groupby("type").agg(nb_groupes=("groupe_2008","nunique"),nb_entreprises=("nb_entreprises_2008","sum")).reset_index().sort_values("nb_entreprises",ascending=False)
    fig=go.Figure()
    fig.add_trace(go.Bar(x=dt["type"],y=dt["nb_entreprises"],name="Entreprises",
        marker_color=[COLOR_TYPE.get(t,"#95a5a6") for t in dt["type"]],
        text=dt["nb_entreprises"].apply(lambda x:f"{x:,.0f}".replace(",",".")),
        textposition="outside",hovertemplate="<b>%{x}</b><br>%{y:,.0f} entreprises<extra></extra>"))
    fig.update_layout(title="Entreprises impactees par type de changement NAF",
        xaxis_title="Type",yaxis_title="Nb entreprises",
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",showlegend=False,
        yaxis=dict(showgrid=False),xaxis=dict(showgrid=False))
    return fig


def plot_secteurs_avant_apres(df):
    av=df.groupby("section_2008")["groupe_2008"].nunique().reset_index().rename(columns={"section_2008":"section","groupe_2008":"nb_codes"})
    av["version"]="NAF 2008"; av["lib"]=av["section"].map(SECTIONS_NAF).fillna("Inconnu")
    ap=df.groupby("section_2025")["groupe_2025"].nunique().reset_index().rename(columns={"section_2025":"section","groupe_2025":"nb_codes"})
    ap["version"]="NAF 2025"; ap["lib"]=ap["section"].map(SECTIONS_NAF).fillna("Inconnu")
    dc=pd.concat([av,ap]).sort_values(["section","version"])
    fig=px.bar(dc,x="lib",y="nb_codes",color="version",barmode="group",
        color_discrete_map={"NAF 2008":"#3498db","NAF 2025":"#e74c3c"},
        title="Nombre de groupes par section : NAF 2008 vs NAF 2025",
        labels={"lib":"Section","nb_codes":"Nb groupes","version":"Nomenclature"},text="nb_codes")
    fig.update_traces(textposition="outside")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=45,showgrid=False),yaxis=dict(showgrid=False),
        legend=dict(orientation="h",yanchor="bottom",y=1.02))
    return fig


def afficher_tableau_correspondance(df, recherche=""):
    da=df[["groupe_2008","lib_2008","section_2008","groupe_2025","lib_2025","section_2025","type","nb_entreprises_2008"]].drop_duplicates(subset=["groupe_2008","groupe_2025"]).copy()
    da.columns=["Groupe 2008","Libelle 2008","Section 2008","Groupe 2025","Libelle 2025","Section 2025","Type","Nb entreprises"]
    da["Nb entreprises"]=da["Nb entreprises"].apply(lambda x:f"{int(x):,}".replace(",","."') if x>0 else "-")
    if recherche:
        mask=(da["Groupe 2008"].str.contains(recherche,case=False,na=False)
             |da["Libelle 2008"].str.contains(recherche,case=False,na=False)
             |da["Groupe 2025"].str.contains(recherche,case=False,na=False)
             |da["Libelle 2025"].str.contains(recherche,case=False,na=False))
        da=da[mask]
    def coloriser(val):
        c={"1->1 Identique":"background-color:#d5f5e3","1->1 Recode":"background-color:#d6eaf8",
           "N->1 Fusion":"background-color:#fdebd0","1->N Division":"background-color:#fadbd8",
           "Rearrangement":"background-color:#e8daef"}
        return c.get(val,"")
    st.dataframe(da.style.applymap(coloriser,subset=["Type"]),use_container_width=True,height=400)
    st.caption(f"{len(da):,} correspondances affichees")


def afficher_onglet_naf(df_naf_sirene: pd.DataFrame):
    st.subheader("Comparaison NAF 2008 (rev.2) -> NAF 2025")
    st.caption("La NAF 2025 entre en vigueur au 1er janvier 2027.")
    with st.spinner("Chargement table de correspondance INSEE..."):
        df_corr = charger_table_correspondance()
    if df_corr.empty:
        st.error("Impossible de charger la table de correspondance.")
        return
    df_corr = enrichir_avec_sirene(df_corr, df_naf_sirene)
    nb_2008=df_corr["groupe_2008"].nunique(); nb_2025=df_corr["groupe_2025"].nunique()
    nb_div=df_corr[df_corr["type"]=="1->N Division"]["groupe_2008"].nunique()
    nb_fus=df_corr[df_corr["type"]=="N->1 Fusion"]["groupe_2025"].nunique()
    nb_id=df_corr[df_corr["type"]=="1->1 Identique"]["groupe_2008"].nunique()
    pct=round((nb_2008-nb_id)/nb_2008*100,1) if nb_2008 else 0
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Groupes NAF 2008",f"{nb_2008}")
    c2.metric("Groupes NAF 2025",f"{nb_2025}",f"{nb_2025-nb_2008:+d}")
    c3.metric("Divisions (1->N)",f"{nb_div}")
    c4.metric("Fusions (N->1)",f"{nb_fus}")
    c5.metric("% groupes impactes",f"{pct}%")
    st.divider()
    with st.expander("Legende des types de changement"):
        c1,c2=st.columns(2)
        with c1:
            st.markdown("**1->1 Identique** : meme code, meme perimetre")
            st.markdown("**1->1 Recode** : meme code, libelle modifie")
            st.markdown("**N->1 Fusion** : plusieurs anciens codes -> 1 nouveau")
        with c2:
            st.markdown("**1->N Division** : 1 ancien code -> plusieurs nouveaux")
            st.markdown("**Rearrangement** : reorganisation complexe")
    t1,t2,t3,t4=st.tabs(["Sankey","Types de changement","Secteurs avant/apres","Table de correspondance"])
    with t1:
        sects=sorted([s for s in df_corr["section_2008"].dropna().unique() if s in SECTIONS_NAF])
        choix=st.selectbox("Filtrer par section NAF",["Toutes"]+[f"{s} - {SECTIONS_NAF[s]}" for s in sects],key="sankey_sec")
        sc=choix[0] if choix!="Toutes" else "Toutes"
        st.plotly_chart(plot_sankey(df_corr,sc),use_container_width=True)
        st.caption("La largeur des flux est proportionnelle au nombre d'entreprises concernees.")
    with t2:
        st.plotly_chart(plot_types_changement(df_corr),use_container_width=True)
    with t3:
        st.plotly_chart(plot_secteurs_avant_apres(df_corr),use_container_width=True)
    with t4:
        rech=st.text_input("Rechercher un code ou libelle",placeholder="Ex: 62.01, restauration...",key="naf_search")
        tc=sorted(df_corr["type"].dropna().unique().tolist())
        tf=st.multiselect("Filtrer par type",tc,default=tc,key="naf_type")
        sf=st.multiselect("Filtrer par section",sects,default=[],placeholder="Toutes",key="naf_sect")
        df_fil=df_corr[df_corr["type"].isin(tf)]
        if sf: df_fil=df_fil[df_fil["section_2008"].isin(sf)]
        afficher_tableau_correspondance(df_fil,rech)
        csv=df_fil[["groupe_2008","lib_2008","groupe_2025","lib_2025","type","nb_entreprises_2008"]].drop_duplicates().to_csv(index=False,sep=";").encode("utf-8-sig")
        st.download_button("Telecharger la table filtree (CSV)",data=csv,file_name="naf_correspondance.csv",mime="text/csv")
