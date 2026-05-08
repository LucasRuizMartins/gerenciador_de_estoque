from datetime import datetime
import pandas as pd 
from src.classes.CnabParser import CNABParser

class SingulareParser(CNABParser):
    """
    Parser especializado para o layout da Singulare.
    Processa arquivos CNAB 444 extraindo dados de liquidação e estoque.
    """

    def parse_header(self):
        """Extrai metadados do header do arquivo."""
        data_cnab = datetime.strptime(self.header[94:100], "%d%m%y")

        return {
            "banco": self.header[79:94].strip(),
            "data_operacao": data_cnab,
            "numero_banco": self.header[76:79],
            "gestora": self.header[46:76].strip()
        }

    def _safe_float(self, valor_str: str) -> float:
        """Converte string para float com segurança, retornando 0.0 em caso de erro."""
        try:
            limpo = valor_str.strip()
            if not limpo:
                return 0.0
            return float(limpo)
        except (ValueError, TypeError):
            return 0.0

    def parse_body(self):
        """Itera sobre as linhas do corpo e extrai os campos de cada registro."""
        lista = []
        erros = []

        for i, linha in enumerate(self.corpo):
            try:
                # Layout posicional (CNAB 444)
                registro = {
                    'numero_doc': linha[110:120].strip(),
                    'seu_numero': linha[37:62].strip(),
                    'identificacao_ocorrencia': linha[108:110].strip(),
                    'valor_pago': self._safe_float(linha[82:92]) / 100,
                    'especie_titulo': linha[147:149].strip(),
                    'data_vencimento': linha[120:126].strip(),
                    'valor_nominal': self._safe_float(linha[126:139]) / 100,
                    'valor_presente': self._safe_float(linha[192:205]) / 100,
                    'cedente': linha[334:380].strip(),
                    'doc_cedente': linha[380:394].strip(),
                    'tipo_cedente': linha[159:161].strip(),
                    'sacado': linha[234:274].strip(),
                    'doc_sacado': linha[220:234].strip(),
                    'tipo_sacado': linha[218:220].strip(),
                }
                lista.append(registro)
            except Exception as e:
                erros.append(f"Linha {i+2}: {e}")

        return {
            "dataframe": pd.DataFrame(lista),
            "erros": erros
        }