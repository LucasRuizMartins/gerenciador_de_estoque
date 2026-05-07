"""Componentes Streamlit reutilizáveis para tabelas agrupadas.

Centraliza o padrão repetido de:
  groupby → agg → format → rename → st.dataframe

Uso nas pages:
    from src.components.tables import agrupar_e_exibir, agrupar_por_mes
"""

import pandas as pd
import streamlit as st
from src.formatting import fmt_moeda, fmt_numero, fmt_pct


def agrupar_e_exibir(
    df: pd.DataFrame,
    group_col: str,
    agg_specs: dict[str, tuple[str, str]],
    *,
    titulo: str = "",
    icone: str = "",
    sort_col: str | None = None,
    ascending: bool = False,
    top_n: int | None = None,
    colunas_moeda: list[str] | None = None,
    colunas_numero: list[str] | None = None,
    colunas_pct: list[str] | None = None,
    col_ratio_pct: tuple[str, str, str] | None = None,
    col_return_pct: tuple[str, str, str] | None = None,
    nomes_colunas: list[str] | None = None,
    show_divider: bool = True,
) -> pd.DataFrame | None:
    """Agrupa, formata e exibe uma tabela Streamlit.

    Args:
        df: DataFrame filtrado.
        group_col: Coluna para groupby.
        agg_specs: Dict de {nome_saída: (coluna_origem, agg_func)}.
                   Ex: {"Qtd": ("ID", "count"), "Vl_Compra": ("VALOR", "sum")}
        titulo: Texto do subheader.
        icone: Emoji para o subheader.
        sort_col: Coluna para ordenação (padrão: 1ª coluna de valor).
        ascending: Direção da ordenação.
        top_n: Se definido, mostra apenas os N primeiros.
        colunas_moeda: Colunas a formatar como R$.
        colunas_numero: Colunas a formatar como inteiro.
        colunas_pct: Colunas a formatar como %.
        col_ratio_pct: Tupla (nome_nova, numerador, denominador) para deságio.
                       Fórmula: (num - den) / num
        col_return_pct: Tupla (nome_nova, numerador, denominador) para retorno.
                        Fórmula: num / den - 1
        nomes_colunas: Lista de nomes finais para display.
        show_divider: Se True, mostra divider antes do bloco.

    Returns:
        DataFrame formatado ou None se group_col não existir.
    """
    if group_col not in df.columns:
        return None

    # Agrupa
    df_agg = df.groupby(group_col, as_index=False).agg(**agg_specs)

    # Ordena
    if sort_col and sort_col in df_agg.columns:
        df_agg = df_agg.sort_values(sort_col, ascending=ascending)
    elif len(df_agg.columns) > 1:
        df_agg = df_agg.sort_values(df_agg.columns[1], ascending=ascending)

    # Top N
    if top_n:
        df_agg = df_agg.head(top_n)

    # Deságio: (num - den) / num
    if col_ratio_pct:
        nome, num, den = col_ratio_pct
        df_agg[nome] = ((df_agg[num] - df_agg[den]) / df_agg[num]).map(fmt_pct)

    # Retorno: num / den - 1
    if col_return_pct:
        nome, num, den = col_return_pct
        df_agg[nome] = (df_agg[num] / df_agg[den] - 1).map(fmt_pct)

    # Formatação
    for col in (colunas_moeda or []):
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].map(fmt_moeda)

    for col in (colunas_numero or []):
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].map(fmt_numero)

    for col in (colunas_pct or []):
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].map(fmt_pct)

    # Renomeia colunas para display
    if nomes_colunas and len(nomes_colunas) == len(df_agg.columns):
        df_agg.columns = nomes_colunas

    # Exibe
    if show_divider:
        st.divider()
    if titulo:
        st.subheader(f"{icone} {titulo}" if icone else titulo)

    st.dataframe(df_agg, use_container_width=True, hide_index=True)
    return df_agg


def agrupar_por_mes(
    df: pd.DataFrame,
    date_col: str,
    agg_specs: dict[str, tuple[str, str]],
    *,
    titulo: str = "",
    icone: str = "",
    colunas_moeda: list[str] | None = None,
    colunas_numero: list[str] | None = None,
    nomes_colunas: list[str] | None = None,
    show_divider: bool = True,
) -> pd.DataFrame | None:
    """Agrupa por mês (period) de uma coluna de data e exibe.

    Args:
        df: DataFrame filtrado.
        date_col: Coluna datetime para agrupar por mês.
        agg_specs: Especificações de agregação.
        titulo: Título do subheader.
        icone: Emoji.
        colunas_moeda: Colunas a formatar como R$.
        colunas_numero: Colunas a formatar como inteiro.
        nomes_colunas: Nomes finais das colunas.
        show_divider: Se True, mostra divider.

    Returns:
        DataFrame formatado ou None se date_col não existir/for vazia.
    """
    if date_col not in df.columns or not df[date_col].notna().any():
        return None

    df_tmp = df.copy()
    col_mes = f"_mes_{date_col}"
    df_tmp[col_mes] = df_tmp[date_col].dt.to_period("M").astype(str)

    df_agg = df_tmp.groupby(col_mes, as_index=False).agg(**agg_specs).sort_values(col_mes)

    # Formatação
    for col in (colunas_moeda or []):
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].map(fmt_moeda)

    for col in (colunas_numero or []):
        if col in df_agg.columns:
            df_agg[col] = df_agg[col].map(fmt_numero)

    if nomes_colunas and len(nomes_colunas) == len(df_agg.columns):
        df_agg.columns = nomes_colunas

    if show_divider:
        st.divider()
    if titulo:
        st.subheader(f"{icone} {titulo}" if icone else titulo)

    st.dataframe(df_agg, use_container_width=True, hide_index=True)
    return df_agg
