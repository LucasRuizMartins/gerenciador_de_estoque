import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from src.classes.analise_estoque import AnaliseEstoque

@pytest.fixture
def sample_estoque_csv():
    """Cria um CSV temporário com dados de estoque para teste."""
    # Data de referência fixa para o teste ser determinístico
    hoje = pd.Timestamp.now().normalize()
    
    dados = {
        'TIPO_RECEBIVEL': ['Duplicata', 'Cheque', 'Duplicata', 'Cartão'],
        'VALOR_NOMINAL': [1000.0, 500.0, 2000.0, 300.0],
        'VALOR_PRESENTE': [950.0, 480.0, 1900.0, 290.0],
        'VALOR_AQUISICAO': [900.0, 450.0, 1800.0, 280.0],
        'VALOR_PDD': [50.0, 20.0, 100.0, 10.0],
        'DATA_REFERENCIA': [hoje, hoje, hoje, hoje],
        'DATA_AQUISICAO': [hoje - pd.Timedelta(days=5), hoje, hoje, hoje],
        'DATA_VENCIMENTO_ORIGINAL': [
            hoje + pd.Timedelta(days=10),  # A vencer 0-15
            hoje + pd.Timedelta(days=45),  # A vencer 31-60
            hoje - pd.Timedelta(days=20),  # Vencido 16-30
            hoje + pd.Timedelta(days=100)  # A vencer 91-120
        ],
        'PRAZO_ATUAL': [10, 45, -20, 100],
        'PRAZO': [15, 45, 10, 100],
        'SITUACAO_RECEBIVEL': ['A vencer', 'A vencer', 'Vencido', 'A vencer'],
        'TAXA_CESSAO': [0.02, 0.03, 0.02, 0.01],
        'DOC_CEDENTE': ['123', '456', '123', '789'],
        'NOME_CEDENTE': ['Cedente A', 'Cedente B', 'Cedente A', 'Cedente C'],
        'NOME_FUNDO': ['Fundo Alpha', 'Fundo Alpha', 'Fundo Alpha', 'Fundo Alpha'],
        'DOC_SACADO': ['S1', 'S2', 'S1', 'S3'],
        'NOME_SACADO': ['Sacado 1', 'Sacado 2', 'Sacado 1', 'Sacado 3']
    }
    
    df = pd.DataFrame(dados)
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='ISO-8859-1') as tmp:
        df.to_csv(tmp.name, index=False, sep=';', decimal=',', encoding='ISO-8859-1')
        path = tmp.name
        
    yield path
    
    if os.path.exists(path):
        os.remove(path)

def test_analise_estoque_metricas_globais(sample_estoque_csv):
    """Testa se as métricas globais são calculadas corretamente."""
    analise = AnaliseEstoque(sample_estoque_csv)
    mg = analise.metricas_globais
    
    # Valores totais
    assert mg.valor_nominal == 3800.0  # 1000+500+2000+300
    assert mg.valor_presente == 3620.0 # 950+480+1900+290
    assert mg.valor_pdd == 180.0       # 50+20+100+10
    
    # Contagens
    assert mg.cont_transacoes == 4
    assert mg.total_cedentes == 3 # A, B, C
    assert mg.total_sacados == 3  # 1, 2, 3

def test_analise_estoque_vencimentos(sample_estoque_csv):
    """Testa a classificação em faixas de vencimento."""
    analise = AnaliseEstoque(sample_estoque_csv)
    mv = analise.metricas_vencimento
    
    # A vencer
    assert mv.a_vencer_0_15 == 950.0   # Row 1
    assert mv.a_vencer_31_60 == 480.0  # Row 2
    assert mv.a_vencer_91_120 == 290.0 # Row 4
    
    # Vencido
    assert mv.vencido_16_30 == 1900.0  # Row 3
    
    # PDD
    assert mv.pdd_a_vencer_0_15 == 50.0
    assert mv.pdd_vencido_16_30 == 100.0

def test_analise_estoque_agrupamentos(sample_estoque_csv):
    """Testa os métodos de agrupamento para Cedentes e Recebíveis."""
    analise = AnaliseEstoque(sample_estoque_csv)
    
    # Cedentes
    df_ced = analise.obter_cedentes_agrupados()
    # Cedente A tem 2 linhas (950 + 1900 presente)
    cedente_a = df_ced[df_ced['NOME_CEDENTE'] == 'Cedente A'].iloc[0]
    assert cedente_a['VALOR_PRESENTE'] == 2850.0
    
    # Tipos de Recebível (Agrupados: Duplicata, Cheque, Cartão)
    df_rec = analise.obter_recebiveis_agrupados()
    assert len(df_rec) == 3 

    duplicata = df_rec[df_rec['TIPO_RECEBIVEL'] == 'Duplicata'].iloc[0]
    assert duplicata['VALOR_NOMINAL'] == 3000.0 # 1000 + 2000

def test_analise_estoque_filtro_fundo(sample_estoque_csv):
    """Verifica se o nome do fundo é capturado."""
    analise = AnaliseEstoque(sample_estoque_csv)
    assert analise.metricas_globais.nome_fundo == 'Fundo Alpha'

def test_analise_estoque_medianas(sample_estoque_csv):
    """Verifica se o cálculo das medianas segue a lógica (taxa / aquisição)."""
    analise = AnaliseEstoque(sample_estoque_csv)
    mg = analise.metricas_globais
    
    # Na lógica global (_mediana_ratio), o cálculo é t / v
    # Vamos verificar um dos tipos para simplificar
    duplicata_mg = analise.metricas_globais_por_tipo['Duplicata']
    
    # Para Duplicata no sample:
    # Row 1: Aquisição 900, Yield calculado ~482.0
    # Row 3: Aquisição 1800, Yield calculado ~1700.0
    # A mediana deve seguir mg.mediana_taxa_cessao / statistics.median([900, 1800])
    
    mediana_aq = (900 + 1800) / 2
    esperado = duplicata_mg.mediana_taxa_cessao / mediana_aq
    
    assert duplicata_mg.mediana_valor_aquisicao == pytest.approx(esperado, rel=1e-4)

