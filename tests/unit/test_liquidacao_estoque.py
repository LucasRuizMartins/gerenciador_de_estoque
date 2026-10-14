from datetime import date

import pandas as pd

from src.classes import liquidacao_estoque as liq
from src.classes.cnab444_converter import CNAB444Converter

CONFIG = {
    "codigo_originador": "1", "nome_originador": "ORIG", "numero_banco": "1",
    "nome_banco": "BANCO", "identificacao_sistema": "MX", "coobrigacao": "01",
    "identificacao_ocorrencia": "75", "nr_sequencial_arquivo": 1,
}


def _estoque():
    return pd.DataFrame({
        "NOME_CEDENTE": ["CED"] * 3, "DOC_CEDENTE": ["12345678000199"] * 3,
        "NOME_SACADO": ["A", "B", "C"], "DOC_SACADO": ["11122233344"] * 3,
        "TIPO_RECEBIVEL": ["Duplicata Mercantil", "CHEQUE", "Xpto"],
        "VALOR_NOMINAL": ["1.234,56", "100,00", "50,00"],
        "DATA_VENCIMENTO_AJUSTADA": ["10/10/2026", "09/10/2026", "10/10/2026"],
        "DATA_EMISSAO": ["01/09/2026"] * 3, "DATA_AQUISICAO": ["02/09/2026"] * 3,
        "NU_DOCUMENTO": ["1", "2", "3"], "SEU_NUMERO": ["1", "2", "3"],
    })


def test_mapeamento_tipo():
    assert liq.mapear_tipo_recebivel("Duplicata Mercantil") == ("01", True)
    assert liq.mapear_tipo_recebivel("Cheque pré") == ("51", True)
    assert liq.mapear_tipo_recebivel("xyz") == ("01", False)


def test_filtros():
    est = liq.normalizar_estoque(_estoque())
    assert len(liq.filtrar_vencimento(est, "data", date(2026, 10, 10))) == 2
    assert len(liq.filtrar_vencimento(est, "vencidos", date(2026, 10, 10))) == 3


def test_tabela_e_cnab():
    est = liq.normalizar_estoque(_estoque())
    tab, nao = liq.montar_tabela_liquidacao(est, date(2026, 10, 10))
    assert nao == {"Xpto"}
    assert (tab["VALOR_PAGO"] == tab["VALOR_NOMINAL"]).all()
    assert (tab["IDENTIFICACAO_OCORRENCIA"].map(liq.codigo_do_rotulo) == "75").all()
    tab.loc[0, "INCLUIR"] = False
    df = liq.preparar_para_cnab(tab)
    assert len(df) == 2
    linhas = CNAB444Converter(CONFIG).converter(df)
    assert len(linhas) == 4 and all(len(l) == 444 for l in linhas)
    assert linhas[1][108:110] == "75"
