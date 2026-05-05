import pytest
import pandas as pd
from io import BytesIO
from src.data_loader import ler_csv

"""
TESTANDO COM MOCKS (SIMULAÇÕES)

Às vezes não queremos criar um arquivo real no disco para testar uma função.
Podemos usar o 'BytesIO' para simular um arquivo na memória.
"""

def test_ler_csv_valido():
    # Arrange: Criamos um CSV em memória
    csv_content = "DOC_SACADO;VALOR_PRESENTE\n123;100,50\n456;200,00"
    file_mock = BytesIO(csv_content.encode("ISO-8859-1"))
    
    # Act
    df = ler_csv(file_mock)
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df["DOC_SACADO"].iloc[0] == 123
    # Verifica se o decimal foi tratado corretamente (100,50 -> 100.5)
    assert df["VALOR_PRESENTE"].iloc[0] == 100.5

def test_ler_csv_vazio():
    # Arrange
    csv_content = "DOC_SACADO;VALOR_PRESENTE"
    file_mock = BytesIO(csv_content.encode("ISO-8859-1"))
    
    # Act
    df = ler_csv(file_mock)
    
    # Assert
    assert len(df) == 0
