import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any
# pyrefly: ignore [missing-import]
from src.global_var import MAP_ESPECIE_TITULO

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
    """Conversor de Excel/CSV para CNAB 444 (BRL Trust FIDC)."""
    
    LINE_SIZE = 444

    def __init__(self, config: Dict):
        self.config = config
        self.formatter = CNABFormatter()
        self.formatter_vec = CNABFormatterVectorized()
        # Converte o mapa do global_var (int: desc) para (desc_upper: cod_str)
        self.mapa_especies = {
            v.upper(): str(k).zfill(2) for k, v in MAP_ESPECIE_TITULO.items()
        }

    def _valida_linha(self, linha: str) -> str:
        if len(linha) != self.LINE_SIZE:
            raise ValueError(f"Linha inválida: {len(linha)} caracteres (esperado {self.LINE_SIZE})")
        return linha

    def _get_especie(self, tipo: str) -> str:
        if not tipo or pd.isna(tipo):
            return "01"
            
        chave = str(tipo).upper().strip()
        
        primeira_parte = chave.split('-')[0].strip().split()[0]
        if primeira_parte.isdigit():
            return primeira_parte.zfill(2)[:2]
            
        chave = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in chave)
        return self.mapa_especies.get(chave, "01")

    def _get_especie_vectorized(self, series: pd.Series) -> pd.Series:
        s = series.fillna("").astype(str).str.upper().str.strip()
        token1 = s.str.split('-').str[0].str.strip().str.split().str[0].fillna("")
        is_digit = token1.str.isdigit()
        
        cleaned_chars = s.str.replace(r'[^A-Z0-9 ]', ' ', regex=True)
        mapped = cleaned_chars.map(self.mapa_especies).fillna("01")
        
        result = np.where(is_digit, token1.str.zfill(2).str.slice(-2), mapped)
        return pd.Series(result, index=series.index)

    def _get_tipo_pessoa(self, doc: str) -> str:
        s = ''.join(filter(str.isdigit, str(doc))) if doc else ""
        return "01" if len(s) <= 11 else "02"

    def montar_header(self, seq_arquivo: int, data_gravacao: Optional[str] = None) -> str:
        if data_gravacao is None:
            data_gravacao = datetime.today().strftime("%d%m%y")
            
        f = self.formatter
        c = self.config
        
        linha = (
            "0"                                         # 1
            + "1"                                       # 2
            + f.alfa("REMESSA", 7)                      # 3-9
            + "01"                                      # 10-11
            + f.alfa("COBRANCA", 15)                    # 12-26
            + f.num(c["codigo_originador"], 20)         # 27-46
            + f.alfa(c["nome_originador"], 30)          # 47-76
            + f.num(c["numero_banco"], 3)               # 77-79
            + f.alfa(c["nome_banco"], 15)               # 80-94
            + data_gravacao                             # 95-100
            + f.alfa("", 8)                             # 101-108
            + f.alfa(c["identificacao_sistema"], 2)     # 109-110
            + f.num(seq_arquivo, 7)                     # 111-117
            + f.alfa("", 2)                             # 118-119
            + f.num(c.get("agencia_cedente", 0), 5)     # 120-124
            + f.num(c.get("dig_verificador", 0), 1)     # 125-125
            + f.num(c.get("conta_corrente", 0), 12)     # 126-137
            + f.num(c.get("dig_verificador_cc", 0), 1)  # 138-138
            + f.num(c.get("taxa", 0), 4)                # 139-142 Taxa
            + f.alfa("", 296)                           # 143-438 Branco
            + "000001"                                  # 439-444
        )
        return self._valida_linha(linha)

    def montar_detalhe(self, row: Dict, seq: int) -> str:
        f = self.formatter
        c = self.config
        
        nome_ced_fmt = f.alfa(row.get("NOME_CEDENTE", ""), 46)
        cnpj_ced_fmt = f.cnpj_cpf(row.get("DOC_CEDENTE", ""), 14)
        cedente_campo = nome_ced_fmt + cnpj_ced_fmt  # 60 chars

        linha = (
            "1"                                             # 1
            + f.num(0, 6)                                   # 2-7 Data Carencia
            + f.num(c.get("tipo_juros", 0), 1)              # 8 Tipo Juros
            + "  "                                          # 9-10 Branco
            + f.num(c.get("taxa_juros", 0), 10)             # 11-20 Taxa Juros
            + c["coobrigacao"]                              # 21-22
            + "00"                                          # 23-24
            + "0000"                                        # 25-28
            + "00"                                          # 29-30
            + "0000"                                        # 31-34
            + f.alfa("", 2)                                 # 35-36
            + "0"                                           # 37
            + f.alfa(str(row.get("SEU_NUMERO", "")), 25)    # 38-62
            + "000"                                         # 63-65
            + "00000"                                       # 66-70
            + "00000000000"                                 # 71-81
            + " "                                           # 82
            + f.num(row.get("VALOR_PAGO", 0), 10, 2)        # 83-92
            + " "                                           # 93
            + " "                                           # 94
            + f.data(row.get("DATA_LIQUIDACAO", None))      # 95-100 (Liquidação)
            + f.alfa("", 4)                                 # 101-104
            + " "                                           # 105
            + " "                                           # 106 (Branco - End Aviso)
            + f.alfa("", 2)                                 # 107-108
            + f.num(row.get("IDENTIFICACAO_OCORRENCIA", c["identificacao_ocorrencia"]), 2) # 109-110
            + f.alfa(str(row.get("NU_DOCUMENTO", "")), 10) # 111-120
            + f.data(row.get("DATA_VENCIMENTO_AJUSTADA"))   # 121-126
            + f.num(row.get("VALOR_NOMINAL", 0), 13, 2)     # 127-139
            + "000"                                         # 140-142
            + "00000"                                       # 143-147
            + self._get_especie(row.get("TIPO_RECEBIVEL"))  # 148-149
            + " "                                           # 150
            + f.data(row.get("DATA_EMISSAO"))               # 151-156
            + "00"                                          # 157-158
            + "0"                                           # 159
            + self._get_tipo_pessoa(row.get("DOC_CEDENTE")) # 160-161
            + f.alfa("", 12)                                # 162-173 (Juros/Mora X(12))
            + f.alfa(str(row.get("TERMO_CESSAO", row.get("DATA_AQUISICAO", ""))), 19) # 174-192
            + f.num(row.get("VALOR_AQUISICAO", 0), 13, 2)   # 193-205
            + f.num(0, 13, 2)                               # 206-218
            + self._get_tipo_pessoa(row.get("DOC_SACADO"))  # 219-220
            + f.cnpj_cpf(row.get("DOC_SACADO", ""), 14)     # 221-234
            + f.alfa(row.get("NOME_SACADO", ""), 40)        # 235-274
            + f.alfa(row.get("ENDERECO") if pd.notna(row.get("ENDERECO")) and str(row.get("ENDERECO")).strip() else "X", 40) # 275-314
            + f.alfa("",9)                                 # 315-323
            + f.alfa("", 3)                                 # 324-326
            + f.cep(row.get("CEP", ""))                     # 327-334
            + cedente_campo                                 # 335-394
            + f.alfa("", 44)                                # 395-438
            + f.num(seq, 6)                                 # 439-444
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

    def montar_detalhes_vectorized(self, df: pd.DataFrame, start_seq: int) -> pd.Series:
        """Monta registros de detalhe de forma totalmente vetorizada."""
        f = self.formatter_vec
        c = self.config
        N = len(df)
        
        # Colunas Estáticas repetidas
        col1 = pd.Series(["1"] * N, index=df.index)
        col2 = pd.Series(["000000"] * N, index=df.index)
        col3 = pd.Series([self.formatter.num(c.get("tipo_juros", 0), 1)] * N, index=df.index)
        col4 = pd.Series(["  "] * N, index=df.index)
        col5 = pd.Series([self.formatter.num(c.get("taxa_juros", 0), 10)] * N, index=df.index)
        col6 = pd.Series([c["coobrigacao"][:2]] * N, index=df.index)
        col7 = pd.Series(["000000000000  0"] * N, index=df.index) # pos 23-37
        
        # Dados do Título (com busca tolerante de cabeçalhos)
        col13 = f.alfa(self._get_df_column(df, ["SEU_NUMERO", "SEU NÚMERO", "Seu Numero"], pd.Series([""] * N, index=df.index)), 25)
        col14 = pd.Series(["0000000000000000000 "] * N, index=df.index) # pos 63-82
        col18 = f.num(self._get_df_column(df, ["VALOR_PAGO", "Valor Pago", "VALOR PAGO"], pd.Series([0] * N, index=df.index)), 10, 2)
        col19 = pd.Series(["  "] * N, index=df.index)
        col21 = f.data(self._get_df_column(df, ["DATA_LIQUIDACAO", "Data Liquidacao", "DATA LIQUIDAÇÃO"], pd.Series([None] * N, index=df.index)))
        col22 = pd.Series(["        "] * N, index=df.index)
        
        # Ocorrência e Documento
        col26 = f.num(self._get_df_column(df, ["IDENTIFICACAO_OCORRENCIA", "Identificacao Ocorrencia", "IDENTIFICAÇÃO OCORRÊNCIA"], pd.Series([c["identificacao_ocorrencia"]] * N, index=df.index)), 2)
        col27 = f.alfa(self._get_df_column(df, ["NU_DOCUMENTO", "Nu Documento", "NU DOCUMENTO"], pd.Series([""] * N, index=df.index)), 10)
        col28 = f.data(self._get_df_column(df, ["DATA_VENCIMENTO_AJUSTADA", "Data Vencimento Ajustada", "DATA VENCIMENTO"], pd.Series([None] * N, index=df.index)))
        col29 = f.num(self._get_df_column(df, ["VALOR_NOMINAL", "Valor Nominal", "VALOR NOMINAL"], pd.Series([0] * N, index=df.index)), 13, 2)
        col30 = pd.Series(["00000000"] * N, index=df.index)
        
        # Espécie
        col32 = self._get_especie_vectorized(self._get_df_column(df, ["TIPO_RECEBIVEL", "Tipo Recebivel", "TIPO RECEBÍVEL"], pd.Series([""] * N, index=df.index)))
        col33 = pd.Series([" "] * N, index=df.index)
        col34 = f.data(self._get_df_column(df, ["DATA_EMISSAO", "Data Emissao", "DATA EMISSÃO"], pd.Series([None] * N, index=df.index)))
        col35 = pd.Series(["000"] * N, index=df.index)
        col37 = f.tipo_pessoa(self._get_df_column(df, ["DOC_CEDENTE", "Doc Cedente"], pd.Series([""] * N, index=df.index)))
        col38 = pd.Series(["000000000000"] * N, index=df.index)
        
        # Termo de Cessão
        termo_cessao = self._get_df_column(df, ["TERMO_CESSAO", "Termo Cessao", "TERMO CESSÃO"], pd.Series([None] * N, index=df.index)).fillna("")
        data_aquisicao = self._get_df_column(df, ["DATA_AQUISICAO", "Data Aquisicao", "DATA AQUISIÇÃO"], pd.Series([None] * N, index=df.index)).fillna("")
        if pd.api.types.is_datetime64_any_dtype(data_aquisicao) or (isinstance(data_aquisicao, pd.Series) and data_aquisicao.dtype == 'datetime64[ns]'):
            aquis_str = data_aquisicao.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
        else:
            aquis_str = data_aquisicao.astype(str).replace("NaT", "")
        termo_combined = np.where(termo_cessao.astype(str).str.strip() != "", termo_cessao.astype(str), aquis_str)
        col39 = f.alfa(pd.Series(termo_combined, index=df.index), 19)
        
        col40 = f.num(self._get_df_column(df, ["VALOR_AQUISICAO", "Valor Aquisicao", "VALOR AQUISIÇÃO", "VALOR_PRESENTE", "Valor Presente", "VALOR PRESENTE"], pd.Series([0] * N, index=df.index)), 13, 2)
        col41 = pd.Series(["0000000000000"] * N, index=df.index)
        
        # Sacado e Endereço
        col42 = f.tipo_pessoa(self._get_df_column(df, ["DOC_SACADO", "Doc Sacado"], pd.Series([""] * N, index=df.index)))
        col43 = f.cnpj_cpf(self._get_df_column(df, ["DOC_SACADO", "Doc Sacado"], pd.Series([""] * N, index=df.index)), 14)
        col44 = f.alfa(self._get_df_column(df, ["NOME_SACADO", "Nome Sacado"], pd.Series([""] * N, index=df.index)), 40)
        
        end_series = self._get_df_column(df, ["ENDERECO", "Endereco", "ENDEREÇO"], pd.Series([""] * N, index=df.index))
        end_cleaned = np.where(end_series.isna() | (end_series.astype(str).str.strip() == ""), "X", end_series.astype(str))
        col45 = f.alfa(pd.Series(end_cleaned, index=df.index), 40)
        
        # CEP e Cedente
        col46 = pd.Series(["            "] * N, index=df.index)
        col47 = f.cep(self._get_df_column(df, ["CEP", "Cep"], pd.Series([""] * N, index=df.index)))
        
        nome_ced_fmt = f.alfa(self._get_df_column(df, ["NOME_CEDENTE", "Nome Cedente"], pd.Series([""] * N, index=df.index)), 46)
        cnpj_ced_fmt = f.cnpj_cpf(self._get_df_column(df, ["DOC_CEDENTE", "Doc Cedente"], pd.Series([""] * N, index=df.index)), 14)
        col48 = nome_ced_fmt.str.cat(cnpj_ced_fmt)
        
        col49 = pd.Series([" " * 44] * N, index=df.index)
        
        # Sequencial incremental
        seq_nums = pd.Series(range(start_seq, start_seq + N), index=df.index).astype(str).str.zfill(6)
        col50 = seq_nums
        
        # Concatenação das colunas em lote
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
