"""Preparação de dados de ESTOQUE para geração de CNAB de LIQUIDAÇÃO.

Módulo puro (sem Streamlit): lê o layout de estoque, filtra por vencimento,
mapeia o tipo de recebível do estoque para o código numérico do CNAB e
monta a tabela editável usada pela página de liquidação.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from src.global_var import MAP_ESPECIE_TITULO, MAP_OCORRENCIA

# Tipo de baixa (ocorrência) padrão: 75 - Baixa por depósito cedente
OCORRENCIA_PADRAO = "75"
ESPECIE_PADRAO = "01"

COLUNAS_ESTOQUE_OBRIGATORIAS = [
    "TIPO_RECEBIVEL", "VALOR_NOMINAL", "DATA_VENCIMENTO_AJUSTADA",
]

# Colunas do estoque aproveitadas para o CNAB (as demais são descartadas)
COLUNAS_UTEIS = [
    "NOME_CEDENTE", "DOC_CEDENTE", "NOME_SACADO", "DOC_SACADO",
    "TIPO_RECEBIVEL", "VALOR_NOMINAL", "VALOR_PRESENTE", "VALOR_AQUISICAO",
    "DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO", "DATA_AQUISICAO",
    "NU_DOCUMENTO", "SEU_NUMERO",
]
COLUNAS_NUMERICAS = ["VALOR_NOMINAL", "VALOR_PRESENTE", "VALOR_AQUISICAO"]
COLUNAS_DATA = ["DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO", "DATA_AQUISICAO"]

# ── Mapeamento tipo de recebível (estoque) -> código CNAB ────────────────────
# Chaves normalizadas (maiúsculo, sem acento, só A-Z0-9 e espaço).
# Acrescente novas entradas aqui conforme novos tipos aparecerem no estoque.
MAPA_TIPO_EXATO = {
    "DUPLICATA": "01",
    "DUPLICATA MERCANTIL": "01",
    "NOTA PROMISSORIA": "02",
    "NP": "02",
    "NOTA DE SEGURO": "03",
    "COBRANCA SERIADA": "04",
    "RECIBO": "05",
    "NOTA COMERCIAL": "09",
    "LETRA DE CAMBIO": "10",
    "LETRAS DE CAMBIO": "10",
    "NOTA DE DEBITO": "11",
    "PRECATORIO": "13",
    "PRECATORIOS": "13",
    "DUPLICATA DE SERVICO": "14",
    "DUPLICATA SERVICO": "14",
    "RENEGOCIACAO DA DIVIDA": "21",
    "UNIDADE DE RECEBIVEL": "29",
    "UNIDADES DE RECEBIVEL": "29",
    "UNIDADE DE RECEBIVEIS": "29",
    "UNIDADES DE RECEBIVEIS": "29",
    "UR": "29",
    "CCB": "41",
    "CCB DIGITAL": "41",
    "NOTA FISCAL": "50",
    "NF": "50",
    "CHEQUE": "51",
    "CHEQUE MANUAL": "52",
    "CONTRATO": "60",
    "CONTRATO FISICO": "61",
    "CONFISSAO DE DIVIDA": "62",
    "ASSUNCAO DE DIVIDA": "64",
    "FATURA DE CARTAO": "65",
    "FATURA DE CARTAO DE CREDITO": "65",
    "CARTAO DE CREDITO": "65",
    "CCB PRE DIGITAL": "70",
    "CCB PRE BALCAO": "71",
    "CCB PRE CETIP": "72",
    "OUTROS": "73",
    "CCB FORMALIZACAO FONADA": "74",
}

# Aproximação por palavra-chave (ordem importa: do mais específico ao genérico)
PALAVRAS_CHAVE = [
    ("DUPLICATA", "SERVICO", "14"),
    ("DUPLICATA", None, "01"),
    ("NOTA", "PROMISSORIA", "02"),
    ("NOTA", "COMERCIAL", "09"),
    ("NOTA", "DEBITO", "11"),
    ("NOTA", "SEGURO", "03"),
    ("NOTA", "FISCAL", "50"),
    ("LETRA", "CAMBIO", "10"),
    ("UNIDADE", "RECEBIVEL", "29"),
    ("UNIDADES", "RECEBIVEL", "29"),
    ("RECEBIVEL", None, "29"),
    ("RECEBIVEIS", None, "29"),
    ("UR", None, "29"),
    ("CHEQUE", None, "51"),
    ("CONFISSAO", None, "62"),
    ("ASSUNCAO", None, "64"),
    ("FATURA", None, "65"),
    ("CARTAO", None, "65"),
    ("CCB", None, "41"),
    ("CONTRATO", None, "60"),
    ("PRECATORIO", None, "13"),
    ("RECIBO", None, "05"),
]


def normalizar_texto(valor) -> str:
    """Maiúsculo, sem acento, apenas A-Z0-9 e espaço."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ""
    s = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Z0-9 ]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


def rotulo_especie(cod: str) -> str:
    cod = str(cod).zfill(2)
    desc = MAP_ESPECIE_TITULO.get(int(cod)) if cod.isdigit() else None
    return f"{cod} - {desc.upper()}" if desc else f"{cod} - [NÃO CADASTRADO]"


def mapear_tipo_recebivel(valor) -> Tuple[str, bool]:
    """Retorna (código CNAB, encontrado).

    Tenta: código numérico já informado -> match exato -> aproximação por
    palavras-chave. Se nada casar, devolve o padrão (01) com encontrado=False.
    """
    texto = normalizar_texto(valor)
    if not texto:
        return ESPECIE_PADRAO, False
    primeiro = texto.split()[0]
    if primeiro.isdigit() and len(primeiro) <= 2:
        return primeiro.zfill(2), True
    if texto in MAPA_TIPO_EXATO:
        return MAPA_TIPO_EXATO[texto], True
    palavras = set(texto.split())
    for chave1, chave2, cod in PALAVRAS_CHAVE:
        if chave1 in palavras and (chave2 is None or chave2 in palavras):
            return cod, True
    return ESPECIE_PADRAO, False


# ── Leitura/normalização ─────────────────────────────────────────────────────

def parse_numero(serie: pd.Series) -> pd.Series:
    """Converte números em formato BR ('1.234,56') ou US ('1234.56') para float."""
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float).fillna(0.0)
    s = serie.fillna("").astype(str).str.strip().str.replace("R$", "", regex=False)
    tem_virgula = s.str.contains(",", regex=False)
    s = s.where(~tem_virgula, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


_FORMATOS_DATA = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d",
]
_INVALIDOS = {"", "nan", "NaT", "None", "none", "NAT", "NAN"}


def parse_data(serie: pd.Series) -> pd.Series:
    """Converte datas em vários formatos, priorizando padrão brasileiro."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    s = serie.fillna("").astype(str).str.strip()
    valido = ~s.isin(_INVALIDOS)
    dt = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    for fmt in _FORMATOS_DATA:
        mask = dt.isna() & valido
        if not mask.any():
            break
        parsed = pd.to_datetime(s[mask], format=fmt, errors="coerce")
        dt[mask] = dt[mask].where(parsed.isna(), parsed)
    resto = dt.isna() & valido
    if resto.any():
        dt[resto] = pd.to_datetime(s[resto], dayfirst=True, errors="coerce")
    return dt


def normalizar_estoque(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém só as colunas úteis e tipa números/datas.

    Raises:
        ValueError: se faltarem colunas obrigatórias do estoque.
    """
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    faltando = [c for c in COLUNAS_ESTOQUE_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias ausentes no estoque: {', '.join(faltando)}")

    out = pd.DataFrame(index=df.index)
    for col in COLUNAS_UTEIS:
        if col in df.columns:
            out[col] = df[col]
        elif col in COLUNAS_NUMERICAS:
            out[col] = 0.0
        else:
            out[col] = None
    for col in COLUNAS_NUMERICAS:
        out[col] = parse_numero(out[col])
    for col in COLUNAS_DATA:
        out[col] = parse_data(out[col])
    for col in ["NOME_CEDENTE", "DOC_CEDENTE", "NOME_SACADO", "DOC_SACADO", "NU_DOCUMENTO", "SEU_NUMERO"]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    return out.dropna(subset=["DATA_VENCIMENTO_AJUSTADA"]).reset_index(drop=True)


def filtrar_vencimento(
    df: pd.DataFrame,
    modo: str,
    data_ref: date,
) -> pd.DataFrame:
    """Filtra pelo vencimento.

    modo="data": apenas títulos vencendo exatamente em data_ref.
    modo="vencidos": todos com vencimento <= data_ref.
    """
    venc = df["DATA_VENCIMENTO_AJUSTADA"].dt.normalize()
    ref = pd.Timestamp(data_ref).normalize()
    mask = (venc == ref) if modo == "data" else (venc <= ref)
    return df[mask].reset_index(drop=True)


def montar_tabela_liquidacao(
    df_filtrado: pd.DataFrame,
    data_liquidacao: Optional[date] = None,
    ocorrencia: str = OCORRENCIA_PADRAO,
) -> Tuple[pd.DataFrame, set]:
    """Cria a tabela editável de liquidação.

    VALOR_PAGO = VALOR_NOMINAL; TIPO_RECEBIVEL vira rótulo 'NN - DESCRIÇÃO';
    IDENTIFICACAO_OCORRENCIA vira 'NN - descrição'.

    Returns:
        (tabela, tipos_nao_mapeados) — o 2º item lista tipos de recebível
        do estoque sem correspondência (receberam o padrão 01).
    """
    tab = df_filtrado.copy()
    nao_mapeados: set = set()
    rotulos = []
    for original in tab["TIPO_RECEBIVEL"]:
        cod, ok = mapear_tipo_recebivel(original)
        if not ok:
            nao_mapeados.add(str(original))
        rotulos.append(rotulo_especie(cod))
    tab["TIPO_RECEBIVEL_ESTOQUE"] = tab["TIPO_RECEBIVEL"].astype(str)
    tab["TIPO_RECEBIVEL"] = rotulos
    tab["VALOR_PAGO"] = tab["VALOR_NOMINAL"]
    tab["DATA_LIQUIDACAO"] = pd.Timestamp(data_liquidacao) if data_liquidacao else pd.NaT
    tab["IDENTIFICACAO_OCORRENCIA"] = rotulo_ocorrencia(ocorrencia)
    tab.insert(0, "INCLUIR", True)
    tab.insert(1, "LOTE", False)
    return tab, nao_mapeados


def rotulo_ocorrencia(cod: str) -> str:
    cod = str(cod).zfill(2)
    return f"{cod} - {MAP_OCORRENCIA.get(cod, '[NÃO CADASTRADO]')}"


def codigo_do_rotulo(rotulo) -> str:
    """Extrai o código numérico de 'NN - descrição'."""
    s = str(rotulo).strip()
    token = s.split("-")[0].strip().split()[0] if s else ""
    return token.zfill(2)[-2:] if token.isdigit() else s[:2].zfill(2)


def preparar_para_cnab(tab: pd.DataFrame) -> pd.DataFrame:
    """Aplica seleção (INCLUIR) e converte rótulos em códigos para o conversor."""
    df = tab[tab["INCLUIR"].fillna(False).astype(bool)].copy()
    df["TIPO_RECEBIVEL"] = df["TIPO_RECEBIVEL"].map(codigo_do_rotulo)
    df["IDENTIFICACAO_OCORRENCIA"] = df["IDENTIFICACAO_OCORRENCIA"].map(codigo_do_rotulo)
    df["VALOR_PAGO"] = pd.to_numeric(df["VALOR_PAGO"], errors="coerce").fillna(0.0)
    for col in COLUNAS_DATA + ["DATA_LIQUIDACAO"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df.drop(columns=["INCLUIR", "LOTE", "TIPO_RECEBIVEL_ESTOQUE"], errors="ignore").reset_index(drop=True)
