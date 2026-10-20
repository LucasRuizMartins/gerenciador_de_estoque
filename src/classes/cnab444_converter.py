import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Union, Any
# pyrefly: ignore [missing-import]
from src.global_var import MAP_ESPECIE_TITULO


class CnabVariant(str, Enum):
    """Variantes de layout CNAB 444 suportadas."""
    APEX_444 = "APEX_444"   # Padrão BRL Trust / APEX GROUP (atual)
    QI_444   = "QI_444"    # Padrão QI (Singulare) — ajustado ago/2025

# Definições estáticas para otimização de CPU-bound operations
TRANS_TABLE = str.maketrans({
    'Á':'A','À':'A','Â':'A','Ã':'A','Ä':'A',
    'É':'E','È':'E','Ê':'E','Ë':'E',
    'Í':'I','Ì':'I','Î':'I','Ï':'I',
    'Ó':'O','Ò':'O','Ô':'O','Õ':'O','Ö':'O',
    'Ú':'U','Ù':'U','Û':'U','Ü':'U',
    'Ç':'C','Ñ':'N'
})

INVALID_CHARS_RE = re.compile(r'[^A-Z0-9 \.\-\/,]')
ALFANUM_CHARS_RE = re.compile(r'[^A-Z0-9\.\-\/,]')
DIGITS_ONLY_RE = re.compile(r'\D')


def _fmt_termo_cessao(valor: Any) -> str:
    """Formata valor para o campo TERMO_CESSAO (X(19)).
    Se for datetime/date, retorna DD/MM/YYYY (sem traços, sem timestamp).
    Caso contrário, retorna str() do valor.
    """
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d%m%y")
    if hasattr(valor, "strftime"):
        try:
            return valor.strftime("%d%m%y")
        except (ValueError, AttributeError):
            return ""
    return str(valor)


class CNABFormatter:
    """Utilitários de formatação clássicos para arquivos CNAB (chamadas individuais)."""

    @staticmethod
    def num(valor: Any, tamanho: int, decimais: int = 0) -> str:
        """Campo numérico: alinhado à direita, zeros à esquerda."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            valor = 0
        if isinstance(valor, str):
            valor = valor.strip()
            if "," in valor:
                valor = valor.replace(".", "").replace(",", ".")
        try:
            if decimais > 0:
                valor = round(float(valor) * (10 ** decimais))
            valor = int(valor)
        except Exception:
            valor = 0
        return str(valor).zfill(tamanho)[-tamanho:]

    @staticmethod
    def alfa(valor: Any, tamanho: int) -> str:
        """Campo alfanumérico: maiúsculo, sem acento, alinhado à esquerda."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            valor = ""
        valor = str(valor).upper().translate(TRANS_TABLE)
        valor = INVALID_CHARS_RE.sub(' ', valor)
        return valor[:tamanho].ljust(tamanho)

    @staticmethod
    def alfa_num(valor: Any, tamanho: int) -> str:
        """Campo alfanumérico: limpa caracteres e preenche com ZEROS à ESQUERDA."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            valor = ""
        
        # Limpeza básica (reaproveitando lógica de alfa)
        valor = str(valor).upper().translate(TRANS_TABLE)
        valor = ALFANUM_CHARS_RE.sub('', valor)
        
        # Preenche com zeros à esquerda
        return valor.zfill(tamanho)[-tamanho:]

    @staticmethod
    def data(valor: Any) -> str:
        """Formata data para DDMMAA de forma robusta."""
        # Verifica explicitamente None, NaN float e pd.NaT antes de qualquer outra coisa
        if valor is None:
            return "000000"
        try:
            if pd.isna(valor):
                return "000000"
        except (TypeError, ValueError):
            pass
        
        # Se for um Timestamp do pandas, datetime ou date (mas NÃO NaT — já tratado acima)
        if isinstance(valor, (datetime, date)) or hasattr(valor, "strftime"):
            try:
                return valor.strftime("%d%m%y")
            except (ValueError, AttributeError):
                return "000000"
            
        try:
            # Tenta converter usando pandas (fallback para strings)
            dt = pd.to_datetime(valor, errors='coerce')
            if pd.notna(dt):
                return dt.strftime("%d%m%y")
        except Exception:
            pass
            
        return "000000"


    @staticmethod
    def cep(valor: Any) -> str:
        """Remove hífen e garante 8 dígitos."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return "00000000"
        s = DIGITS_ONLY_RE.sub('', str(valor))
        return s.zfill(8)[:8]

    @staticmethod
    def cnpj_cpf(valor: Any, tamanho: int = 14) -> str:
        """Remove pontuação e retorna só dígitos."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return "0" * tamanho
        s = DIGITS_ONLY_RE.sub('', str(valor))
        return s.zfill(tamanho)[-tamanho:]


class CNABFormatterVectorized:
    """Utilitários de formatação de CNAB otimizados com Pandas (Vetorizados)."""

    @staticmethod
    def num(series: pd.Series, tamanho: int, decimais: int = 0) -> pd.Series:
        # Suporta decimais brasileiros com vírgula e remove pontos de milhar
        s = series.fillna("0").astype(str).str.strip()
        has_comma = s.str.contains(",", regex=False)
        s_cleaned = pd.Series(
            np.where(has_comma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), s),
            index=series.index
        )
        
        s_num = pd.to_numeric(s_cleaned, errors='coerce').fillna(0)
        if decimais > 0:
            s_num = (s_num * (10 ** decimais)).round()
        s_str = s_num.astype(np.int64).astype(str)
        return s_str.str.zfill(tamanho).str.slice(-tamanho)

    @staticmethod
    def alfa(series: pd.Series, tamanho: int) -> pd.Series:
        s = series.fillna("").astype(str).str.upper()
        # Traduz acentos de forma rápida na lista de strings
        translated = [val.translate(TRANS_TABLE) for val in s]
        s = pd.Series(translated, index=series.index)
        # Substitui caracteres inválidos
        s = s.str.replace(r'[^A-Z0-9 \.\-\/,]', ' ', regex=True)
        return s.str.slice(0, tamanho).str.ljust(tamanho)

    @staticmethod
    def alfa_num(series: pd.Series, tamanho: int) -> pd.Series:
        s = series.fillna("").astype(str).str.upper()
        translated = [val.translate(TRANS_TABLE) for val in s]
        s = pd.Series(translated, index=series.index)
        s = s.str.replace(r'[^A-Z0-9\.\-\/,]', '', regex=True)
        return s.str.zfill(tamanho).str.slice(-tamanho)

    @staticmethod
    def data(series: pd.Series) -> pd.Series:
        if pd.api.types.is_datetime64_any_dtype(series):
            return series.dt.strftime("%d%m%y").fillna("000000")

        # Tenta formatos explícitos em ordem de prioridade (brasileiro primeiro)
        # Isso evita que o pandas interprete datas americanas MM-DD-YYYY incorretamente
        FORMATOS_BR = [
            "%d/%m/%Y", "%d/%m/%y",   # 18/05/2026 ou 18/05/26
            "%d-%m-%Y", "%d-%m-%y",   # 18-05-2026 ou 18-05-26
            "%d.%m.%Y", "%d.%m.%y",   # 18.05.2026
            "%Y-%m-%d",               # ISO 8601 (invariável, sem ambiguidade)
        ]

        s_str = series.fillna("").astype(str).str.strip()
        dt = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

        # Primeira passagem: formatos explícitos (sem ambiguidade)
        for fmt in FORMATOS_BR:
            mask = dt.isna() & (s_str != "") & (s_str != "nan") & (s_str != "NaT")
            if not mask.any():
                break
            parsed = pd.to_datetime(s_str[mask], format=fmt, errors="coerce")
            dt[mask] = dt[mask].where(parsed.isna(), parsed)

        # Fallback: inferência do pandas com dayfirst=True para qualquer remanescente
        still_na = dt.isna() & (s_str != "") & (s_str != "nan") & (s_str != "NaT")
        if still_na.any():
            parsed_fb = pd.to_datetime(s_str[still_na], dayfirst=True, errors="coerce")
            dt[still_na] = dt[still_na].where(parsed_fb.isna(), parsed_fb)

        return dt.dt.strftime("%d%m%y").fillna("000000")

    @staticmethod
    def cep(series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.replace(r'\D', '', regex=True)
        return s.str.zfill(8).str.slice(0, 8)

    @staticmethod
    def cnpj_cpf(series: pd.Series, tamanho: int = 14) -> pd.Series:
        s = series.fillna("").astype(str).str.replace(r'\D', '', regex=True)
        return s.str.zfill(tamanho).str.slice(-tamanho)

    @staticmethod
    def tipo_pessoa(series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.replace(r'\D', '', regex=True)
        return np.where(s.str.len() <= 11, "01", "02")


class CNAB444Converter:
    """Conversor de Excel/CSV para CNAB 444.
    
    Suporta múltiplas variantes de layout via `variant`:
    - ``CnabVariant.APEX_444`` (padrão): layout BRL Trust / APEX GROUP V3
    - ``CnabVariant.QI_444``: layout QI (Singulare) — revisado ago/2025

    Diferenças estruturais entre variantes:
    - Header: QI possui campo CNPJ Emissor Original (duplo endosso) nas
      posições 378–392; APEX usa brancos nessa região.
    - Detalhe: QI subdivide o endereço do sacado (pos 275–314, 40 chars) em
      Logradouro (16) + Bairro (7) + Cidade (15) + Estado (2); APEX usa
      um único campo "Endereço Completo" de 40 chars.
    """
    
    LINE_SIZE = 444

    def __init__(self, config: Dict, variant: CnabVariant = CnabVariant.APEX_444):
        self.config = config
        self.variant = CnabVariant(variant)  # aceita str ou enum
        self.formatter = CNABFormatter()
        self.formatter_vec = CNABFormatterVectorized()
        # Converte o mapa do global_var (int: desc) para (desc_upper: cod_str)
        self.mapa_especies = {
            v.upper(): str(k).zfill(2) for k, v in MAP_ESPECIE_TITULO.items()
        }
        self.mapa_especies.update({
            "DUPLICATA": "01",
            "NP": "02",
            "NOTA PROMISSORIA": "02",
            "NOTA PROMISSORIA FISICA": "06",
            "NOTA COMERCIAL": "09",
            "DUPLICATA SERVICO": "14",
            "DUPLICATA DE SERVICO FISICA": "14",
            "CHEQUE": "51",
            "CONTRATO": "60",
            "CONTRATO FISICO": "61",
            "CONFISSAO DE DIVIDA": "62",
            "FATURA CARTAO": "65",
            "FATURA DE CARTAO CREDITO": "65",
            "CCB DIGITAL": "41",
            "CCB PRE DIGITAL": "70",
            "CCB PRE BALCAO": "71",
            "CCB PRE CETIP": "72",
            "OUTROS": "73",
            "CCB FORMALIZACAO FONADA": "74",
            # Espécies adicionais da variante QI_444
            "UNIDADE DE RECEBIVEL": "29",
            "UNIDADES DE RECEBIVEL": "29",
            "UNIDADE DE RECEBIVEIS": "29",
            "UNIDADES DE RECEBIVEIS": "29",
            "UR": "29",
            "NOTA COMERCIAL PRE": "79",
            "NOTA COMERCIAL POS": "82",
            "CCE POS": "85",
            "CEDULA CREDITO EXPORTACAO POS": "85",
            "CCE PRE": "86",
            "CEDULA CREDITO EXPORTACAO PRE": "86",
            "NCE POS": "88",
            "NOTA CREDITO EXPORTACAO POS": "88",
            "NCE PRE": "89",
            "NOTA CREDITO EXPORTACAO PRE": "89",
        })

    @property
    def is_qi(self) -> bool:
        """Atalho para verificar se a variante ativa é QI_444."""
        return self.variant == CnabVariant.QI_444

    def _valida_linha(self, linha: str) -> str:
        if len(linha) != self.LINE_SIZE:
            raise ValueError(f"Linha inválida: {len(linha)} caracteres (esperado {self.LINE_SIZE})")
        return linha

    def _get_especie(self, tipo: Any) -> str:
        if tipo is None or (isinstance(tipo, float) and pd.isna(tipo)):
            return "01"
            
        chave = str(tipo).upper().strip()
        
        primeira_parte = chave.split('-')[0].strip().split()[0]
        if primeira_parte.isdigit():
            return primeira_parte.zfill(2)[:2]
            
        chave_limpa = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in chave).strip()
        if chave_limpa in self.mapa_especies:
            return self.mapa_especies[chave_limpa]
        return chave_limpa[:2].zfill(2) if chave_limpa else "01"

    def _get_especie_vectorized(self, series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.upper().str.strip()
        token1 = s.str.split('-').str[0].str.strip().str.split().str[0].fillna("")
        is_digit = token1.str.isdigit()
        
        cleaned_chars = s.str.replace(r'[^A-Z0-9 ]', ' ', regex=True).str.strip()
        mapped = cleaned_chars.map(self.mapa_especies)
        
        fallback_cod = cleaned_chars.str.slice(0, 2).str.zfill(2)
        final_mapped = mapped.fillna(fallback_cod).replace("", "01")
        
        result = np.where(is_digit, token1.str.zfill(2).str.slice(-2), final_mapped)
        return pd.Series(result, index=series.index)

    def _get_tipo_pessoa(self, doc: str) -> str:
        s = ''.join(filter(str.isdigit, str(doc))) if doc else ""
        return "01" if len(s) <= 11 else "02"

    def montar_header(self, seq_arquivo: int, data_gravacao: Optional[str] = None) -> str:
        if data_gravacao is None:
            data_gravacao = datetime.today().strftime("%d%m%y")
            
        f = self.formatter
        c = self.config

        # Campos comuns: pos 1–139
        parte_comum = (
            "0"                                         # 1    pos 1      Ident. Registro
            + "1"                                       # 2    pos 2      Ident. Arquivo Remessa
            + f.alfa("REMESSA", 7)                      # 3    pos 3-9    Literal Remessa
            + "01"                                      # 4    pos 10-11  Código Serviço
            + f.alfa("COBRANCA", 15)                    # 5    pos 12-26  Literal Serviço
            + f.num(c["codigo_originador"], 20)         # 6    pos 27-46  Código Originador
            + f.alfa(c["nome_originador"], 30)          # 7    pos 47-76  Nome Originador
            + f.num(c["numero_banco"], 3)               # 8    pos 77-79  Número Banco
            + f.alfa(c["nome_banco"], 15)               # 9    pos 80-94  Nome Banco
            + data_gravacao                             # 10   pos 95-100 Data Gravação
            + f.alfa("", 8)                             # 11   pos 101-108 Branco
            + f.alfa(c["identificacao_sistema"], 2)     # 12   pos 109-110 Ident. Sistema
            + f.num(seq_arquivo, 7)                     # 13   pos 111-117 Nº Seq. Arquivo
            + f.num(c.get("numero_banco", 0), 3)        # 14   pos 118-120 Banco cedente
            + f.num(c.get("agencia_cedente", 0), 5)     # 15   pos 121-125 Agência cedente
            + f.num(c.get("dig_verificador", 0), 1)     # 16   pos 126    DV Agência
            + f.num(c.get("conta_corrente", 0), 12)     # 17   pos 127-138 Conta Corrente
            + f.num(c.get("dig_verificador_cc", 0), 1)  # 18   pos 139   DV Conta
        )  # total até aqui: 139 chars

        if self.is_qi:
            # QI: pos 140–377 Branco (237 chars)
            #      pos 378–391 CNPJ Emissor Original / duplo endosso (14 chars)
            #      pos 392–438 Branco (47 chars)
            # total 140–438 = 299 chars
            parte_variante = (
                f.alfa("", 238)                             # 19   pos 140-377 Branco (238)
                + f.num(c.get("cnpj_emissor_endosso", 0), 14) # 20  pos 378-391 CNPJ Emissor
                + f.alfa("", 47)                            # 21   pos 392-438 Branco (47)
            )
        else:
            # APEX: pos 140–438 todo branco (299 chars)
            parte_variante = (
                f.num(c.get("taxa", 0), 4)                 # pos 140-143 Taxa (campo legado APEX)
                + f.alfa("", 295)                          # pos 144-438 Branco (295)
            )

        linha = parte_comum + parte_variante + "000001"  # 439-444 Seq. Registro
        return self._valida_linha(linha)

    def _montar_campo_endereco(self, row: Dict) -> str:
        """Monta o bloco de 40 chars do endereço do sacado (pos 275–314).
        
        - APEX_444: campo único "Endereço Completo" (X40)
        - QI_444:   Logradouro (X16) + Bairro (X7) + Cidade (X15) + Estado (X2)
        """
        f = self.formatter
        if self.is_qi:
            return (
                f.alfa(row.get("LOGRADOURO", row.get("ENDERECO", "")), 16)  # 275-290
                + f.alfa(row.get("BAIRRO", ""), 7)                           # 291-297
                + f.alfa(row.get("CIDADE", ""), 15)                          # 298-312
                + f.alfa(row.get("ESTADO", ""), 2)                           # 313-314
            )
        else:
            # APEX: campo único; fallback para "X" se vazio
            end = row.get("ENDERECO")
            if end is None or (isinstance(end, float) and pd.isna(end)) or str(end).strip() == "":
                end = "X"
            return f.alfa(end, 40)  # 275-314

    def montar_detalhe(self, row: Dict, seq: int) -> str:
        f = self.formatter
        c = self.config
        
        nome_ced_fmt = f.alfa(row.get("NOME_CEDENTE", ""), 46)
        cnpj_ced_fmt = f.cnpj_cpf(row.get("DOC_CEDENTE", ""), 14)
        cedente_campo = nome_ced_fmt + cnpj_ced_fmt  # 60 chars

        linha = (
            "1"                                             # 1    pos 1       Ident. Registro
            + f.num(0, 6)                                   # 2    pos 2-7     Data Carência
            + f.num(c.get("tipo_juros", 0), 1)              # 3    pos 8       Tipo Juros
            + "  "                                          # 4    pos 9-10    Branco
            + f.num(c.get("taxa_juros", 0), 10)             # 5    pos 11-20   Taxa Juros
            + c["coobrigacao"]                              # 6    pos 21-22   Coobrigação
            + "00"                                          # 7    pos 23-24   Característica Especial
            + "0000"                                        # 8    pos 25-28   Modalidade Operação
            + "00"                                          # 9    pos 29-30   Natureza Operação
            + "0000"                                        # 10   pos 31-34   Origem Recurso
            + f.alfa("", 2)                                 # 11   pos 35-36   Classe Risco
            + "0"                                           # 12   pos 37      Zeros
            + f.alfa(str(row.get("SEU_NUMERO", "")), 25)    # 13   pos 38-62   Nº Controle Participante
            + "000"                                         # 14   pos 63-65   Número Banco (cheque)
            + "00000"                                       # 15   pos 66-70   Zeros
            + "00000000000"                                 # 16   pos 71-81   Ident. Título Banco
            + " "                                           # 17   pos 82      Dígito Nosso Número
            + f.num(row.get("VALOR_PAGO", 0), 10, 2)        # 18   pos 83-92   Valor Pago
            + " "                                           # 19   pos 93      Condição Emissão
            + " "                                           # 20   pos 94      Ident. Débito Aut.
            + f.data(row.get("DATA_LIQUIDACAO", None))      # 21   pos 95-100  Data Liquidação
            + f.alfa("", 4)                                 # 22   pos 101-104 Ident. Operação Banco
            + " "                                           # 23   pos 105     Indicador Rateio
            + " "                                           # 24   pos 106     Endereçamento Débito Aut.
            + f.alfa("", 2)                                 # 25   pos 107-108 Branco
            + f.num(row.get("IDENTIFICACAO_OCORRENCIA", c["identificacao_ocorrencia"]), 2)  # 26  pos 109-110
            + f.alfa(str(row.get("NU_DOCUMENTO", "")), 10)  # 27   pos 111-120 Nº Documento
            + f.data(row.get("DATA_VENCIMENTO_AJUSTADA"))   # 28   pos 121-126 Data Vencimento
            + f.num(row.get("VALOR_NOMINAL", 0), 13, 2)     # 29   pos 127-139 Valor Título (face)
            + "000"                                         # 30   pos 140-142 Banco Cobrança
            + "00000"                                       # 31   pos 143-147 Agência Depositária
            + self._get_especie(row.get("TIPO_RECEBIVEL"))  # 32   pos 148-149 Espécie Título
            + " "                                           # 33   pos 150     Identificação
            + f.data(row.get("DATA_EMISSAO"))               # 34   pos 151-156 Data Emissão
            + "00"                                          # 35   pos 157-158 1ª Instrução
            + "0"                                           # 36   pos 159     2ª Instrução
            + self._get_tipo_pessoa(row.get("DOC_CEDENTE")) # 37   pos 160-161 Tipo Pessoa Cedente
            + f.alfa("", 12)                                # 38   pos 162-173 Juros/Mora X(12)
            + f.alfa(_fmt_termo_cessao(row.get("TERMO_CESSAO", row.get("DATA_AQUISICAO", ""))), 19)  # 39 pos 174-192
            + f.num(row.get("VALOR_AQUISICAO", 0), 13, 2)   # 40   pos 193-205 Valor Presente Parcela
            + f.num(0, 13, 2)                               # 41   pos 206-218 Valor Abatimento
            + self._get_tipo_pessoa(row.get("DOC_SACADO"))  # 42   pos 219-220 Tipo Inscrição Sacado
            + f.cnpj_cpf(row.get("DOC_SACADO", ""), 14)     # 43   pos 221-234 Nº Inscrição Sacado
            + f.alfa(row.get("NOME_SACADO", ""), 40)        # 44   pos 235-274 Nome Sacado
            + self._montar_campo_endereco(row)              # 45   pos 275-314 Endereço (40 chars)
            + f.alfa("", 9)                                 # 46   pos 315-323 Nº NF Duplicata
            + f.alfa("", 3)                                 # 47   pos 324-326 Série NF
            + f.cep(row.get("CEP", ""))                     # 48   pos 327-334 CEP
            + cedente_campo                                 # 49   pos 335-394 Cedente (60)
            + f.alfa("", 44)                                # 50   pos 395-438 Chave NF-e
            + f.num(seq, 6)                                 # 51   pos 439-444 Nº Seq. Registro
        )
        return self._valida_linha(linha)

    def _get_df_column(self, df: pd.DataFrame, keys: List[str], fallback_default) -> pd.Series:
        for k in keys:
            if k in df.columns:
                return df[k]
            # Case-insensitive and stripped lookup
            for col in df.columns:
                if str(col).strip().upper() == k.upper():
                    return df[col]
        return fallback_default

    def _montar_campo_endereco_vec(self, df: pd.DataFrame, N: int) -> pd.Series:
        """Monta o bloco de 40 chars de endereço do sacado de forma vetorizada.
        
        - APEX_444: campo único Endereço (X40)
        - QI_444:   Logradouro (X16) + Bairro (X7) + Cidade (X15) + Estado (X2)
        """
        f = self.formatter_vec
        if self.is_qi:
            log_series = self._get_df_column(
                df, ["LOGRADOURO", "Logradouro", "ENDERECO", "Endereco", "ENDEREÇO"],
                pd.Series([""] * N, index=df.index)
            )
            bairro_series = self._get_df_column(
                df, ["BAIRRO", "Bairro"],
                pd.Series([""] * N, index=df.index)
            )
            cidade_series = self._get_df_column(
                df, ["CIDADE", "Cidade", "MUNICIPIO", "Municipio"],
                pd.Series([""] * N, index=df.index)
            )
            estado_series = self._get_df_column(
                df, ["ESTADO", "Estado", "UF", "Uf"],
                pd.Series([""] * N, index=df.index)
            )
            return (
                f.alfa(log_series, 16)
                .str.cat(f.alfa(bairro_series, 7))
                .str.cat(f.alfa(cidade_series, 15))
                .str.cat(f.alfa(estado_series, 2))
            )  # total: 40 chars
        else:
            end_series = self._get_df_column(
                df, ["ENDERECO", "Endereco", "ENDEREÇO"],
                pd.Series([""] * N, index=df.index)
            )
            end_cleaned = np.where(
                end_series.isna() | (end_series.astype(str).str.strip() == ""),
                "X", end_series.astype(str)
            )
            return f.alfa(pd.Series(end_cleaned, index=df.index), 40)

    def montar_detalhes_vectorized(self, df: pd.DataFrame, start_seq: int) -> pd.Series:
        """Monta registros de detalhe de forma totalmente vetorizada."""
        f = self.formatter_vec
        c = self.config
        N = len(df)
        
        # ── Campos estáticos (repetidos) ──────────────────────────────────────
        col1  = pd.Series(["1"] * N, index=df.index)
        col2  = pd.Series(["000000"] * N, index=df.index)           # pos 2-7   Data Carência
        col3  = pd.Series([self.formatter.num(c.get("tipo_juros", 0), 1)] * N, index=df.index)  # pos 8
        col4  = pd.Series(["  "] * N, index=df.index)               # pos 9-10  Branco
        col5  = pd.Series([self.formatter.num(c.get("taxa_juros", 0), 10)] * N, index=df.index) # pos 11-20
        col6  = pd.Series([c["coobrigacao"][:2]] * N, index=df.index)  # pos 21-22
        col7  = pd.Series(["000000000000  0"] * N, index=df.index)  # pos 23-37
        
        # ── Dados do Título ───────────────────────────────────────────────────
        col13 = f.alfa(self._get_df_column(df, ["SEU_NUMERO", "SEU NÚMERO", "Seu Numero"], pd.Series([""] * N, index=df.index)), 25)
        col14 = pd.Series(["0000000000000000000 "] * N, index=df.index)  # pos 63-82
        col18 = f.num(self._get_df_column(df, ["VALOR_PAGO", "Valor Pago", "VALOR PAGO"], pd.Series([0] * N, index=df.index)), 10, 2)
        col19 = pd.Series(["  "] * N, index=df.index)               # pos 93-94
        col21 = f.data(self._get_df_column(df, ["DATA_LIQUIDACAO", "Data Liquidacao", "DATA LIQUIDAÇÃO"], pd.Series([None] * N, index=df.index)))
        col22 = pd.Series(["        "] * N, index=df.index)         # pos 101-108
        
        # ── Ocorrência e Documento ────────────────────────────────────────────
        col26 = f.num(self._get_df_column(df, ["IDENTIFICACAO_OCORRENCIA", "Identificacao Ocorrencia", "IDENTIFICAÇÃO OCORRÊNCIA"], pd.Series([c["identificacao_ocorrencia"]] * N, index=df.index)), 2)
        col27 = f.alfa(self._get_df_column(df, ["NU_DOCUMENTO", "Nu Documento", "NU DOCUMENTO"], pd.Series([""] * N, index=df.index)), 10)
        col28 = f.data(self._get_df_column(df, ["DATA_VENCIMENTO_AJUSTADA", "Data Vencimento Ajustada", "DATA VENCIMENTO"], pd.Series([None] * N, index=df.index)))
        col29 = f.num(self._get_df_column(df, ["VALOR_NOMINAL", "Valor Nominal", "VALOR NOMINAL"], pd.Series([0] * N, index=df.index)), 13, 2)
        col30 = pd.Series(["00000000"] * N, index=df.index)         # pos 140-147
        
        # ── Espécie, Datas e Cedente ──────────────────────────────────────────
        col32 = self._get_especie_vectorized(self._get_df_column(df, ["TIPO_RECEBIVEL", "Tipo Recebivel", "TIPO RECEBÍVEL"], pd.Series([""] * N, index=df.index)))
        col33 = pd.Series([" "] * N, index=df.index)                # pos 150
        col34 = f.data(self._get_df_column(df, ["DATA_EMISSAO", "Data Emissao", "DATA EMISSÃO"], pd.Series([None] * N, index=df.index)))
        col35 = pd.Series(["000"] * N, index=df.index)              # pos 157-159
        col37 = f.tipo_pessoa(self._get_df_column(df, ["DOC_CEDENTE", "Doc Cedente"], pd.Series([""] * N, index=df.index)))
        col38 = pd.Series(["000000000000"] * N, index=df.index)     # pos 162-173
        
        # ── Termo de Cessão ───────────────────────────────────────────────────
        termo_cessao   = self._get_df_column(df, ["TERMO_CESSAO", "Termo Cessao", "TERMO CESSÃO"], pd.Series([None] * N, index=df.index)).fillna("")
        data_aquisicao = self._get_df_column(df, ["DATA_AQUISICAO", "Data Aquisicao", "DATA AQUISIÇÃO"], pd.Series([None] * N, index=df.index)).fillna("")
        if pd.api.types.is_datetime64_any_dtype(data_aquisicao) or (isinstance(data_aquisicao, pd.Series) and data_aquisicao.dtype == 'datetime64[ns]'):
            aquis_str = data_aquisicao.dt.strftime("%d%m%y").fillna("")
        else:
            s_raw = data_aquisicao.astype(str).str.strip()
            invalidos = {"NaT", "nan", "None", "none", "", "NAN", "NAT"}
            mask_dt = ~s_raw.isin(invalidos)
            dt_parsed = pd.to_datetime(s_raw[mask_dt], errors="coerce")
            s_fmt = s_raw.copy()
            s_fmt[mask_dt] = np.where(dt_parsed.notna(), dt_parsed.dt.strftime("%d%m%y"), s_raw[mask_dt])
            aquis_str = s_fmt.where(~s_raw.isin(invalidos), "")
        termo_combined = np.where(termo_cessao.astype(str).str.strip() != "", termo_cessao.astype(str), aquis_str)
        col39 = f.alfa(pd.Series(termo_combined, index=df.index), 19)
        
        col40 = f.num(self._get_df_column(df, ["VALOR_AQUISICAO", "Valor Aquisicao", "VALOR AQUISIÇÃO", "VALOR_PRESENTE", "Valor Presente", "VALOR PRESENTE"], pd.Series([0] * N, index=df.index)), 13, 2)
        col41 = pd.Series(["0000000000000"] * N, index=df.index)    # pos 206-218
        
        # ── Sacado ────────────────────────────────────────────────────────────
        col42 = f.tipo_pessoa(self._get_df_column(df, ["DOC_SACADO", "Doc Sacado"], pd.Series([""] * N, index=df.index)))
        col43 = f.cnpj_cpf(self._get_df_column(df, ["DOC_SACADO", "Doc Sacado"], pd.Series([""] * N, index=df.index)), 14)
        col44 = f.alfa(self._get_df_column(df, ["NOME_SACADO", "Nome Sacado"], pd.Series([""] * N, index=df.index)), 40)
        
        # ── Endereço (40 chars — layout varia por variante) ───────────────────
        col45 = self._montar_campo_endereco_vec(df, N)
        
        # ── CEP e Cedente ─────────────────────────────────────────────────────
        col46 = pd.Series(["            "] * N, index=df.index)     # pos 315-326 (NF + série)
        col47 = f.cep(self._get_df_column(df, ["CEP", "Cep"], pd.Series([""] * N, index=df.index)))
        
        nome_ced_fmt = f.alfa(self._get_df_column(df, ["NOME_CEDENTE", "Nome Cedente"], pd.Series([""] * N, index=df.index)), 46)
        cnpj_ced_fmt = f.cnpj_cpf(self._get_df_column(df, ["DOC_CEDENTE", "Doc Cedente"], pd.Series([""] * N, index=df.index)), 14)
        col48 = nome_ced_fmt.str.cat(cnpj_ced_fmt)                  # 60 chars pos 335-394
        
        col49 = pd.Series([" " * 44] * N, index=df.index)           # pos 395-438 Chave NF-e
        
        # ── Sequencial incremental ────────────────────────────────────────────
        seq_nums = pd.Series(range(start_seq, start_seq + N), index=df.index).astype(str).str.zfill(6)
        col50 = seq_nums
        
        # ── Concatenação em lote ──────────────────────────────────────────────
        lines = col1.str.cat([
            col2, col3, col4, col5, col6, col7, col13, col14,
            col18, col19, col21, col22, col26, col27, col28, col29,
            col30, col32, col33, col34, col35, col37, col38, col39,
            col40, col41, col42, col43, col44, col45, col46, col47,
            col48, col49, col50
        ])
        return lines

    def montar_trailer(self, seq_total: int) -> str:
        linha = (
            "9"                                         # 1
            + self.formatter.alfa("", 437)              # 2-438
            + self.formatter.num(seq_total, 6)           # 439-444
        )
        return self._valida_linha(linha)

    def converter(self, df: pd.DataFrame) -> List[str]:
        """Converte um DataFrame para uma lista de linhas CNAB (vetorizado)."""
        header = self.montar_header(self.config["nr_sequencial_arquivo"])
        
        if len(df) > 0:
            linhas_detalhe = self.montar_detalhes_vectorized(df, start_seq=2).tolist()
        else:
            linhas_detalhe = []
            
        trailer = self.montar_trailer(len(linhas_detalhe) + 2)
        return [header] + linhas_detalhe + [trailer]

    def converter_para_fluxo(self, df: pd.DataFrame, out_stream, chunk_size: int = 50000):
        """Converte o DataFrame em blocos (chunks) e grava diretamente no fluxo."""
        # 1. Header
        header = self.montar_header(self.config["nr_sequencial_arquivo"])
        out_stream.write(header + "\r\n")
        
        # 2. Detalhes em pedaços (chunks)
        total_registros = len(df)
        for start_idx in range(0, total_registros, chunk_size):
            chunk = df.iloc[start_idx : start_idx + chunk_size]
            # O sequencial de detalhe começa em start_idx + 2
            linhas_chunk = self.montar_detalhes_vectorized(chunk, start_seq=start_idx + 2)
            
            # Grava as linhas separadas por quebra de linha CNAB
            out_stream.write("\r\n".join(linhas_chunk) + "\r\n")
            
        # 3. Trailer
        # O sequencial total de linhas é header (1) + total_registros + trailer (1) = total_registros + 2
        trailer = self.montar_trailer(total_registros + 2)
        out_stream.write(trailer + "\r\n")

    def get_conteudo(self, linhas: List[str]) -> str:
        """Retorna o conteúdo formatado para gravação no arquivo."""
        return "\r\n".join(linhas) + "\r\n"

    def salvar(self, linhas: List[str], caminho_saida: str):
        """Salva as linhas em um arquivo."""
        with open(caminho_saida, "w", encoding="ascii", errors="replace", newline="") as f:
            f.write(self.get_conteudo(linhas))
