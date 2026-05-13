import logging
import pandas as pd
import numpy as np
from zipfile import ZipFile
import humanize
import statistics
from typing import Dict, Optional, Iterator
from dataclasses import dataclass, field
import tempfile
import os
import io
# pyrefly: ignore [missing-import]
from src.classes.chunk_reader import ChunkReader
# pyrefly: ignore [missing-import]
from src.classes.metricas_aggregator import MetricasAggregator
# pyrefly: ignore [missing-import]
from src.classes.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)


class AnaliseEstoque:
    """
    Classe otimizada para análise de estoque de recebíveis com grandes volumes.
    Processa dados em chunks para minimizar uso de memória.
    """
    
    # Constantes de configuração

    def __init__(self, arquivo):
        try:
            if hasattr(arquivo, "read"):
                arquivo.seek(0)
                sufixo = os.path.splitext(arquivo.name)[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
                    tmp.write(arquivo.read())
                    caminho = tmp.name
            else:
                caminho = arquivo

            logger.info("Iniciando processamento de %s...", caminho)
            
            reader = ChunkReader(caminho)
            self.aggregator = MetricasAggregator()
            
            self.data_ref = reader.data_ref
            self.aggregator.data_ref = self.data_ref
            self.aggregator.metricas_mensais.data_ref = self.data_ref
            
            logger.info("Data de referência identificada: %s", self.data_ref.strftime('%Y-%m-%d'))

            for chunk in reader.iter_chunks():
                self.aggregator._processar_chunk(chunk)
                del chunk

            self.aggregator._finalizar_calculos()
            
            # Retrocompatibilidade de atributos públicos
            self.metricas_globais = self.aggregator.metricas_globais
            self.metricas_mensais = self.aggregator.metricas_mensais
            self.metricas_vencimento = self.aggregator.metricas_vencimento
            self.metricas_globais_por_tipo = self.aggregator.metricas_globais_por_tipo
            self.metricas_mensais_por_tipo = self.aggregator.metricas_mensais_por_tipo
            self.metricas_vencimento_por_tipo = self.aggregator.metricas_vencimento_por_tipo
            self.cedentes_acum = self.aggregator.cedentes_acum
            self.recebiveis_acum = self.aggregator.recebiveis_acum
            self.sacados_acum = self.aggregator.sacados_acum
            
            logger.info("Processamento concluído com sucesso!")

        except Exception as e:
            logger.error("Erro ao processar arquivo: %s", e)
            raise

    # ==================== MÉTODOS PÚBLICOS ====================
    
    def obter_cedentes_agrupados(self) -> pd.DataFrame:
        """Retorna DataFrame com cedentes agrupados."""
        if not self.cedentes_acum:
            return pd.DataFrame(columns=['DOC_CEDENTE', 'NOME_CEDENTE', 'VALOR_PRESENTE', '%'])
        
        dados = [
            {'DOC_CEDENTE': doc, 'NOME_CEDENTE': nome, 'VALOR_PRESENTE': valor}
            for (doc, nome), valor in self.cedentes_acum.items()
        ]
        
        df = pd.DataFrame(dados)
        total = df['VALOR_PRESENTE'].sum()
        df['%'] = (df['VALOR_PRESENTE'] / total * 100).fillna(0).round(2) if total > 0 else 0
        
        return df.sort_values('VALOR_PRESENTE', ascending=False)
    
    def obter_recebiveis_agrupados(self) -> pd.DataFrame:
        """Retorna DataFrame com recebíveis agrupados."""
        if not self.recebiveis_acum:
            return pd.DataFrame(columns=['TIPO_RECEBIVEL', 'VALOR_PRESENTE', 'VALOR_NOMINAL', 'VALOR_AQUISICAO'])
        
        dados = [
            {
                'TIPO_RECEBIVEL': tipo,
                'VALOR_PRESENTE': valores['VALOR_PRESENTE'],
                'VALOR_NOMINAL': valores['VALOR_NOMINAL'],
                'VALOR_AQUISICAO': valores['VALOR_AQUISICAO']
            }
            for tipo, valores in self.recebiveis_acum.items()
        ]
        
        return pd.DataFrame(dados).sort_values('VALOR_PRESENTE', ascending=False)
    
    # ==================== EXPORTAÇÃO ====================
    
    def exportar_para_excel(self, output) -> bool:
        """Exporta métricas para Excel (arquivo ou buffer)."""
        exporter = ExcelExporter(self)
        return exporter.exportar(output)
    


    
