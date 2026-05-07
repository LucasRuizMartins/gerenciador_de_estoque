"""
Página Streamlit: Análise de Aquisições.

Permite ao usuário:
  1. Fazer upload de ZIP, CSV ou XLSX com os dados de aquisições
  2. Visualizar KPIs globais (valores de compra e vencimento)
  3. Analisar por Tipo de Recebível, Sacado, Cedente
  4. Quebrar por mês de Entrada e por mês de Vencimento
  5. Inspecionar os recebíveis individuais com filtros
"""

import pandas as pd
import streamlit as st
from src.data_loader import carregar_arquivo, normalizar_colunas, aplicar_aliases, preparar_colunas_datas, preparar_colunas_valores
from src.formatting import fmt_moeda, fmt_numero, fmt_pct

# ── Constantes de colunas ──────────────────────────────────────
COL_ENTRADA      = "ENTRADA"
COL_DT_VENC      = "DATA VENCIMENTO"
COL_VL_COMPRA    = "VALOR DE COMPRA"
COL_VL_VENC      = "VALOR DE VENCIMENTO"
COL_TIPO         = "TIPO RECEBIVEL"
COL_SACADO       = "NOME SACADO"
COL_CPF_SACADO   = "CPF_CNPJ SACADO"
COL_CPF_CEDENTE  = "CPF_CNPJ_CEDENTE"

COLUNAS_ESPERADAS = [
    COL_ENTRADA, COL_DT_VENC, COL_VL_COMPRA, COL_VL_VENC,
    COL_TIPO, COL_SACADO, COL_CPF_SACADO, COL_CPF_CEDENTE,
]

# ── Aliases de nomes alternativos → nome canônico ──────────────
ALIASES_COLUNAS = {
    # Entrada / Data de Aquisição
    "DATA ENTRADA"      : COL_ENTRADA,
    "DT_ENTRADA"        : COL_ENTRADA,
    "DATA DA AQUISICAO" : COL_ENTRADA,
    "DATA_AQUISICAO"    : COL_ENTRADA,

    # Data de Vencimento
    "DATA DE VENCIMENTO": COL_DT_VENC,
    "DT_VENCIMENTO"     : COL_DT_VENC,
    "DT VENCIMENTO"     : COL_DT_VENC,

    # Valor de Compra / Aquisição
    "VALOR DE AQUISICAO": COL_VL_COMPRA,
    "VALOR_AQUISICAO"   : COL_VL_COMPRA,
    "VL_AQUISICAO"      : COL_VL_COMPRA,
    "VL_COMPRA"         : COL_VL_COMPRA,

    # Valor de Vencimento / Nominal
    "VALOR DE VENCIMENTO": COL_VL_VENC,
    "VALOR_VENCIMENTO"   : COL_VL_VENC,
    "VALOR_NOMINAL"      : COL_VL_VENC,
    "VL_VENCIMENTO"      : COL_VL_VENC,

    # Tipo de Recebível
    "TIPO_RECEBIVEL"     : COL_TIPO,
    "TIPO DE RECEBIVEL"  : COL_TIPO,
    "ESPECIE"            : COL_TIPO,

    # Sacado
    "SACADO"             : COL_SACADO,
    "NOME_SACADO"        : COL_SACADO,

    # CPF/CNPJ Sacado
    "CPF/CNPJ SACADO"    : COL_CPF_SACADO,
    "CPF_CNPJ_SACADO"    : COL_CPF_SACADO,
    "DOC_SACADO"         : COL_CPF_SACADO,

    # CPF/CNPJ Cedente
    "CPF/CNPJ_CEDENTE"   : COL_CPF_CEDENTE,
    "CPF_CNPJ CEDENTE"   : COL_CPF_CEDENTE,
    "DOC_CEDENTE"        : COL_CPF_CEDENTE,
}



# ══════════════════════════════════════════════════════════════
# INTERFACE
# ══════════════════════════════════════════════════════════════

st.title("📥 Análise de Aquisições")
st.markdown("Carregue o arquivo de aquisições para visualizar os indicadores consolidados.")

# ── Upload ─────────────────────────────────────────────────────
arquivo = st.file_uploader(
    "📂 Faça o upload do arquivo de aquisições",
    type=["zip", "csv", "xlsx", "xls"],
    help="Aceita ZIP (com CSVs internos), CSV ou Excel."
)

if arquivo is None:
    st.info("Aguardando arquivo...")
    st.stop()

if st.button("🚀 Processar arquivo", type="primary"):
    st.session_state.pop("df_aquis", None)
    with st.spinner("Lendo e processando..."):
        try:
            df_raw = carregar_arquivo(arquivo.read(), arquivo.name)
            df_raw = normalizar_colunas(df_raw)
            df_raw = aplicar_aliases(df_raw, ALIASES_COLUNAS)
            df_raw = preparar_colunas_datas(df_raw, [COL_ENTRADA, COL_DT_VENC])
            df_raw = preparar_colunas_valores(df_raw, [COL_VL_COMPRA, COL_VL_VENC])
            st.session_state["df_aquis"] = df_raw
            st.success(f"✅ {len(df_raw):,} registros carregados.")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
            st.stop()

if "df_aquis" not in st.session_state:
    st.stop()

df: pd.DataFrame = st.session_state["df_aquis"]

# ── Aviso de colunas ausentes ──────────────────────────────────
ausentes = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
if ausentes:
    st.warning(f"⚠️ Colunas não encontradas: `{'`, `'.join(ausentes)}`")

# ══════════════════════════════════════════════════════════════
# FILTROS LATERAIS
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔎 Filtros")

    # Tipo de Recebível
    if COL_TIPO in df.columns:
        tipos = ["Todos"] + sorted(df[COL_TIPO].dropna().unique().tolist())
        tipo_sel = st.multiselect("Tipo de Recebível", tipos, default=["Todos"])
    else:
        tipo_sel = ["Todos"]

    # Sacado
    if COL_SACADO in df.columns:
        sacados = ["Todos"] + sorted(df[COL_SACADO].dropna().unique().tolist())
        sacado_sel = st.multiselect("Sacado", sacados, default=["Todos"])
    else:
        sacado_sel = ["Todos"]

    # Período (Data de Entrada / Aquisição)
    if COL_ENTRADA in df.columns and df[COL_ENTRADA].notna().any():
        dt_min = df[COL_ENTRADA].min().date()
        dt_max = df[COL_ENTRADA].max().date()
        periodo_entrada = st.date_input(
            "Período de entrada",
            value=(dt_min, dt_max),
            min_value=dt_min,
            max_value=dt_max
        )
    else:
        periodo_entrada = None

    # Período (Data de Vencimento)
    if COL_DT_VENC in df.columns and df[COL_DT_VENC].notna().any():
        venc_min = df[COL_DT_VENC].min().date()
        venc_max = df[COL_DT_VENC].max().date()
        periodo_venc = st.date_input(
            "Período de vencimento",
            value=(venc_min, venc_max),
            min_value=venc_min,
            max_value=venc_max
        )
    else:
        periodo_venc = None

# Aplica filtros
df_f = df.copy()

if "Todos" not in tipo_sel and tipo_sel and COL_TIPO in df_f.columns:
    df_f = df_f[df_f[COL_TIPO].isin(tipo_sel)]

if "Todos" not in sacado_sel and sacado_sel and COL_SACADO in df_f.columns:
    df_f = df_f[df_f[COL_SACADO].isin(sacado_sel)]

if periodo_entrada and len(periodo_entrada) == 2 and COL_ENTRADA in df_f.columns:
    df_f = df_f[df_f[COL_ENTRADA].dt.date.between(periodo_entrada[0], periodo_entrada[1])]

if periodo_venc and len(periodo_venc) == 2 and COL_DT_VENC in df_f.columns:
    df_f = df_f[df_f[COL_DT_VENC].dt.date.between(periodo_venc[0], periodo_venc[1])]

# ══════════════════════════════════════════════════════════════
# KPIs GLOBAIS
# ══════════════════════════════════════════════════════════════
st.divider()
st.subheader("📊 KPIs Globais")

total_compra  = df_f[COL_VL_COMPRA].sum() if COL_VL_COMPRA in df_f.columns else 0
total_venc    = df_f[COL_VL_VENC].sum()   if COL_VL_VENC   in df_f.columns else 0
n_titulos     = len(df_f)
n_sacados     = df_f[COL_SACADO].nunique()    if COL_SACADO    in df_f.columns else 0
n_cedentes    = df_f[COL_CPF_CEDENTE].nunique() if COL_CPF_CEDENTE in df_f.columns else 0
n_tipos       = df_f[COL_TIPO].nunique()      if COL_TIPO      in df_f.columns else 0

# Deságio médio = (VL_VENC - VL_COMPRA) / VL_VENC
desagio = (total_venc - total_compra) / total_venc if total_venc else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 Total de Compra",    fmt_moeda(total_compra))
c2.metric("📋 Total de Vencimento", fmt_moeda(total_venc))
c3.metric("📈 Deságio Médio",       fmt_pct(desagio))
c4.metric("🗂️ Títulos",             fmt_numero(n_titulos))

c1, c2, c3 = st.columns(3)
c1.metric("👤 Sacados Únicos",  fmt_numero(n_sacados))
c2.metric("🏢 Cedentes Únicos", fmt_numero(n_cedentes))
c3.metric("📑 Tipos",           fmt_numero(n_tipos))

# ══════════════════════════════════════════════════════════════
# TABELAS AGRUPADAS
# ══════════════════════════════════════════════════════════════
from src.components.tables import agrupar_e_exibir, agrupar_por_mes

# Specs de agregação reutilizáveis
_AGG_COMPRA = {
    "Qtd":           (COL_VL_COMPRA, "count"),
    "Vl_Compra":     (COL_VL_COMPRA, "sum"),
    "Vl_Vencimento": (COL_VL_VENC,   "sum"),
}

# ── Por Tipo de Recebível ──
agrupar_e_exibir(
    df_f, COL_TIPO, _AGG_COMPRA,
    titulo="Por Tipo de Recebível", icone="📑",
    sort_col="Vl_Compra",
    col_ratio_pct=("Desagio", "Vl_Vencimento", "Vl_Compra"),
    colunas_moeda=["Vl_Compra", "Vl_Vencimento"],
    colunas_numero=["Qtd"],
    nomes_colunas=["Tipo", "Qtd", "Vl. Compra", "Vl. Vencimento", "Deságio"],
)

# ── Por Sacado (Top 20) ──
agrupar_e_exibir(
    df_f, COL_SACADO, _AGG_COMPRA,
    titulo="Por Sacado (Top 20)", icone="👤",
    sort_col="Vl_Compra", top_n=20,
    col_ratio_pct=("Desagio", "Vl_Vencimento", "Vl_Compra"),
    colunas_moeda=["Vl_Compra", "Vl_Vencimento"],
    colunas_numero=["Qtd"],
    nomes_colunas=["Sacado", "Qtd", "Vl. Compra", "Vl. Vencimento", "Deságio"],
)

# ── Por Mês de Entrada ──
_AGG_MES_COMPRA = {
    "Qtd":           (COL_VL_COMPRA, "count"),
    "Vl_Compra":     (COL_VL_COMPRA, "sum"),
    "Vl_Vencimento": (COL_VL_VENC,   "sum"),
}

agrupar_por_mes(
    df_f, COL_ENTRADA, _AGG_MES_COMPRA,
    titulo="Por Mês de Entrada", icone="📆",
    colunas_moeda=["Vl_Compra", "Vl_Vencimento"],
    colunas_numero=["Qtd"],
    nomes_colunas=["Mês Entrada", "Qtd", "Vl. Compra", "Vl. Vencimento"],
)

# ── Por Mês de Vencimento ──
agrupar_por_mes(
    df_f, COL_DT_VENC, _AGG_MES_COMPRA,
    titulo="Por Mês de Vencimento", icone="📅",
    colunas_moeda=["Vl_Compra", "Vl_Vencimento"],
    colunas_numero=["Qtd"],
    nomes_colunas=["Mês Vencimento", "Qtd", "Vl. Compra", "Vl. Vencimento"],
)

# ══════════════════════════════════════════════════════════════
# DETALHAMENTO — TABELA COMPLETA
# ══════════════════════════════════════════════════════════════
st.divider()
with st.expander("🔍 Ver tabela completa de aquisições"):
    colunas_exibir = list(dict.fromkeys(c for c in COLUNAS_ESPERADAS if c in df_f.columns))
    df_exibir = df_f[colunas_exibir].copy()
    df_exibir = df_exibir.loc[:, ~df_exibir.columns.duplicated()]
    st.dataframe(df_exibir.reset_index(drop=True), use_container_width=True)
    st.caption(f"Exibindo {len(df_f):,} registros.")
