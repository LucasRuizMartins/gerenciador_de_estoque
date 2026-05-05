import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_pdd_data():
    """
    Fixture que fornece um DataFrame de exemplo para testes de PDD.
    As fixtures são funções que o pytest injeta nos seus testes automaticamente.
    """
    data = {
        "DOC_SACADO": ["123", "123", "456"],
        "SEU_NUMERO": ["A1", "A2", "B1"],
        "SITUACAO_RECEBIVEL": ["Vencido", "Vencido", "A vencer"],
        "PRAZO_ATUAL": [-15, -50, 10],
        "VALOR_PRESENTE": [1000.0, 2000.0, 5000.0],
        "VALOR_AQUISICAO": [900.0, 1800.0, 4500.0],
        "VALOR_NOMINAL": [1100.0, 2100.0, 5100.0],
        "VALOR_PDD": [0.0, 0.0, 0.0],
        "DATA_REFERENCIA": ["2024-01-01", "2024-01-01", "2024-01-01"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def config_pdd_mock():
    """Fixture com uma configuração de PDD simplificada para testes."""
    return [
        ("0~9", 0, -9, 0.05),
        ("10~20", -10, -20, 0.10),
        ("+20", None, -21, 1.0)
    ]
