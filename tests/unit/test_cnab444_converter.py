import pytest
import pandas as pd
from src.classes.cnab444_converter import CNABFormatter, CNAB444Converter

@pytest.fixture
def cnab_config():
    return {
        "codigo_originador": "1",
        "nome_originador": "TESTE",
        "numero_banco": "173",
        "nome_banco": "BRLTRUST",
        "identificacao_sistema": "MX",
        "nr_sequencial_arquivo": 1,
        "codigo_banco_dep": "173",
        "agencia_deposito": "0001",
        "conta_corrente": "12345",
        "coobrigacao": "01",
        "identificacao_ocorrencia": "01",
    }

def test_formatter_num():
    assert CNABFormatter.num(100, 5) == "00100"
    assert CNABFormatter.num(10.5, 5, decimais=2) == "01050"
    assert CNABFormatter.num(None, 3) == "000"

def test_formatter_alfa():
    assert CNABFormatter.alfa("Teste", 10) == "TESTE     "
    assert CNABFormatter.alfa("Ação", 5) == "ACAO "
    assert CNABFormatter.alfa(None, 5) == "     "

def test_formatter_data():
    assert CNABFormatter.data("2024-05-05") == "050524"
    assert CNABFormatter.data("2024-05-05 00:00:00") == "050524"
    assert CNABFormatter.data("05/05/2024") == "050524"
    assert CNABFormatter.data(None) == "000000"

def test_cnab_header_length(cnab_config):
    converter = CNAB444Converter(cnab_config)
    header = converter.montar_header(1)
    assert len(header) == 444
    assert header.startswith("01REMESSA")

def test_cnab_trailer_length(cnab_config):
    converter = CNAB444Converter(cnab_config)
    trailer = converter.montar_trailer(10)
    assert len(trailer) == 444
    assert trailer.startswith("9")
    assert trailer.endswith("000010")

def test_cnab_detalhe_length(cnab_config):
    converter = CNAB444Converter(cnab_config)
    row = {
        "NOME_SACADO": "SACADO TESTE",
        "DOC_SACADO": "12345678901",
        "VALOR_NOMINAL": 1500.50,
        "DATA_VENCIMENTO_AJUSTADA": "2024-06-01"
    }
    detalhe = converter.montar_detalhe(row, 2)
    assert len(detalhe) == 444
    assert detalhe.startswith("1")
