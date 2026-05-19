"""
Página Streamlit: Análise de Liquidações.

Permite ao usuário:
  1. Fazer upload de ZIP, CSV ou XLSX com os dados de liquidações
  2. Visualizar KPIs globais (valores de aquisição, vencimento e pagos)
  3. Analisar por Situação do Recebível, Cedente, Sacado
  4. Quebrar por Data de Aquisição e Data de Vencimento
  5. Inspecionar os recebíveis individuais com filtros
"""

import io
import pandas as pd
import numpy as np
import streamlit as st
# pyrefly: ignore [missing-import]
from src.data_loader import carregar_arquivo, normalizar_colunas, aplicar_aliases, preparar_colunas_datas, preparar_colunas_valores
# pyrefly: ignore [missing-import]
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

    # Mês de Competência (DATA MOVIMENTO)
    if COL_DATA_MOV in df.columns and df[COL_DATA_MOV].notna().any():
        meses_competencia = sorted(
            df[COL_DATA_MOV].dropna()
            .dt.to_period("M")
            .unique()
            .astype(str)
            .tolist()
        )
        competencia_sel = st.multiselect(
            "📅 Mês de Competência (Liquidação)",
            options=["Todos"] + meses_competencia,
            default=["Todos"],
            help="Filtra pelo mês/ano da DATA MOVIMENTO (data de liquidação do título)."
        )
    else:
        competencia_sel = ["Todos"]

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

if "Todos" not in competencia_sel and competencia_sel and COL_DATA_MOV in df_f.columns:
    df_f = df_f[
        df_f[COL_DATA_MOV].dt.to_period("M").astype(str).isin(competencia_sel)
    ]

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
# pyrefly: ignore [missing-import]
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


# ══════════════════════════════════════════════════════════════
# ANÁLISE DE PRAZO DE LIQUIDAÇÃO
# ══════════════════════════════════════════════════════════════

def calcular_faixas_atraso(df: pd.DataFrame) -> pd.DataFrame | None:
    """Calcula faixas de prazo de liquidação com base em DATA MOVIMENTO e DATA DE VENCIMENTO.

    Retorna um DataFrame com as faixas, quantidades e valores pagos,
    ou None se as colunas necessárias não existirem.
    """
    if COL_DATA_MOV not in df.columns or COL_DT_VENC not in df.columns:
        return None

    df_tmp = df[[COL_DATA_MOV, COL_DT_VENC, COL_VL_PAGO]].copy() if COL_VL_PAGO in df.columns \
        else df[[COL_DATA_MOV, COL_DT_VENC]].copy()

    # Dias de atraso: positivo = atrasado, 0 ou negativo = em dia
    df_tmp["DIAS_ATRASO"] = (df_tmp[COL_DATA_MOV] - df_tmp[COL_DT_VENC]).dt.days

    # Remove linhas sem data válida
    df_tmp = df_tmp.dropna(subset=["DIAS_ATRASO"])
    df_tmp["DIAS_ATRASO"] = df_tmp["DIAS_ATRASO"].astype(int)

    # Faixas
    faixas_labels = [
        "Liquidados em dia",
        "1 a 30 dias",
        "31 a 60 dias",
        "61 a 90 dias",
        "91 a 120 dias",
        "121 a 150 dias",
        "151 a 180 dias",
        "Acima de 180 dias",
    ]

    def classificar(dias: int) -> str:
        if dias <= 0:
            return faixas_labels[0]
        elif dias <= 30:
            return faixas_labels[1]
        elif dias <= 60:
            return faixas_labels[2]
        elif dias <= 90:
            return faixas_labels[3]
        elif dias <= 120:
            return faixas_labels[4]
        elif dias <= 150:
            return faixas_labels[5]
        elif dias <= 180:
            return faixas_labels[6]
        else:
            return faixas_labels[7]

    df_tmp["FAIXA"] = df_tmp["DIAS_ATRASO"].map(classificar)

    # Agrega por faixa
    agg_dict: dict = {"DIAS_ATRASO": ["count", "max"]}
    if COL_VL_PAGO in df_tmp.columns:
        agg_dict[COL_VL_PAGO] = "sum"

    df_agg = df_tmp.groupby("FAIXA").agg(agg_dict)
    df_agg.columns = ["Qtd_Titulos", "Maior_Atraso_Dias"] if COL_VL_PAGO not in df_tmp.columns \
        else ["Qtd_Titulos", "Maior_Atraso_Dias", "Vl_Pago"]
    df_agg = df_agg.reset_index()

    # Garante que todas as faixas apareçam (mesmo com 0 títulos)
    df_completo = pd.DataFrame({"FAIXA": faixas_labels})
    df_agg = df_completo.merge(df_agg, on="FAIXA", how="left").fillna(0)
    df_agg["Qtd_Titulos"] = df_agg["Qtd_Titulos"].astype(int)
    df_agg["Maior_Atraso_Dias"] = df_agg["Maior_Atraso_Dias"].astype(int)

    # Percentual por quantidade
    total_qtd = df_agg["Qtd_Titulos"].sum()
    df_agg["%_Qtd"] = (df_agg["Qtd_Titulos"] / total_qtd) if total_qtd else 0.0

    return df_agg


st.divider()
st.subheader("⏱️ Análise de Prazo de Liquidação")
st.markdown(
    "Classifica cada título pelo número de dias entre a **data de vencimento** e a "
    "**data de liquidação** (DATA MOVIMENTO), separado por mês de competência."
)

# ── Mapa de meses PT ───────────────────────────────────────────
_MESES_PT = {
    "01": "jan", "02": "fev", "03": "mar", "04": "abr",
    "05": "mai", "06": "jun", "07": "jul", "08": "ago",
    "09": "set", "10": "out", "11": "nov", "12": "dez",
}

def _fmt_mes_ref(periodo_str: str) -> str:
    try:
        ano, mes = periodo_str.split("-")
        return f"{_MESES_PT.get(mes, mes)}/{ano}"
    except Exception:
        return periodo_str

# ── Constrói tabela mês a mês ──────────────────────────────────
_blocos_st: list[pd.DataFrame] = []

if COL_DATA_MOV in df_f.columns and df_f[COL_DATA_MOV].notna().any():
    _meses_ref = sorted(
        df_f[COL_DATA_MOV].dropna()
        .dt.to_period("M")
        .unique()
        .astype(str)
        .tolist()
    )
    for _mes in _meses_ref:
        _mask = df_f[COL_DATA_MOV].dt.to_period("M").astype(str) == _mes
        _bloco = calcular_faixas_atraso(df_f[_mask])
        if _bloco is not None:
            # Data como Timestamp dia 1 do mês — facilita filtros no Excel
            _bloco.insert(0, "Data Referência", pd.Timestamp(f"{_mes}-01"))
            _blocos_st.append(_bloco)

if not _blocos_st:
    st.warning("⚠️ Colunas `DATA MOVIMENTO` e/ou `DATA DE VENCIMENTO` não encontradas no arquivo.")
else:
    df_faixas = pd.concat(_blocos_st, ignore_index=True)

    # ── KPIs consolidados ──────────────────────────────────────
    # Label de exibição ainda usa texto amigável
    _ref_label = " · ".join(_fmt_mes_ref(m) for m in _meses_ref)
    _em_dia_tot    = df_faixas.loc[df_faixas["FAIXA"] == "Liquidados em dia", "Qtd_Titulos"].sum()
    _total_tot     = df_faixas["Qtd_Titulos"].sum()
    _atrasados_tot = _total_tot - _em_dia_tot
    _pct_em_dia    = _em_dia_tot / _total_tot if _total_tot else 0

    ka1, ka2, ka3, ka4 = st.columns(4)
    ka1.metric("📅 Referência",          _ref_label if len(_blocos_st) == 1 else f"{len(_blocos_st)} meses")
    ka2.metric("✅ Títulos em dia",       fmt_numero(int(_em_dia_tot)))
    ka3.metric("⚠️ Títulos atrasados",   fmt_numero(int(_atrasados_tot)))
    ka4.metric("📊 % Liquidados em dia",  fmt_pct(_pct_em_dia))

    # ── Formata para exibição ──────────────────────────────────
    df_faixas_exib = df_faixas.copy()
    df_faixas_exib["Data Referência"]   = df_faixas_exib["Data Referência"].dt.strftime("%m/%Y")
    df_faixas_exib["Qtd_Titulos"]       = df_faixas_exib["Qtd_Titulos"].map(fmt_numero)
    df_faixas_exib["Maior_Atraso_Dias"] = df_faixas_exib["Maior_Atraso_Dias"].map(fmt_numero)
    df_faixas_exib["%_Qtd"]             = df_faixas_exib["%_Qtd"].astype(float).map(fmt_pct)

    nomes_faixas = ["Data Referência", "Faixa de Prazo", "Qtd. Títulos", "Maior Atraso (dias)", "% Qtd"]
    if "Vl_Pago" in df_faixas_exib.columns:
        df_faixas_exib["Vl_Pago"] = df_faixas_exib["Vl_Pago"].map(fmt_moeda)
        nomes_faixas = ["Data Referência", "Faixa de Prazo", "Qtd. Títulos", "Maior Atraso (dias)", "Vl. Pago", "% Qtd"]

    df_faixas_exib.columns = nomes_faixas
    st.dataframe(df_faixas_exib, use_container_width=True, hide_index=True)

# DETALHAMENTO — TABELA COMPLETA

st.divider()
with st.expander("🔍 Ver tabela completa de recebíveis"):
    # Seleciona apenas colunas conhecidas, sem duplicatas
    colunas_exibir = list(dict.fromkeys(c for c in COLUNAS_ESPERADAS if c in df_f.columns))
    df_exibir = df_f[colunas_exibir].copy()
    df_exibir = df_exibir.loc[:, ~df_exibir.columns.duplicated()]  # guarda-chuva final
    st.dataframe(df_exibir.reset_index(drop=True), use_container_width=True)
    st.caption(f"Exibindo {len(df_f):,} registros.")


# ══════════════════════════════════════════════════════════════
# DOWNLOAD — EXCEL MULTI-ABAS
# ══════════════════════════════════════════════════════════════

st.divider()
st.subheader("📥 Exportar Dados")
st.markdown("Baixe todas as informações exibidas na página em um único arquivo Excel com múltiplas abas.")


def gerar_excel_exportacao(df_dados: pd.DataFrame, df_faixas_raw: pd.DataFrame | None) -> bytes:
    """Gera um arquivo Excel com múltiplas abas contendo todos os dados da página."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # Aba 1 — Dados Brutos (filtrados)
        # colunas_exp = list(dict.fromkeys(c for c in COLUNAS_ESPERADAS if c in df_dados.columns))
        # df_dados[colunas_exp].to_excel(writer, sheet_name="Dados Brutos", index=False)

        # Aba 2 — Por Situação
        if COL_SITUACAO in df_dados.columns:
            df_sit = df_dados.groupby(COL_SITUACAO, as_index=False).agg(**_AGG_LIQ)
            df_sit.columns = ["Situação", "Qtd", "Vl. Aquisição", "Vl. Vencimento", "Vl. Pago"]
            df_sit.to_excel(writer, sheet_name="Por Situação", index=False)

        # Aba 3 — Por Cedente
        if COL_CEDENTE in df_dados.columns:
            df_ced = df_dados.groupby(COL_CEDENTE, as_index=False).agg(**_AGG_LIQ)
            df_ced.columns = ["Cedente", "Qtd", "Vl. Aquisição", "Vl. Vencimento", "Vl. Pago"]
            df_ced.to_excel(writer, sheet_name="Por Cedente", index=False)

        # Aba 4 — Por Mês de Vencimento
        if COL_DT_VENC in df_dados.columns and df_dados[COL_DT_VENC].notna().any():
            df_mv = df_dados.copy()
            df_mv["Mês Vencimento"] = df_mv[COL_DT_VENC].dt.to_period("M").astype(str)
            df_mv = df_mv.groupby("Mês Vencimento", as_index=False).agg(**_AGG_LIQ).sort_values("Mês Vencimento")
            df_mv.columns = ["Mês Vencimento", "Qtd", "Vl. Aquisição", "Vl. Vencimento", "Vl. Pago"]
            df_mv.to_excel(writer, sheet_name="Por Mês Vencimento", index=False)

        # Aba 5 — Por Mês de Aquisição
        if COL_DT_AQUIS in df_dados.columns and df_dados[COL_DT_AQUIS].notna().any():
            df_ma = df_dados.copy()
            df_ma["Mês Aquisição"] = df_ma[COL_DT_AQUIS].dt.to_period("M").astype(str)
            df_ma = df_ma.groupby("Mês Aquisição", as_index=False).agg(**_AGG_LIQ).sort_values("Mês Aquisição")
            df_ma.columns = ["Mês Aquisição", "Qtd", "Vl. Aquisição", "Vl. Vencimento", "Vl. Pago"]
            df_ma.to_excel(writer, sheet_name="Por Mês Aquisição", index=False)

        # Aba 6 — Prazo de Liquidação: uma linha por faixa por mês de competência
        if COL_DATA_MOV in df_dados.columns and df_dados[COL_DATA_MOV].notna().any():
            _meses_exp = sorted(
                df_dados[COL_DATA_MOV].dropna()
                .dt.to_period("M")
                .unique()
                .astype(str)
                .tolist()
            )
            blocos: list[pd.DataFrame] = []
            for mes_periodo in _meses_exp:
                _mask = df_dados[COL_DATA_MOV].dt.to_period("M").astype(str) == mes_periodo
                _df_mes = df_dados[_mask]
                _df_faixas_mes = calcular_faixas_atraso(_df_mes)
                if _df_faixas_mes is None:
                    continue
                # Data como datetime.date — filtrável nativamente no Excel sem hora
                _df_faixas_mes.insert(0, "Data Referência", pd.Timestamp(f"{mes_periodo}-01").date())
                blocos.append(_df_faixas_mes)

            if blocos:
                df_exp_faixas = pd.concat(blocos, ignore_index=True)
                df_exp_faixas = df_exp_faixas.rename(columns={
                    "Data Referência": "Data Referência",
                    "FAIXA": "Faixa de Prazo",
                    "Qtd_Titulos": "Qtd. Títulos",
                    "Maior_Atraso_Dias": "Maior Atraso (dias)",
                    "%_Qtd": "% por Quantidade",
                    "Vl_Pago": "Vl. Pago",
                })
                df_exp_faixas.to_excel(writer, sheet_name="Prazo de Liquidação", index=False)


    return output.getvalue()


if st.button("📊 Gerar Excel para Download", type="primary"):
    with st.spinner("Gerando arquivo Excel..."):
        excel_bytes = gerar_excel_exportacao(df_f, df_faixas)
    st.download_button(
        label="⬇️ Baixar Excel (.xlsx)",
        data=excel_bytes,
        file_name="liquidacoes_exportacao.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
