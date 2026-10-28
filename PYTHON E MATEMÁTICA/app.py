import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="População 2010 x 2022", page_icon="📊", layout="wide")

ARQUIVO = "CD2022_Populacao_2010_Compatibilizada_20231222.ods"


@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO, engine="calamine", header=None, skiprows=3)
    df = df.iloc[:, 1:8]
    df.columns = ["UF", "Cod UF", "Cod Munic", "Município", "Pop 2010 (Sinopse)", "Pop 2010 (Compatibilizada)", "Pop 2022"]
    df = df.dropna(subset=["Cod UF", "Município"]).copy()
    df["Cod UF"] = df["Cod UF"].astype(int)
    for c in ["Pop 2010 (Sinopse)", "Pop 2010 (Compatibilizada)", "Pop 2022"]:
        df[c] = df[c].astype(int)
    df["Variação absoluta"] = df["Pop 2022"] - df["Pop 2010 (Compatibilizada)"]
    df["Variação (%)"] = (df["Variação absoluta"] / df["Pop 2010 (Compatibilizada)"] * 100).round(2)
    return df


df = carregar_dados()

st.title("📊 População dos Municípios Brasileiros: 2010 x 2022")
st.caption("Fonte: IBGE, Censo Demográfico 2022 - Primeiros Resultados")

st.sidebar.header("Filtros")
ufs = sorted(df["UF"].unique())
sel_ufs = st.sidebar.multiselect("Estados (UF)", ufs, default=ufs)
busca = st.sidebar.text_input("Buscar município")
top_n = st.sidebar.slider("Quantidade no ranking", 5, 30, 10)

filtrado = df[df["UF"].isin(sel_ufs)]
if busca:
    filtrado = filtrado[filtrado["Município"].str.contains(busca, case=False, na=False)]

if filtrado.empty:
    st.warning("Nenhum município encontrado com os filtros escolhidos.")
    st.stop()

pop10 = filtrado["Pop 2010 (Compatibilizada)"].sum()
pop22 = filtrado["Pop 2022"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Municípios", f"{len(filtrado):,}".replace(",", "."))
c2.metric("População 2010", f"{pop10:,}".replace(",", "."))
c3.metric("População 2022", f"{pop22:,}".replace(",", "."))
c4.metric("Variação", f"{(pop22 - pop10) / pop10 * 100:.2f}%", f"{pop22 - pop10:,}".replace(",", "."))

aba1, aba2, aba3, aba4 = st.tabs(["Por estado", "Ranking", "Distribuição", "Dados"])

with aba1:
    por_uf = filtrado.groupby("UF", as_index=False)[["Pop 2010 (Compatibilizada)", "Pop 2022"]].sum()
    longo = por_uf.melt(id_vars="UF", value_vars=["Pop 2010 (Compatibilizada)", "Pop 2022"], var_name="Ano", value_name="População")
    longo["Ano"] = longo["Ano"].replace({"Pop 2010 (Compatibilizada)": "2010", "Pop 2022": "2022"})
    fig = px.bar(longo, x="UF", y="População", color="Ano", barmode="group", title="População por estado")
    st.plotly_chart(fig, use_container_width=True)

    por_uf["Variação (%)"] = ((por_uf["Pop 2022"] / por_uf["Pop 2010 (Compatibilizada)"] - 1) * 100).round(2)
    por_uf = por_uf.sort_values("Variação (%)", ascending=False)
    fig2 = px.bar(por_uf, x="UF", y="Variação (%)", color="Variação (%)", color_continuous_scale="RdYlGn", title="Variação percentual 2010-2022 por estado")
    st.plotly_chart(fig2, use_container_width=True)

with aba2:
    maiores = filtrado.nlargest(top_n, "Pop 2022").sort_values("Pop 2022")
    fig3 = px.bar(maiores, x="Pop 2022", y="Município", color="UF", orientation="h", title=f"Top {top_n} municípios mais populosos (2022)")
    st.plotly_chart(fig3, use_container_width=True)

    cresc = filtrado.nlargest(top_n, "Variação (%)").sort_values("Variação (%)")
    fig4 = px.bar(cresc, x="Variação (%)", y="Município", color="UF", orientation="h", title=f"Top {top_n} maiores crescimentos (%)")
    st.plotly_chart(fig4, use_container_width=True)

with aba3:
    fig5 = px.histogram(filtrado, x="Variação (%)", nbins=60, title="Distribuição da variação percentual dos municípios")
    st.plotly_chart(fig5, use_container_width=True)

    fig6 = px.box(filtrado, x="UF", y="Variação (%)", title="Variação percentual por estado")
    st.plotly_chart(fig6, use_container_width=True)

    fig7 = px.scatter(
        filtrado,
        x="Pop 2010 (Compatibilizada)",
        y="Pop 2022",
        color="UF",
        hover_name="Município",
        log_x=True,
        log_y=True,
        title="População 2010 x 2022 (escala log)",
    )
    st.plotly_chart(fig7, use_container_width=True)

with aba4:
    st.dataframe(filtrado, use_container_width=True, hide_index=True)
