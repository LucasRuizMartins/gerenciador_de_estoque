
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class MetricasGlobais:
    """Armazena métricas agregadas globais do estoque."""
    nome_fundo: str = "Fundo não identificado"
    valor_nominal: float = 0.0
    valor_nominal_a_vencer: float = 0.0
    valor_nominal_vencido: float = 0.0
    
    valor_vencido:float = 0.0 
    valor_a_vencer:float = 0.0
    valor_pdd:float = 0.0
   
    valor_presente: float = 0.0

    valor_aquisicao: float = 0.0
    valor_aquisicao_a_vencer: float = 0.0
    valor_aquisicao_vencido: float = 0.0
    
    cont_transacoes: int = 0
    total_sacados: int = 0 
    total_cedentes: int = 0 
    qtd_aquisicao: int = 0
    qtd_a_vencer: int = 0
    qtd_vencido: int = 0
      
    ticket_medio_aquisicao_a_vencer: float = 0.0
    ticket_medio_aquisicao_vencido: float = 0.0
    ticket_medio_aquisicao_total: float = 0.0

    ticket_medio_presente_a_vencer: float = 0.0
    ticket_medio_presente_vencido: float = 0.0
    ticket_medio_presente_total: float = 0.0

    ticket_medio_nominal_a_vencer: float = 0.0
    ticket_medio_nominal_vencido: float = 0.0
    ticket_medio_nominal_total: float = 0.0

    ultima_quinzena_valor_aquisicao: float = 0.0
    ultima_quinzena_valor_aquisicao_a_vencer: float = 0.0
    ultima_quinzena_valor_aquisicao_vencido: float = 0.0
    
    ultima_quinzena_valor_nominal: float = 0.0
    ultima_quinzena_valor_nominal_a_vencer: float = 0.0
    ultima_quinzena_valor_nominal_vencido: float = 0.0
    
    ultima_quinzena_valor_presente: float = 0.0    
    ultima_quinzena_valor_vencido:float = 0.0 
    ultima_quinzena_valor_a_vencer:float = 0.0
    
    ultima_quinzena_qtd_aquisicao: int = 0
    ultima_quinzena_qtd_a_vencer: int = 0
    ultima_quinzena_qtd_vencido: int = 0

    ultima_quinzena_ticket_medio_aquisicao_a_vencer: float = 0.0
    ultima_quinzena_ticket_medio_aquisicao_vencido: float = 0.0
    ultima_quinzena_ticket_medio_aquisicao_total: float = 0.0

    ultima_quinzena_ticket_medio_presente_a_vencer: float = 0.0
    ultima_quinzena_ticket_medio_presente_vencido: float = 0.0
    ultima_quinzena_ticket_medio_presente_total: float = 0.0

    ultima_quinzena_ticket_medio_nominal_a_vencer: float = 0.0
    ultima_quinzena_ticket_medio_nominal_vencido: float = 0.0
    ultima_quinzena_ticket_medio_nominal_total: float = 0.0

    taxa_media_total :float =0.0
    mediana_taxa_media: float =0.0 
    mediana_valor_aquisicao:float = 0.0
    mediana_valor_aquisicao_vencido : float = 0.0 
    mediana_valor_aquisicao_a_vencer : float = 0.0 

    
    mediana_total: float = 0.0 
    mediana_a_vencer: float = 0.0 
    mediana_vencido: float = 0.0 

    
    prazo_medio_total :float =0.0
    prazo_medio_total_a_vencer :float =0.0
    prazo_medio_total_vencido :float =0.0
    
    prazo_medio:float =0.0
    prazo_medio_a_vencer :float =0.0
    prazo_medio_vencido :float =0.0

    ultima_quinzena_prazo_medio_total :float =0.0
    ultima_quinzena_prazo_medio_total_a_vencer :float =0.0
    ultima_quinzena_prazo_medio_total_vencido :float =0.0

    ultima_quinzena_prazo_medio:float =0.0
    ultima_quinzena_prazo_medio_a_vencer :float =0.0
    ultima_quinzena_prazo_medio_vencido :float =0.0

    mediana_taxa_cessao:float = 0.0
    taxa_de_cessao:float = 0.0
        
@dataclass
class MetricasMensais:
    """Armazena métricas relacionadas ao período mensal."""
    data_ref: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.now().replace(day=1))
    valor_aquisicao_mes: float = 0.0
    qtd_aquisicao_mes: int = 0
    ticket_medio_mensal: float = 0.0
    prazo_medio_mensal: float = 0.0
    taxa_media_mes: float = 0.0
    # Acumuladores para cálculos ponderados
    _soma_prazo_ponderado: float = 0.0
    _soma_taxa_ponderada: float = 0.0
    _soma_peso_prazo: float = 0.0
    _soma_peso_taxa: float = 0.0

@dataclass
class MetricasVencimento:
    """Armazena métricas de períodos de vencimento."""
    
    a_vencer_0_15: float = 0.0
    a_vencer_16_30: float = 0.0
    a_vencer_31_60: float = 0.0
    a_vencer_61_90: float = 0.0
    a_vencer_91_120: float = 0.0
    a_vencer_121_150: float = 0.0
    a_vencer_151_180: float = 0.0
    a_vencer_181_360: float = 0.0
    a_vencer_acima_360: float = 0.0
    
    vencido_0_15: float = 0.0
    vencido_16_30: float = 0.0
    vencido_31_60: float = 0.0
    vencido_61_90: float = 0.0
    vencido_91_120: float = 0.0
    vencido_121_150: float = 0.0
    vencido_151_180: float = 0.0
    vencido_181_360: float = 0.0
    vencido_acima_360: float = 0.0
    
    pdd_a_vencer_0_15: float = 0.0
    pdd_a_vencer_16_30: float = 0.0
    pdd_a_vencer_31_60: float = 0.0
    pdd_a_vencer_61_90: float = 0.0
    pdd_a_vencer_91_120: float = 0.0
    pdd_a_vencer_121_150: float = 0.0
    pdd_a_vencer_151_180: float = 0.0
    pdd_a_vencer_181_360: float = 0.0
    pdd_a_vencer_acima_360: float = 0.0

    pdd_vencido_0_15: float = 0.0
    pdd_vencido_16_30: float = 0.0
    pdd_vencido_31_60: float = 0.0
    pdd_vencido_61_90: float = 0.0
    pdd_vencido_91_120: float = 0.0
    pdd_vencido_121_150: float = 0.0
    pdd_vencido_151_180: float = 0.0
    pdd_vencido_181_360: float = 0.0
    pdd_vencido_acima_360: float = 0.0
