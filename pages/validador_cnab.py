import streamlit as st
import pandas as pd
import zipfile
import os
from io import BytesIO
from src import data_loader
from src import global_var
from src.components import selector
from datetime import datetime
from src.classes.CnabParserFactory import CNABParserFactory
from src.classes.Formater import Formater as fmt
from src.global_var import MAP_OCORRENCIA, MAP_ESPECIE_TITULO

st.title("📄 Leitor de Arquivo CNAB")


uploaded = st.file_uploader("Suba seu arquivo .rem ou .txt", type=["rem", "txt"])

if uploaded is None:
    st.stop()

# ── Parsing ─────────────────────────────────────
linhas = uploaded.read().decode("utf-8").splitlines()

parser = CNABParserFactory.get_parser(linhas)
resultado = parser.parse()

header = resultado["header"]
body = resultado["body"]

df = body["dataframe"]
erros = body["erros"]
trailer_raw = resultado["trailer"]
header_raw = parser.header  

# ── Header ─────────────────────────────────────
st.subheader("📋 Cabeçalho")

col1, col2, col3 = st.columns(3)

col1.metric("Banco", header["banco"])
col2.metric("Nº do Banco", header["numero_banco"])
col3.metric("Data da operação", header["data_operacao"].strftime("%d/%m/%Y"))

col1, col2 = st.columns(2)
col1.metric("Gestora", header["gestora"])

with st.expander("Ver header"):
    st.code(header_raw)

# ── BODY ─────────────────────────────────────
st.subheader(f"📝 Registros")

# ── KPIs ─────────────────────────────────────
st.write("### Identificação de ocorrência")

contagem = df['identificacao_ocorrencia'].value_counts().reset_index()
contagem.columns = ['Código','Quantidade']
contagem['Descrição'] = contagem['Código'].map(MAP_OCORRENCIA)
contagem = contagem[['Código','Descrição','Quantidade']]

# Resumo de Espécies
st.write("### Espécies de Títulos")
contagem_esp = df['especie_titulo'].value_counts().reset_index()
contagem_esp.columns = ['Código','Quantidade']
# Converte código string para int para bater com o MAP_ESPECIE_TITULO
contagem_esp['Descrição'] = contagem_esp['Código'].apply(lambda x: MAP_ESPECIE_TITULO.get(int(x) if str(x).isdigit() else x, "Desconhecido"))
contagem_esp = contagem_esp[['Código','Descrição','Quantidade']]




col1,col2 = st.columns(2)
with col1:
    st.write("**Ocorrências**")
    st.dataframe(contagem, hide_index=True, use_container_width=True)
with col2:
    st.write("**Espécies**")
    st.dataframe(contagem_esp, hide_index=True, use_container_width=True)

st.write("### Resumo de Ocorrências no Arquivo")
col1, col2, col3, col4, col5,col6 = st.columns(6)

col1.metric("Total Títulos", f"{len(df):}")
col2.metric("Valor Nominal Total", fmt.format_br(df['valor_nominal'].sum()))
col3.metric("Valor Pago Total", fmt.format_br(df['valor_pago'].sum()))
col4.metric("Valor Presente Total", fmt.format_br(df['valor_presente'].sum()))
col5.metric("Contagem de Sacados", f"{df['doc_sacado'].nunique():}")
col6.metric("Contagem de Cedentes", f"{df['cedente'].nunique():,}")


# ── Tabela ─────────────────────────────────────

st.dataframe(
    df.style.format({
        'valor_nominal': 'R$ {:,.2f}',
        'valor_pago': 'R$ {:,.2f}',
        'valor_presente': 'R$ {:,.2f}',
        'data_vencimento': fmt.format_cnab_data,
        'doc_cedente': fmt.format_documento,
        'tipo_cedente': fmt.definir_tipo_documento,
        'doc_sacado': fmt.format_documento,
        'tipo_sacado': fmt.definir_tipo_documento,
        'especie_titulo': lambda x: f"{x} - {MAP_ESPECIE_TITULO.get(int(x) if str(x).isdigit() else x, '???')}"
    }),
    use_container_width=True,
    hide_index=True
)

# ── Erros ─────────────────────────────────────
if erros:
    with st.expander(f"⚠️ {len(erros)} erros na leitura"):
        st.write(erros)

# ── Trailer ─────────────────────────────────────
with st.expander("Ver linha trailer"):
    st.code(trailer_raw)