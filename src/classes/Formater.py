import humanize
import pandas as pd
from src.global_var import MAP_CEDENTE 
import re
from datetime import datetime

class Formater:
    
    @classmethod
    def definir_tipo_cedente(cls,df):
        tipos_existentes = df['tipo_cedente'].map(MAP_CEDENTE).unique()

        if len(tipos_existentes) > 1:
            return "Multscedente"
        elif len(tipos_existentes) == 1:
            return  tipos_existentes[0]
        else:
            return "Não foi encontrado código correto do tipo de cedente"
        
    @classmethod
    def format_br(cls,valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    
    @classmethod
    def formatar_moeda(valor: float) -> str:
        """Formata valor para padrão monetário brasileiro."""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    @classmethod
    def formatar_percentual(valor: float) -> str:
        """Formata valor para percentual brasileiro."""
        return f"{valor*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    @staticmethod
    def formatar_numero(valor: float) -> str:
        """Formata valor para padrão monetário brasileiro."""
        return f"{valor:,.0f}".replace(",", ".")
    
    def formatar_numero_decimal(valor: float) -> str:
        """Formata valor para padrão monetário com casas decimais."""
        return f"{valor:,.2f}".replace(",", ".")
    
    @classmethod
    def formatar_pl_humano(valor):
        try:
            # 1. Garante que o valor seja numérico (float/int)
            valor_num = pd.to_numeric(valor, errors='coerce')
            
            if pd.isna(valor_num) or valor_num == 0:
                return "R$ 0,00"                
            # 2. Transforma 1.000.000 em "1,0 milhão"
            res = humanize.intword(valor_num)
            return f"R$ {res}"
            
        except Exception as e: # 'Exception' com E maiúsculo e sem erro de grafia
            print(f"Erro na formatação: {e}")
            return "R$ 0,00"
    
    @classmethod
    def definir_tipo_documento(cls,valor):
        if valor == 1:
            return 'Pessoa Fisica'
        else: 
            return 'Pessoa Juridica'

    
    @classmethod
    def format_cnab_data(cls, data_str):
        if not data_str or data_str == "000000":
            return "-"
        dt = datetime.strptime(data_str, "%d%m%y")
        return dt.strftime("%d/%m/%Y")
    
    
    
    @classmethod
    def format_documento(cls,doc):
        """Formata string numérica para CPF ou CNPJ baseado no tamanho."""
        doc = re.sub(r'\D', '', str(doc))
        
        # CPF: 11 dígitos
        if len(doc) == 11:
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        
        # CNPJ: 14 dígitos
        if len(doc) == 14:
            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
        
        return doc