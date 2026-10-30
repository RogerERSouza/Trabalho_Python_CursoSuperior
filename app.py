import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Curso Superior", layout="wide", page_icon="🎁")

@st.cache_data
def carregar_dados(caminho_arquivo):

    xls = pd.ExcelFile(caminho_arquivo)

    abas_estados = [sheet for sheet in xls.sheet_names if "(CV)" not in sheet]

    dados_totais = []

    for estado in abas_estados:
        df_raw = pd.read_excel(xls, sheet_name=estado)

        start_idx = df_raw[df_raw.iloc[:, 0] == "Brasil"].index[0]

        df_estado = df_raw.iloc[start_idx:, [0, 1, 2, 3]].copy()
        df_estado.columns = ["Localidade", "Total", "Homens", "Mulheres"]

        df_estado = df_estado.dropna(subset=["Localidade"])
        df_estado = df_estado[df_estado["Localidade"].astype(str).str.strip() != ""]

        for col in ["Total", "Homens", "Mulheres"]:
            df_estado[col] = pd.to_numeric(df_estado[col], errors="coerce")

        df_estado["estado"] = str(estado)
        dados_totais.append(df_estado)

    df_completo = pd.concat(dados_totais, ignore_index=True)
    return df_completo

caminho_arquivo = r"Tabela_3_Areas_gerais_de_formacao_na_graduacao.xlsx"

try: 
    df = carregar_dados(caminho_arquivo)

    st.sidebar.header("Estados")

    estado_disponiveis = sorted(df["Estado"].unique(), reverse=True)
    estado_selecionado = st.sidebar.selectbox("Selecione o Estado:", estado_disponiveis)

    area_disponiveis = df["Area de conhecimento"].unique().tolist()
    area_selecionadas = st.sidebar.multiselect(
        "Selecione as Area de conhecimento:",
        options=area_disponiveis,
        default=["Exatas", "Humanas", "Saúde"]
    )

    sexo_disponiveis = df["Sexo"].unique().tolist()
    sexo_disponiveis_selecionadas = st.sidebar.multiselect(
        "Selecione o Sexo:",
        options=sexo_disponiveis,
        default=["Homens", "Mulheres"]
    )

    st.title("📊  Pessoas com nível superior completo, por áreas gerais")
    st.markdown("Análise da média de horas semanais dedicadas por pessoas ocupadas de 14 estados ou mais, por sexo.")





    # Filtrar DataFrame com base nas seleções
    df_filtrado = df[(df["estado"] == estado_selecionado) & (df["Localidade"].isin(area_selecionadas))]

    if not df_filtrado.empty:

        st.subheader(f"Dados em Tabela ({estado_selecionado})")
        st.dataframe(df_filtrado[["Localidade", "Total", "Homens", "Mulheres"]].reset_index(drop=True), use_container_width=True)

        st.markdown("---")
        st.subheader("Graficos Comparativos")

        col1, col2 = st.columns(2)


        # ---

        with col1:

            df_melted = df_filtrado.melt(
                id_vars=["Localidade"],
                value_vars=["Homens", "Mulheres"],
                var_name="Sexo",
                value_name="Curso Superior"
            )

            fig_bar = px.bar(
                df_melted,
                x="Localidade",
                y="Curso Superior",
                color="Sexo",
                barmode="group",
                title=f"Quantidade de curso superior por estado ({estado_selecionado})",
                color_discrete_sequence=["#1f77b4", "#e377c2"],
                labels={"Curso Superior": "Quantidade", "Localidade": "Região / UF"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            
        with col2:
            df_historico = df[df["Localidade"].isin(area_selecionadas)]

            fig_line = px.line(
                df_historico,
                x="Area",
                y="Total",
                color="Localidade",
                markers=True,
                title="Evolução Temporal do Total da quantidade de cursos superiores",
                labels={"Total": "Quantidade", "estado": "estado"}
            )
            st.plotly_chart(fig_line, use_container_width=True)
        
    else:
        st.warning("Nenhuma localidade selecionada nos filtros da barra lateral.")

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.info("Certifique-se de que o arquivo 'Tabela_3_Areas_gerais_de_formacao_na_graduacao.xlsx' está no mesmo diretório do script")