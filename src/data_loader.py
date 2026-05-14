"""Módulo de leitura e carregamento de dados.

Fornece funções para leitura de arquivos ZIP, CSV e Excel de forma
padronizada, incluindo processamento em chunks para grandes volumes.
Funções compartilhadas de normalização de colunas também ficam aqui.
"""

import io
import logging
from zipfile import ZipFile
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

CHUNK_SIZE = 100_000  # linhas por chunk


# ══════════════════════════════════════════════════════════════
# LEITURA DE ARQUIVOS
# ══════════════════════════════════════════════════════════════

def ler_zip(file) -> pd.DataFrame:
    """Lê todos os CSVs dentro de um ZIP e retorna um DataFrame concatenado.

    Args:
        file: Caminho do arquivo ou objeto file-like (UploadedFile, BytesIO).

    Raises:
        ValueError: Se nenhum arquivo CSV for encontrado dentro do ZIP.
    """
    dfs = []
    with ZipFile(file) as z:
        for name in z.namelist():
            if name.endswith(".csv"):
                with z.open(name) as f:
                    dfs.append(pd.read_csv(
                        f,
                        encoding="ISO-8859-1",
                        delimiter=";",
                        on_bad_lines="skip",
                        low_memory=False
                    ))
    if not dfs:
        raise ValueError("Nenhum arquivo CSV encontrado dentro do ZIP.")
    return pd.concat(dfs, ignore_index=True)


def ler_csv(file) -> pd.DataFrame:
    """Lê um arquivo CSV com encoding ISO-8859-1 e separador ';'.

    Args:
        file: Caminho do arquivo ou objeto file-like.
    """
    return pd.read_csv(
        file,
        encoding="ISO-8859-1",
        delimiter=";",
        on_bad_lines="skip",
        low_memory=False
    )


@st.cache_data(show_spinner=False)
def carregar_arquivo(arquivo_bytes: bytes, nome: str) -> pd.DataFrame:
    """Lê ZIP, CSV ou XLSX e retorna um DataFrame bruto.

    Função compartilhada entre páginas de análise (aquisições, liquidações, etc).
    """
    buf = io.BytesIO(arquivo_bytes)
    ext = nome.rsplit(".", 1)[-1].lower()

    if ext == "zip":
        df = ler_zip(buf)
    elif ext == "csv":
        df = ler_csv(buf)
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(buf)
    else:
        raise ValueError(f"Formato não suportado: {ext}")
    return df


# ══════════════════════════════════════════════════════════════
# NORMALIZAÇÃO DE COLUNAS
# ══════════════════════════════════════════════════════════════

def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Maiúsculas + desambiguação de duplicatas com sufixo _2, _3...

    1. Converte para maiúsculas e remove espaços.
    2. Colunas repetidas recebem sufixo _2, _3...
    3. Guarda-chuva final remove qualquer duplicata remanescente.
    """
    novas = []
    contagem: dict[str, int] = {}
    for col in df.columns:
        nome = col.strip().upper()
        if nome in contagem:
            contagem[nome] += 1
            nome = f"{nome}_{contagem[nome]}"
        else:
            contagem[nome] = 1
        novas.append(nome)
    df.columns = novas
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def aplicar_aliases(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    """Renomeia aliases para nomes canônicos, um por vez (evita duplicatas).

    Args:
        df: DataFrame com colunas a renomear.
        aliases: Dicionário {alias: nome_canônico}.
    """
    for alias, canonical in aliases.items():
        if alias in df.columns and canonical not in df.columns:
            df = df.rename(columns={alias: canonical})
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def preparar_colunas_datas(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Converte colunas de data para datetime, protegendo contra duplicatas e inversão de mês/dia.
    Otimizado para performance vetorial.
    """
    for col_dt in colunas:
        if col_dt in df.columns:
            serie = df[col_dt]
            if isinstance(serie, pd.DataFrame):
                serie = serie.iloc[:, 0]
            
            # Se já for datetime, apenas remove timezone
            if pd.api.types.is_datetime64_any_dtype(serie):
                df[col_dt] = pd.to_datetime(serie).dt.tz_localize(None)
                continue
                
            # Para strings, detecta padrões ISO vs BR de forma vetorial
            s = serie.astype(str).str.strip()
            if s.empty:
                continue

            # Regex rápido para identificar ISO (YYYY-MM-DD)
            is_iso = s.str.contains(r"^\d{4}-\d{2}-\d{2}", regex=True, na=False)
            
            res = pd.Series(pd.NaT, index=serie.index)
            
            # Processa ISO e BR separadamente para usar dayfirst correto em cada grupo
            if is_iso.any():
                res[is_iso] = pd.to_datetime(s[is_iso], dayfirst=False, errors="coerce")
            
            if (~is_iso).any():
                res[~is_iso] = pd.to_datetime(s[~is_iso], dayfirst=True, errors="coerce")

            df[col_dt] = res
    return df


def preparar_colunas_valores(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Converte colunas numéricas com formato brasileiro (ponto milhar, vírgula decimal).
    Otimizado para performance vetorial.
    """
    for col_v in colunas:
        if col_v in df.columns:
            serie = df[col_v]
            if isinstance(serie, pd.DataFrame):
                serie = serie.iloc[:, 0]
            
            # Se já for numérico, apenas garante float
            if pd.api.types.is_numeric_dtype(serie):
                df[col_v] = pd.to_numeric(serie, errors="coerce")
                continue

            # Se for string, limpa símbolos e decide o separador decimal
            s = serie.astype(str).str.replace(r"[R$\s]", "", regex=True).str.strip()
            
            # Heurística: se tem ambos . e ,
            # BR: 1.234,56 -> ponto antes da vírgula
            # US: 1,234.56 -> vírgula antes do ponto
            mask_both = s.str.contains(r"\..*,", regex=True, na=False)
            mask_us_both = s.str.contains(r",.*\.", regex=True, na=False)
            mask_comma_only = s.str.contains(",", na=False) & ~mask_both & ~mask_us_both
            
            s_clean = s.copy()
            if mask_both.any():
                s_clean.loc[mask_both] = s.loc[mask_both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            if mask_us_both.any():
                s_clean.loc[mask_us_both] = s.loc[mask_us_both].str.replace(",", "", regex=False)
            if mask_comma_only.any():
                s_clean.loc[mask_comma_only] = s.loc[mask_comma_only].str.replace(",", ".", regex=False)

            df[col_v] = pd.to_numeric(s_clean, errors="coerce")
            
    df = df.loc[:, ~df.columns.duplicated()]
    return df


# ══════════════════════════════════════════════════════════════
# CHUNKS
# ══════════════════════════════════════════════════════════════

def processar_zip_por_chunks(caminho_zip: str, colunas: list = None):
    """Lê cada CSV dentro do ZIP em chunks, evitando carregar tudo na RAM.

    Retorna um generator de DataFrames.
    """
    with ZipFile(caminho_zip, 'r') as z:
        csvs = [f for f in z.namelist() if f.endswith('.csv')]

        for nome_csv in csvs:
            with z.open(nome_csv) as arquivo:
                for chunk in pd.read_csv(
                    arquivo,
                    chunksize=CHUNK_SIZE,
                    encoding='ISO-8859-1',
                    sep=";",
                    usecols=colunas,
                    low_memory=False
                ):
                    yield chunk
