from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Curso Superior no Sudeste", page_icon="🎓", layout="wide")

ARQUIVO_DADOS = Path(__file__).parent / "Tabela_3_Areas_gerais_de_formacao_na_graduacao.xlsx"
ESTADOS_SUDESTE = ["Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo"]
AREA_TOTAL = "Total"


@st.cache_data
def carregar_dados(caminho_arquivo: str) -> pd.DataFrame:
    """Lê a planilha do IBGE e a converte para o formato longo do dashboard."""
    bruto = pd.read_excel(caminho_arquivo, sheet_name="Sheet1", header=[1, 2])
    coluna_localidade = bruto.columns[0]
    registros = []

    for _, linha in bruto.iterrows():
        localidade = linha[coluna_localidade]
        if pd.isna(localidade) or str(localidade).startswith("Fonte:"):
            continue

        for area_original, sexo_original in bruto.columns[1:]:
            area = str(area_original).strip()
            sexo = str(sexo_original).strip()
            quantidade = pd.to_numeric(
                linha[(area_original, sexo_original)], errors="coerce"
            )

            if pd.notna(quantidade):
                registros.append(
                    {
                        "Localidade": str(localidade).strip(),
                        "Área": area,
                        "Sexo": sexo,
                        "Quantidade": int(quantidade),
                    }
                )

    return pd.DataFrame(registros)


def formatar_numero(valor: int | float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def percentual_mulheres(dados: pd.DataFrame, area: str) -> float | None:
    filtro = dados[(dados["Área"] == area) & (dados["Sexo"].isin(["Homens", "Mulheres"]))]
    mulheres = filtro.loc[filtro["Sexo"] == "Mulheres", "Quantidade"].sum()
    total = filtro["Quantidade"].sum()
    return (mulheres / total * 100) if total else None


df = carregar_dados(str(ARQUIVO_DADOS))
areas_formacao = [area for area in df["Área"].unique() if area != AREA_TOTAL]

st.sidebar.header("Filtros")
estados_selecionados = st.sidebar.multiselect(
    "Estados do Sudeste",
    options=ESTADOS_SUDESTE,
    default=ESTADOS_SUDESTE,
)
areas_selecionadas = st.sidebar.multiselect(
    "Áreas de formação",
    options=areas_formacao,
    default=areas_formacao,
)
sexos_selecionados = st.sidebar.multiselect(
    "Sexo",
    options=["Homens", "Mulheres"],
    default=["Homens", "Mulheres"],
)
st.sidebar.info(
    "A base não possui ano. Por isso, não há filtro temporal nem gráfico de evolução histórica."
)

st.title("🎓 Ensino Superior e talentos no Sudeste")
st.caption(
    "Pessoas com nível superior completo por estado, área geral de formação e sexo. "
    "Fonte: IBGE - Censo Demográfico."
)

if not estados_selecionados or not areas_selecionadas or not sexos_selecionados:
    st.warning("Selecione pelo menos um estado, uma área e um sexo para visualizar a análise.")
    st.stop()

dados_filtrados = df[
    (df["Localidade"].isin(estados_selecionados))
    & (df["Área"].isin(areas_selecionadas))
    & (df["Sexo"].isin(sexos_selecionados))
].copy()

dados_total_estados = df[
    (df["Localidade"].isin(estados_selecionados))
    & (df["Área"] == AREA_TOTAL)
    & (df["Sexo"] == "Total")
]
total_superior = dados_total_estados["Quantidade"].sum()
maior_estado = (
    dados_total_estados.loc[dados_total_estados["Quantidade"].idxmax()]
    if not dados_total_estados.empty
    else None
)

col1, col2, col3 = st.columns(3)
col1.metric("Pessoas com nível superior completo", formatar_numero(total_superior))
col2.metric("Estados analisados", len(estados_selecionados))
if maior_estado is not None:
    col3.metric(
        "Maior concentração",
        maior_estado["Localidade"],
        formatar_numero(maior_estado["Quantidade"]),
    )

st.divider()
st.subheader("Perguntas de negócio respondidas")

if maior_estado is not None:
    st.markdown(
        f"**1. Distribuição no Sudeste:** nos estados selecionados, há "
        f"**{formatar_numero(total_superior)} pessoas** com nível superior completo. "
        f"**{maior_estado['Localidade']}** possui a maior concentração, com "
        f"**{formatar_numero(maior_estado['Quantidade'])} pessoas**."
    )

st.markdown(
    "**2. Evolução histórica:** não é possível responder com esta planilha, "
    "pois ela não possui coluna de ano nem série temporal."
)

respostas_mulheres = []
for area in areas_formacao:
    percentual = percentual_mulheres(
        df[df["Localidade"].isin(estados_selecionados)], area
    )
    if percentual is not None:
        respostas_mulheres.append(f"**{area}: {percentual:.1f}%**")

st.markdown(
    "**3. Participação feminina:** a base informa pessoas com nível superior completo, "
    "não ingressantes e diplomadas separadamente. Assim, o indicador disponível é a "
    "proporção de mulheres entre os concluintes: " + "; ".join(respostas_mulheres) + "."
)

st.divider()
st.subheader("Proporção de gênero por área")

genero = dados_filtrados.groupby(["Área", "Sexo"], as_index=False)["Quantidade"].sum()
totais_area = (
    genero.groupby("Área", as_index=False)["Quantidade"]
    .sum()
    .rename(columns={"Quantidade": "Total da área"})
)
genero_percentual = genero.merge(totais_area, on="Área")
genero_percentual["Percentual"] = (
    genero_percentual["Quantidade"] / genero_percentual["Total da área"] * 100
)

fig_proporcao = px.bar(
    genero_percentual,
    x="Área",
    y="Percentual",
    color="Sexo",
    barmode="stack",
    text_auto=".1f",
    color_discrete_map={"Homens": "#2563eb", "Mulheres": "#db2777"},
    labels={"Percentual": "Participação (%)", "Área": "Área de formação"},
    title="Participação de homens e mulheres nas áreas selecionadas",
)
fig_proporcao.update_layout(yaxis_range=[0, 100], legend_title_text="Sexo")
st.plotly_chart(fig_proporcao, use_container_width=True)

st.subheader("Quantidade por estado e área")
fig_quantidade = px.bar(
    dados_filtrados,
    x="Localidade",
    y="Quantidade",
    color="Área",
    facet_col="Sexo",
    barmode="group",
    labels={
        "Localidade": "Estado",
        "Quantidade": "Pessoas",
        "Área": "Área de formação",
    },
    title="Pessoas com nível superior completo por estado",
)
fig_quantidade.update_layout(legend_title_text="Área")
st.plotly_chart(fig_quantidade, use_container_width=True)

st.subheader("Dados detalhados")
tabela = (
    dados_filtrados.pivot_table(
        index=["Localidade", "Área"],
        columns="Sexo",
        values="Quantidade",
        aggfunc="sum",
        fill_value=0,
    )
    .reset_index()
)
st.dataframe(tabela, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Contexto para políticas públicas")
st.markdown(
    "A presença feminina em STEM e a formação de profissionais de tecnologia são pontos "
    "centrais para políticas de atração e retenção de talentos no Sudeste."
)

noticia1, noticia2 = st.columns(2)
with noticia1:
    st.markdown("#### Mulheres na ciência e na tecnologia")
    st.markdown("Dados e iniciativas sobre a participação feminina em STEM.")
    st.link_button("Conhecer a UNESCO", "https://www.unesco.org/en/gender-equality/science")
with noticia2:
    st.markdown("#### Mercado de trabalho e qualificação")
    st.markdown("Indicadores oficiais sobre educação, trabalho e população brasileira.")
    st.link_button("Acessar o IBGE Educa", "https://educa.ibge.gov.br/")

