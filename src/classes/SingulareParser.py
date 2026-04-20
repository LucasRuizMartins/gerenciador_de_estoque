from datetime import datetime
import pandas as pd 
from src.classes.CnabPaser import CNABParser

class SingulareParser(CNABParser):

    def parse_header(self):
        data_cnab = datetime.strptime(self.header[94:100], "%d%m%y")

        return {
            "banco": self.header[79:94].strip(),
            "data_operacao": data_cnab,
            "numero_banco": self.header[76:79],
            "gestora": self.header[46:76].strip()
        }

    def parse_body(self):
        lista = []
        erros = []

        for i, linha in enumerate(self.corpo):
            try:
                registro = {
                    'numero_doc': linha[110:120].strip(),
                    'seu_numero': linha[37:62].strip(),
                    'identificacao_ocorrencia': linha[108:110].strip(),
                    'data_vencimento': linha[120:126].strip(),
                    'valor_nominal': float(linha[126:139]) / 100,
                    'valor_presente': float(linha[192:205]) / 100,
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