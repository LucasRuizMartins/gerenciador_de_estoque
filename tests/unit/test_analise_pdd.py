import pytest
import pandas as pd
from src.classes.analise_pdd import categorizar_prazo, percentual_pdd, processar_pdd

"""
BEM-VINDO AOS SEUS PRIMEIROS TESTES!

Um teste automatizado geralmente segue o padrão AAA:
1. Arrange (Organizar): Prepara os dados de entrada.
2. Act (Agir): Chama a função que você quer testar.
3. Assert (Garantir): Verifica se o resultado é o esperado.

O Pytest identifica arquivos que começam com 'test_' e funções que começam com 'test_'.
"""

def test_categorizar_prazo_vencido(config_pdd_mock):
    # Arrange
    prazo = -15
    
    # Act
    resultado = categorizar_prazo(prazo, config_pdd_mock)
    
    # Assert
    assert resultado == "10~20"

def test_categorizar_prazo_a_vencer(config_pdd_mock):
    # Arrange
    prazo = 5 # positivo é a vencer
    
    # Act
    resultado = categorizar_prazo(prazo, config_pdd_mock)
    
    # Assert
    assert resultado == "A vencer"

def test_categorizar_prazo_muito_atrasado(config_pdd_mock):
    # Arrange
    prazo = -100
    
    # Act
    resultado = categorizar_prazo(prazo, config_pdd_mock)
    
    # Assert
    assert resultado == "+20"

def test_percentual_pdd_correto(config_pdd_mock):
    # Arrange & Act
    pct = percentual_pdd("10~20", config_pdd_mock)
    
    # Assert
    assert pct == 0.10

def test_processar_pdd_fluxo_completo(sample_pdd_data, config_pdd_mock):
    """
    Este teste valida se a função processar_pdd consegue agregar os dados corretamente.
    Note que usamos 'sample_pdd_data' e 'config_pdd_mock' que vêm do arquivo conftest.py.
    """
    # Act
    df_resultado = processar_pdd(sample_pdd_data, usar_vagao=False, faixas=config_pdd_mock)
    
    # Assert
    # 1. Verifica se a linha de 'Total' foi criada
    assert "Total" in df_resultado["FAIXA_PDD"].values
    
    # 2. Verifica se o valor total está correto (1000 + 2000 + 5000 = 8000)
    total_vp = df_resultado[df_resultado["FAIXA_PDD"] == "Total"]["VALOR_PRESENTE"].iloc[0]
    assert total_vp == 8000.0
    
    # 3. Verifica se a faixa "10~20" capturou o item de -15 dias (VALOR_PRESENTE = 1000)
    # No nosso mock, -15 está na faixa 10~20
    # No processar_pdd, ele agrupa por faixa
    faixa_10_20 = df_resultado[df_resultado["FAIXA_PDD"] == "10~20"]
    assert not faixa_10_20.empty
    assert faixa_10_20["VALOR_PRESENTE"].iloc[0] == 1000.0
