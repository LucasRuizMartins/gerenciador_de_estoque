import pytest
from src.funcoes import limpar_cpf_cnpj

def test_limpar_cpf_cnpj():
    # Arrange
    entrada = "123.456.789-00"
    
    # Act
    resultado = limpar_cpf_cnpj(entrada)
    
    # Assert
    assert resultado == "12345678900"

def test_limpar_cpf_cnpj_com_espacos():
    # Arrange
    entrada = " 12.345.678/0001-99 "
    
    # Act
    resultado = limpar_cpf_cnpj(entrada)
    
    # Assert
    assert resultado == "12345678000199"
