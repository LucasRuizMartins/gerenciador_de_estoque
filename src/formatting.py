"""Módulo centralizado de formatação para dados financeiros brasileiros.

Todas as funções seguem o padrão brasileiro:
  - Moeda: R$ 1.234,56
  - Percentual: 12,34%
  - Número: 1.234
  - Documento: CPF (xxx.xxx.xxx-xx) ou CNPJ (xx.xxx.xxx/xxxx-xx)

Uso:
    from src.formatting import fmt_moeda, fmt_pct, fmt_numero
"""

import re
import humanize
import pandas as pd

humanize.activate("pt_BR")


def fmt_moeda(valor) -> str:
    """Formata valor para padrão monetário brasileiro (R$ 1.234,56)."""
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ -"


def fmt_numero(valor) -> str:
    """Formata inteiro com separador de milhar brasileiro (1.234)."""
    try:
        return f"{int(float(valor)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"


def fmt_numero_decimal(valor) -> str:
    """Formata valor com 2 casas decimais no padrão brasileiro (1.234,56)."""
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"


def fmt_pct(valor) -> str:
    """Formata valor como percentual (12,3%)."""
    try:
        return f"{float(valor):.1%}"
    except (ValueError, TypeError):
        return "-"


def fmt_pct_2d(valor) -> str:
    """Formata valor como percentual com 2 decimais (12,34%)."""
    try:
        return f"{float(valor)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00%"


def fmt_pl_humano(valor) -> str:
    """Formata valor monetário de forma legível (ex: R$ 1,5 milhão)."""
    try:
        valor_num = pd.to_numeric(valor, errors='coerce')
        if pd.isna(valor_num) or valor_num == 0:
            return "R$ 0,00"
        res = humanize.intword(valor_num)
        return f"R$ {res}"
    except Exception:
        return "R$ 0,00"


def fmt_documento(doc) -> str:
    """Formata string numérica para CPF (11 dígitos) ou CNPJ (14 dígitos)."""
    doc = re.sub(r'\\D', '', str(doc))
    if len(doc) == 11:
        return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
    if len(doc) == 14:
        return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
    return doc
