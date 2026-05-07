"""
Página Streamlit: Análise de Liquidações.

Permite ao usuário:
  1. Fazer upload de ZIP, CSV ou XLSX com os dados de liquidações
  2. Visualizar KPIs globais (valores de aquisição, vencimento e pagos)
  3. Analisar por Situação do Recebível, Cedente, Sacado
  4. Quebrar por Data de Aquisição e Data de Vencimento
  5. Inspecionar os recebíveis individuais com filtros
"""

import pandas as pd
import numpy as np
import streamlit as st
from src.data_loader import carregar_arquivo, normalizar_colunas, aplicar_aliases, preparar_colunas_datas, preparar_colunas_valores
from src.formatting import fmt_moeda, fmt_numero, fmt_pct

# ── Constantes de colunas ──────────────────────────────────────
COL_DATA_MOV    = "DATA MOVIMENTO"
COL_CEDENTE     = "CEDENTE"
COL_CPF_CNPJ    = "CPF/CNPJ"
COL_OCORRENCIA  = "OCORRENCIA"
COL_SITUACAO    = "SITUACAO DO RECEBIVEL"
COL_DOCUMENTO   = "DOCUMENTO"
COL_SACADO      = "SACADO"
COL_ID          = "ID_RECEBIVEL"
COL_VL_AQUIS    = "VALOR DE AQUISICAO"
COL_VL_VENC     = "VALOR DE VENCIMENTO"
COL_DT_AQUIS    = "DATA DA AQUISICAO"
COL_DT_VENC     = "DATA DE VENCIMENTO"
COL_VL_PAGO     = "VALOR DE PAGO"

COLUNAS_ESPERADAS = [
    COL_DATA_MOV, COL_CEDENTE, COL_CPF_CNPJ, COL_OCORRENCIA,
    COL_SITUACAO, COL_DOCUMENTO, COL_SACADO, COL_ID,
    COL_VL_AQUIS, COL_VL_VENC, COL_DT_AQUIS, COL_DT_VENC, COL_VL_PAGO,
]

# Mapa de aliases: coluna alternativa → coluna canônica usada pela página.
ALIASES_COLUNAS = {
    # Valor de Aquisição
    "VL_AQUISICAO"    : COL_VL_AQUIS,
    "VALOR_AQUISICAO" : COL_VL_AQUIS,
    # Valor de Vencimento / Nominal
    "VALOR_VENCIMENTO": COL_VL_VENC,
    "VALOR_NOMINAL"   : COL_VL_VENC,
    # Valor Pago
    "VALOR_PAGO"      : COL_VL_PAGO,
}

# Colunas de data e valor para preparação automática
_COLUNAS_DATA = [COL_DATA_MOV, COL_DT_AQUIS, COL_DT_VENC]
_COLUNAS_VALOR = [COL_VL_AQUIS, COL_VL_VENC, COL_VL_PAGO]


# INTERFACE


st.title("💰 Análise de Liquidações")
st.markdown("Carregue o arquivo de liquidações para visualizar os indicadores consolidados.")

# ── Upload ─────────────────────────────────────────────────────
arquivo = st.file_uploader(
    "📂 Faça o upload do arquivo de liquidações",
    type=["zip", "csv", "xlsx", "xls"],
    help="Aceita ZIP (com CSVs internos), CSV ou Excel."
)

if arquivo is None:
    st.info("Aguardando arquivo...")
    st.stop()

if st.button("🚀 Processar arquivo", type="primary"):
    # Limpa resultado anterior para forçar repreocessamento limpo
    st.session_state.pop("df_liq", None)
    with st.spinner("Lendo e processando..."):
        try:
            df_raw = carregar_arquivo(arquivo.read(), arquivo.name)
            df_raw = normalizar_colunas(df_raw)
            df_raw = aplicar_aliases(df_raw, ALIASES_COLUNAS)
            df_raw = preparar_colunas_datas(df_raw, _COLUNAS_DATA)
            df_raw = preparar_colunas_valores(df_raw, _COLUNAS_VALOR)
            st.session_state["df_liq"] = df_raw
            st.success(f"✅ {len(df_raw):,} registros carregados.")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
            st.stop()

if "df_liq" not in st.session_state:
    st.stop()

df: pd.DataFrame = st.session_state["df_liq"]

# ── Aviso de colunas ausentes ──────────────────────────────────
ausentes = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
if ausentes:
    st.warning(f"⚠️ Colunas não encontradas no arquivo: `{'`, `'.join(ausentes)}`")


# FILTROS LATERAIS

with st.sidebar:
    st.header("🔎 Filtros")

    # Situação do Recebível
    if COL_SITUACAO in df.columns:
        situacoes = ["Todas"] + sorted(df[COL_SITUACAO].dropna().unique().tolist())
        situacao_sel = st.multiselect("Situação do Recebível", situacoes, default=["Todas"])
    else:
        situacao_sel = ["Todas"]

    # Cedente
    if COL_CEDENTE in df.columns:
        cedentes = ["Todos"] + sorted(df[COL_CEDENTE].dropna().unique().tolist())
        cedente_sel = st.multiselect("Cedente", cedentes, default=["Todos"])
    else:
        cedente_sel = ["Todos"]

    # Período (Data de Vencimento)
    if COL_DT_VENC in df.columns and df[COL_DT_VENC].notna().any():
        dt_min = df[COL_DT_VENC].min().date()
        dt_max = df[COL_DT_VENC].max().date()
        periodo = st.date_input(
            "Período de vencimento",
            value=(dt_min, dt_max),
            min_value=dt_min,
            max_value=dt_max
        )
    else:
        periodo = None

# Aplica filtros
df_f = df.copy()

if "Todas" not in situacao_sel and situacao_sel and COL_SITUACAO in df_f.columns:
    df_f = df_f[df_f[COL_SITUACAO].isin(situacao_sel)]

if "Todos" not in cedente_sel and cedente_sel and COL_CEDENTE in df_f.columns:
    df_f = df_f[df_f[COL_CEDENTE].isin(cedente_sel)]

if periodo and len(periodo) == 2 and COL_DT_VENC in df_f.columns:
    df_f = df_f[
        df_f[COL_DT_VENC].dt.date.between(periodo[0], periodo[1])
    ]


# KPIs GLOBAIS

st.divider()
st.subheader("📊 KPIs Globais")

total_aquis = df_f[COL_VL_AQUIS].sum() if COL_VL_AQUIS in df_f.columns else 0
total_venc  = df_f[COL_VL_VENC].sum()  if COL_VL_VENC  in df_f.columns else 0
total_pago  = df_f[COL_VL_PAGO].sum()  if COL_VL_PAGO  in df_f.columns else 0
n_recebiveis = df_f[COL_ID].nunique()  if COL_ID       in df_f.columns else len(df_f)
n_cedentes  = df_f[COL_CEDENTE].nunique() if COL_CEDENTE in df_f.columns else 0
n_sacados   = df_f[COL_SACADO].nunique()  if COL_SACADO  in df_f.columns else 0

# Retorno sobre aquisição
retorno = (total_pago / total_aquis - 1) if total_aquis else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 Total Aquisição",   fmt_moeda(total_aquis))
c2.metric("📋 Total Vencimento",  fmt_moeda(total_venc))
c3.metric("✅ Total Pago",        fmt_moeda(total_pago))
c4.metric("📈 Retorno s/ Aquis.", fmt_pct(retorno))

c1, c2, c3 = st.columns(3)
c1.metric("🗂️ Recebíveis Únicos", fmt_numero(n_recebiveis))
c2.metric("🏢 Cedentes",          fmt_numero(n_cedentes))
c3.metric("👤 Sacados",           fmt_numero(n_sacados))


# ══════════════════════════════════════════════════════════════
# TABELAS AGRUPADAS
# ══════════════════════════════════════════════════════════════
from src.components.tables import agrupar_e_exibir, agrupar_por_mes

# Specs de agregação para liquidações (3 colunas de valor)
_AGG_LIQ = {
    "Qtd":           (COL_ID,       "count"),
    "Vl_Aquisicao":  (COL_VL_AQUIS, "sum"),
    "Vl_Vencimento": (COL_VL_VENC,  "sum"),
    "Vl_Pago":       (COL_VL_PAGO,  "sum"),
}

_MOEDAS_LIQ = ["Vl_Aquisicao", "Vl_Vencimento", "Vl_Pago"]

# ── Por Situação do Recebível ──
agrupar_e_exibir(
    df_f, COL_SITUACAO, _AGG_LIQ,
    titulo="Por Situação do Recebível", icone="📂",
    sort_col="Vl_Pago",
    col_return_pct=("Retorno", "Vl_Pago", "Vl_Aquisicao"),
    colunas_moeda=_MOEDAS_LIQ,
    colunas_numero=["Qtd"],
    nomes_colunas=["Situação", "Qtd", "Aquisição", "Vencimento", "Pago", "Retorno"],
)

# ── Por Cedente ──
agrupar_e_exibir(
    df_f, COL_CEDENTE, _AGG_LIQ,
    titulo="Por Cedente", icone="🏢",
    sort_col="Vl_Pago",
    col_return_pct=("Retorno", "Vl_Pago", "Vl_Aquisicao"),
    colunas_moeda=_MOEDAS_LIQ,
    colunas_numero=["Qtd"],
    nomes_colunas=["Cedente", "Qtd", "Aquisição", "Vencimento", "Pago", "Retorno"],
)

# ── Por Mês de Vencimento ──
agrupar_por_mes(
    df_f, COL_DT_VENC, _AGG_LIQ,
    titulo="Por Mês de Vencimento", icone="📅",
    colunas_moeda=_MOEDAS_LIQ,
    colunas_numero=["Qtd"],
    nomes_colunas=["Mês Vencimento", "Qtd", "Aquisição", "Vencimento", "Pago"],
)

# ── Por Mês de Aquisição ──
agrupar_por_mes(
    df_f, COL_DT_AQUIS, _AGG_LIQ,
    titulo="Por Mês de Aquisição", icone="📆",
    colunas_moeda=_MOEDAS_LIQ,
    colunas_numero=["Qtd"],
    nomes_colunas=["Mês Aquisição", "Qtd", "Aquisição", "Vencimento", "Pago"],
)


# DETALHAMENTO — TABELA COMPLETA

st.divider()
with st.expander("🔍 Ver tabela completa de recebíveis"):
    # Seleciona apenas colunas conhecidas, sem duplicatas
    colunas_exibir = list(dict.fromkeys(c for c in COLUNAS_ESPERADAS if c in df_f.columns))
    df_exibir = df_f[colunas_exibir].copy()
    df_exibir = df_exibir.loc[:, ~df_exibir.columns.duplicated()]  # guarda-chuva final
    st.dataframe(df_exibir.reset_index(drop=True), use_container_width=True)
    st.caption(f"Exibindo {len(df_f):,} registros.")
