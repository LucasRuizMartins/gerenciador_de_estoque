import pandas as pd
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Union
from src.global_var import MAP_ESPECIE_TITULO

class CNABFormatter:
    """Utilitários de formatação para arquivos CNAB."""

    @staticmethod
    def num(valor: any, tamanho: int, decimais: int = 0) -> str:
        """Campo numérico: alinhado à direita, zeros à esquerda."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            valor = 0
        if decimais > 0:
            valor = round(float(valor) * (10 ** decimais))
        valor = int(valor)
        return str(valor).zfill(tamanho)[-tamanho:]

    @staticmethod
    def alfa(valor: any, tamanho: int) -> str:
        """Campo alfanumérico: maiúsculo, sem acento, alinhado à esquerda."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            valor = ""
        valor = str(valor).upper()
        
        replacements = {
            'Á':'A','À':'A','Â':'A','Ã':'A','Ä':'A',
            'É':'E','È':'E','Ê':'E','Ë':'E',
            'Í':'I','Ì':'I','Î':'I','Ï':'I',
            'Ó':'O','Ò':'O','Ô':'O','Õ':'O','Ö':'O',
            'Ú':'U','Ù':'U','Û':'U','Ü':'U',
            'Ç':'C','Ñ':'N',
        }
        for k, v in replacements.items():
            valor = valor.replace(k, v)
        
        # Remove caracteres especiais mantendo básicos
        valor = ''.join(c if c.isalnum() or c in ' .-/,' else ' ' for c in valor)
        return valor[:tamanho].ljust(tamanho)

    @staticmethod
    def data(valor: any) -> str:
        """Formata data para DDMMAA de forma robusta."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return "000000"
        
        try:
            # Se já for datetime ou date
            if isinstance(valor, (datetime, date)):
                return valor.strftime("%d%m%y")
            
            # Tenta converter usando pandas (que é muito flexível)
            dt = pd.to_datetime(valor, errors='coerce')
            if pd.notna(dt):
                return dt.strftime("%d%m%y")
                
        except Exception:
            pass
            
        return "000000"

    @staticmethod
    def cep(valor: any) -> str:
        """Remove hífen e garante 8 dígitos."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return "00000000"
        s = ''.join(filter(str.isdigit, str(valor)))
        return s.zfill(8)[:8]

    @staticmethod
    def cnpj_cpf(valor: any, tamanho: int = 14) -> str:
        """Remove pontuação e retorna só dígitos."""
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return "0" * tamanho
        s = ''.join(filter(str.isdigit, str(valor)))
        return s.zfill(tamanho)[-tamanho:]


class CNAB444Converter:
    """Conversor de Excel para CNAB 444 (BRL Trust FIDC)."""
    
    LINE_SIZE = 444

    def __init__(self, config: Dict):
        self.config = config
        self.formatter = CNABFormatter()
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
        chave = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in chave)
        return self.mapa_especies.get(chave, "01")

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
            + f.alfa("", 300)                           # 139-438 (Aumentado de 299 para 300 para fechar 444)
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
            + f.alfa("", 19)                                # 2-20
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
            + f.data(row.get("DATA_VENCIMENTO_AJUSTADA"))   # 95-100
            + f.alfa("", 4)                                 # 101-104
            + " "                                           # 105
            + "0"                                           # 106
            + f.alfa("", 2)                                 # 107-108
            + f.num(row.get("IDENTIFICACAO_OCORRENCIA", c["identificacao_ocorrencia"]), 2) # 109-110
            + f.alfa(str(row.get("NU_DOCUMENTO", "")), 10)  # 111-120
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
            + "000000000000"                                # 162-173
            + f.alfa(f.data(row.get("DATA_AQUISICAO")), 19) # 174-192
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

    def montar_trailer(self, seq_total: int) -> str:
        linha = (
            "9"                                         # 1
            + self.formatter.alfa("", 437)              # 2-438
            + self.formatter.num(seq_total, 6)           # 439-444
        )
        return self._valida_linha(linha)

    def converter(self, df: pd.DataFrame) -> List[str]:
        """Converte um DataFrame para uma lista de linhas CNAB."""
        linhas = []
        
        # Header
        linhas.append(self.montar_header(self.config["nr_sequencial_arquivo"]))
        
        # Detalhes
        for i, row in df.iterrows():
            seq = i + 2
            linhas.append(self.montar_detalhe(row.to_dict(), seq))
            
        # Trailer
        linhas.append(self.montar_trailer(len(linhas) + 1))
        
        return linhas

    def get_conteudo(self, linhas: List[str]) -> str:
        """Retorna o conteúdo formatado para gravação no arquivo."""
        return "\r\n".join(linhas) + "\r\n"

    def salvar(self, linhas: List[str], caminho_saida: str):
        """Salva as linhas em um arquivo."""
        with open(caminho_saida, "w", encoding="ascii", errors="replace") as f:
            f.write(self.get_conteudo(linhas))
