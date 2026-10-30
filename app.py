import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Curso Superior", layout="wide", page_icon="🎁")

@st.cache_data
def carregar_dados(caminho_arquivo):

    xls = pd.ExcelFile(caminho_arquivo)

    abas_estados = [sheet for sheet in xls.sheet_names if "(CV)" not in sheet]

    dados_totais = []

    for estado in abas_estado:
        df_raw = pd.read_excel(xls, sheet_name=estado)

        start_idx = df_raw[df_raw.iloc[:, 0] == "Brasil"].index[0]

        df_estado = df_raw.iloc[start_idx:, [0, 1, 2, 3]].copy()
        df_estado.columns = ["Localidade", "Total", "Homens", "Mulheres"]

        df_estado = df_estado.dropna(subset=["Localidade"])
        df_estado = df_estado[df_estado["Localidade"].astype(str).str.strip() != ""]

        for col in ["Total", "Homem", "Mulher"]:
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
    area_disponiveis_selecionadas = st.sidebar.multiselect(
        "Selecione as Area de conhecimento:",
        options=area_disponiveis,
        default=["Exatas", "Humanas", "Saúde"]
    )

    sexo_disponiveis = df["Sexo"].unique().tolist()
    sexo_disponiveis_selecionadas = st.sidebar.multiselect(
        "Selecione o Sexo:",
        options=sexo_disponiveis,
        default=["Homem", "Mulher"]
    )

    st.title("📊  Pessoas com nível superior completo, por áreas gerais")
    st.markdown("Análise da média de horas semanais dedicadas por pessoas ocupadas de 14 anos ou mais, por sexo.")

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.info("Certifique-se de que o arquivo 'Tabela 1.1.2.xls' está no mesmo diretório do script")