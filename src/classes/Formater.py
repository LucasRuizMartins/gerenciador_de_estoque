"""Classe de formatação — wrapper de retrocompatibilidade.

Delega para src.formatting (módulo de funções puras).
Mantido para não quebrar imports existentes como:
    from src.classes.Formater import Formater as fmt
"""

import re
from datetime import datetime
import pandas as pd
# pyrefly: ignore [missing-import]
from src.global_var import MAP_CEDENTE
# pyrefly: ignore [missing-import]
from src.formatting import (
    fmt_moeda,
    fmt_numero,
    fmt_numero_decimal,
    fmt_pct_2d,
    fmt_pl_humano,
    fmt_documento,
)


class Formater:
    """Wrapper de retrocompatibilidade. Prefira importar de src.formatting."""

    # ── Formatações financeiras (delegam para src.formatting) ──

    format_br = staticmethod(fmt_moeda)
    formatar_moeda = staticmethod(fmt_moeda)
    formatar_percentual = staticmethod(fmt_pct_2d)
    formatar_numero = staticmethod(fmt_numero)
    formatar_numero_decimal = staticmethod(fmt_numero_decimal)
    formatar_pl_humano = staticmethod(fmt_pl_humano)
    format_documento = staticmethod(fmt_documento)

    # ── Formatações específicas de domínio ──

    @staticmethod
    def definir_tipo_cedente(df):
        tipos_existentes = df['tipo_cedente'].map(MAP_CEDENTE).unique()
        if len(tipos_existentes) > 1:
            return "Multscedente"
        elif len(tipos_existentes) == 1:
            return tipos_existentes[0]
        else:
            return "Não foi encontrado código correto do tipo de cedente"

    @staticmethod
    def definir_tipo_documento(valor):
        if valor == 1:
            return 'Pessoa Fisica'
        else:
            return 'Pessoa Juridica'

    @staticmethod
    def format_cnab_data(data_str):
        if not data_str or data_str == "000000":
            return "-"
        dt = datetime.strptime(data_str, "%d%m%y")
        return dt.strftime("%d/%m/%Y")