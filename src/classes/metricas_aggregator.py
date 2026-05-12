import pandas as pd
import numpy as np
import statistics
from typing import Dict, Optional
import logging
from src.metricas import MetricasGlobais, MetricasMensais, MetricasVencimento

logger = logging.getLogger(__name__)

class MetricasAggregator:
    FAIXAS_A_VENCER = [
        ('a_vencer_0_15', 0, 15),
        ('a_vencer_16_30', 16, 30),
        ('a_vencer_31_60', 31, 60),
        ('a_vencer_61_90', 61, 90),
        ('a_vencer_91_120', 91, 120),
        ('a_vencer_121_150', 121, 150),
        ('a_vencer_151_180', 151, 180),
        ('a_vencer_181_360', 181, 360),
        ('a_vencer_acima_360', 361, None),
    ]

    FAIXAS_VENCIDO = [
        ('vencido_0_15', -15, -1),
        ('vencido_16_30', -30, -16),
        ('vencido_31_60', -60, -31),
        ('vencido_61_90', -90, -61),
        ('vencido_91_120', -120, -91),
        ('vencido_121_150', -150, -121),
        ('vencido_151_180', -180, -151),
        ('vencido_181_360', -360, -181),
        ('vencido_acima_360', None, -361),
    ]

    def __init__(self):
        self._inicializar_metricas()
        self._inicializar_acumuladores()

    def _inicializar_metricas(self) -> None:
        """Inicializa todas as estruturas de métricas."""
        self.metricas_globais = MetricasGlobais()
        self.metricas_mensais = MetricasMensais()
        self.metricas_vencimento = MetricasVencimento()
        
        self.metricas_globais_por_tipo: Dict[str, MetricasGlobais] = {}
        self.metricas_mensais_por_tipo: Dict[str, MetricasMensais] = {}
        self.metricas_vencimento_por_tipo: Dict[str, MetricasVencimento] = {}
        self.sacados_por_tipo = {}
        self.cedentes_por_tipo = {}

        self._todas_taxas_media_por_tipo = {}
        self._todos_valores_aquisicao_por_tipo = {}
        self._todos_valores_aquisicao_vencido_por_tipo = {}
        self._todos_valores_aquisicao_a_vencer_por_tipo = {}

        self._todas_taxas_cessao_geral = []
        self._todas_taxas_cessao_por_tipo = {}
        
        
    def _inicializar_acumuladores(self) -> None:
        """Inicializa acumuladores para agregações."""
        
        self.cedentes_acum = {}
        self.recebiveis_acum = {}
        self.sacados_acum = set()
        self._todos_valores_aquisicao = []
        self._todos_valores_aquisicao_vencido = []
        self._todos_valores_aquisicao_a_vencer = []
        self._todas_taxas_media = []
    

    
    # ==================== PROCESSAMENTO DE CHUNK ====================
    
    def _processar_chunk(self, chunk: pd.DataFrame) -> None:
        """Processa um chunk e atualiza métricas acumuladas."""
        if chunk.empty:
            return
        
        self._atualizar_metricas_globais(chunk)
        self._atualizar_metricas_mensais(chunk)
        self._atualizar_metricas_vencimento(chunk)
        
        if 'TIPO_RECEBIVEL' in chunk.columns:
            for tipo in chunk['TIPO_RECEBIVEL'].cat.categories:
                df_tipo = chunk[chunk['TIPO_RECEBIVEL'] == tipo]
                if not df_tipo.empty:
                    self._atualizar_metricas_por_tipo(df_tipo, tipo)
        
        self._acumular_cedentes(chunk)
        self._acumular_recebiveis(chunk)
        self._acumular_sacados(chunk)
        self._acumular_taxa_media_completa(chunk)
        self._acumular_taxa_cessao_completa(chunk)
        
    def _atualizar_metricas_globais(self, chunk: pd.DataFrame) -> None:
        """Atualiza métricas globais com dados do chunk."""
        m = self.metricas_globais
        vencido = chunk['SITUACAO_RECEBIVEL'] == 'Vencido'
        a_vencer = chunk['SITUACAO_RECEBIVEL'] == 'A vencer'
        
        # Valores nominais
        m.valor_nominal += chunk['VALOR_NOMINAL'].sum()
        m.valor_nominal_vencido += chunk.loc[vencido, 'VALOR_NOMINAL'].sum()
        m.valor_nominal_a_vencer += chunk.loc[a_vencer, 'VALOR_NOMINAL'].sum()
        
        # Valores presentes
        m.valor_presente += chunk['VALOR_PRESENTE'].sum()
        m.valor_vencido += chunk.loc[vencido, 'VALOR_PRESENTE'].sum()
        m.valor_a_vencer += chunk.loc[a_vencer, 'VALOR_PRESENTE'].sum()
        
        # Valores de aquisição
        m.valor_aquisicao += chunk['VALOR_AQUISICAO'].sum()
        m.valor_aquisicao_vencido += chunk.loc[vencido, 'VALOR_AQUISICAO'].sum()
        m.valor_aquisicao_a_vencer += chunk.loc[a_vencer, 'VALOR_AQUISICAO'].sum()
        
        # Quantidades
        m.cont_transacoes += len(chunk)
        m.qtd_aquisicao += len(chunk)
        m.qtd_vencido += vencido.sum()
        m.qtd_a_vencer += a_vencer.sum()
        
        # PDD e outros
        m.valor_pdd += chunk['VALOR_PDD'].sum()
        m.taxa_media_total += chunk['TAXA_MEDIA'].sum()
        m.prazo_medio_total += chunk['PRAZO_MEDIO'].sum()
        m.prazo_medio_total_a_vencer += chunk.loc[a_vencer, 'PRAZO_MEDIO'].sum()
        m.prazo_medio_total_vencido += chunk.loc[vencido, 'PRAZO_MEDIO'].sum()
        
        self._atualizar_ultima_quinzena(chunk)
        self._atualizar_nome_fundo(chunk)
    
    def _atualizar_ultima_quinzena(self, chunk: pd.DataFrame) -> None:
        """Atualiza métricas da última quinzena."""
        data_corte = self.data_ref - pd.Timedelta(days=15)
        chunk_filtrado = chunk[chunk['DATA_AQUISICAO'] >= data_corte]
        
        if chunk_filtrado.empty:
            return
        
        m = self.metricas_globais
        vencido = chunk_filtrado['SITUACAO_RECEBIVEL'] == 'Vencido'
        a_vencer = chunk_filtrado['SITUACAO_RECEBIVEL'] == 'A vencer'
        
        # Valores presentes
        m.ultima_quinzena_valor_presente += chunk_filtrado['VALOR_PRESENTE'].sum()
        m.ultima_quinzena_valor_vencido += chunk_filtrado.loc[vencido, 'VALOR_PRESENTE'].sum()
        m.ultima_quinzena_valor_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_PRESENTE'].sum()
        
        # Valores de aquisição
        m.ultima_quinzena_valor_aquisicao += chunk_filtrado['VALOR_AQUISICAO'].sum()
        m.ultima_quinzena_valor_aquisicao_vencido += chunk_filtrado.loc[vencido, 'VALOR_AQUISICAO'].sum()
        m.ultima_quinzena_valor_aquisicao_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_AQUISICAO'].sum()
        
        # Valores nominais
        m.ultima_quinzena_valor_nominal += chunk_filtrado['VALOR_NOMINAL'].sum()
        m.ultima_quinzena_valor_nominal_vencido += chunk_filtrado.loc[vencido, 'VALOR_NOMINAL'].sum()
        m.ultima_quinzena_valor_nominal_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_NOMINAL'].sum()
        
        # Quantidades
        m.ultima_quinzena_qtd_vencido += vencido.sum()
        m.ultima_quinzena_qtd_a_vencer += a_vencer.sum()
        m.ultima_quinzena_qtd_aquisicao += len(chunk_filtrado)        
        # Prazos
        m.ultima_quinzena_prazo_medio_total += chunk_filtrado['PRAZO_MEDIO'].sum()
        m.ultima_quinzena_prazo_medio_total_a_vencer += chunk_filtrado.loc[a_vencer, 'PRAZO_MEDIO'].sum()
        m.ultima_quinzena_prazo_medio_total_vencido += chunk_filtrado.loc[vencido, 'PRAZO_MEDIO'].sum()
    
    def _atualizar_nome_fundo(self, chunk: pd.DataFrame) -> None:
        """Atualiza o nome do fundo se ainda não foi identificado."""
        if self.metricas_globais.nome_fundo == "Fundo não identificado" and 'NOME_FUNDO' in chunk.columns:
            primeiro_nome = chunk['NOME_FUNDO'].iloc[0] if len(chunk) > 0 else None
            if pd.notna(primeiro_nome):
                self.metricas_globais.nome_fundo = str(primeiro_nome)
    
    def _atualizar_metricas_mensais(self, chunk: pd.DataFrame) -> None:
        """Atualiza métricas mensais com dados do chunk."""
        if 'DATA_AQUISICAO' not in chunk.columns:
            return
        
        data_inicio = self.data_ref.replace(day=1)
        data_fim = data_inicio + pd.DateOffset(months=1)
        
        df_mes = chunk[
            (chunk['DATA_AQUISICAO'] >= data_inicio) &
            (chunk['DATA_AQUISICAO'] < data_fim)
        ]
        
        self.metricas_mensais.valor_aquisicao_mes += df_mes['VALOR_AQUISICAO'].sum()
        self.metricas_mensais.qtd_aquisicao_mes += len(df_mes)
    
    def _atualizar_metricas_vencimento(self, chunk: pd.DataFrame) -> None:
        """Atualiza métricas de vencimento com dados do chunk."""
        if not all(col in chunk.columns for col in ['PRAZO_ATUAL', 'SITUACAO_RECEBIVEL', 'VALOR_PRESENTE']):
            return
        
        mv = self.metricas_vencimento
        
        # Faixas A vencer (Valor Presente)
        for attr, prazo_min, prazo_max in self.FAIXAS_A_VENCER:
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'A vencer', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
        
        # Faixas Vencido (Valor Presente)
        for attr, prazo_min, prazo_max in self.FAIXAS_VENCIDO:
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'Vencido', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
        
        # PDD A vencer
        for attr, prazo_min, prazo_max in self.FAIXAS_A_VENCER:
            attr_pdd = f'pdd_{attr}'
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'A vencer', 'VALOR_PDD')
            setattr(mv, attr_pdd, getattr(mv, attr_pdd) + valor)
        
        # PDD Vencido
        for attr, prazo_min, prazo_max in self.FAIXAS_VENCIDO:
            attr_pdd = f'pdd_{attr}'
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'Vencido', 'VALOR_PDD')
            setattr(mv, attr_pdd, getattr(mv, attr_pdd) + valor)
    
    def _somar_vencimento(
        self,
        chunk: pd.DataFrame,
        prazo_min: Optional[int],
        prazo_max: Optional[int],
        situacao: str,
        coluna: str,
    ) -> float:
        """Soma valores por faixa de prazo e situação."""
        filtro = chunk['SITUACAO_RECEBIVEL'] == situacao
        
        if prazo_min is not None:
            filtro &= chunk['PRAZO_ATUAL'] >= prazo_min
        if prazo_max is not None:
            filtro &= chunk['PRAZO_ATUAL'] <= prazo_max
        
        return float(chunk.loc[filtro, coluna].sum())
    
    def _atualizar_metricas_por_tipo(self, chunk_tipo: pd.DataFrame, tipo: str) -> None:
        """Atualiza métricas para um tipo específico de recebível."""
        if tipo not in self.metricas_globais_por_tipo:
            self.metricas_globais_por_tipo[tipo] = MetricasGlobais()
            self.metricas_mensais_por_tipo[tipo] = MetricasMensais()
            self.metricas_vencimento_por_tipo[tipo] = MetricasVencimento()
            self.sacados_por_tipo[tipo] = set()
            self.cedentes_por_tipo[tipo] = set()
        
        mg = self.metricas_globais_por_tipo[tipo]
        vencido = chunk_tipo['SITUACAO_RECEBIVEL'] == 'Vencido'
        a_vencer = chunk_tipo['SITUACAO_RECEBIVEL'] == 'A vencer'
        
        # Valores nominais
        mg.valor_nominal += chunk_tipo['VALOR_NOMINAL'].sum()
        mg.valor_nominal_vencido += chunk_tipo.loc[vencido, 'VALOR_NOMINAL'].sum()
        mg.valor_nominal_a_vencer += chunk_tipo.loc[a_vencer, 'VALOR_NOMINAL'].sum()
        
        # Valores presentes
        mg.valor_pdd += chunk_tipo['VALOR_PDD'].sum()
        mg.valor_vencido += chunk_tipo.loc[vencido, 'VALOR_PRESENTE'].sum()
        mg.valor_a_vencer += chunk_tipo.loc[a_vencer, 'VALOR_PRESENTE'].sum()
        mg.valor_presente += chunk_tipo['VALOR_PRESENTE'].sum()
        
        # Valores de aquisição
        mg.valor_aquisicao_vencido += chunk_tipo.loc[vencido, 'VALOR_AQUISICAO'].sum()
        mg.valor_aquisicao_a_vencer += chunk_tipo.loc[a_vencer, 'VALOR_AQUISICAO'].sum()
        mg.valor_aquisicao += chunk_tipo['VALOR_AQUISICAO'].sum()
        
        # Quantidades
        mg.cont_transacoes += len(chunk_tipo)
        mg.qtd_aquisicao += len(chunk_tipo)
        mg.qtd_vencido += vencido.sum()
        mg.qtd_a_vencer += a_vencer.sum()
        
        # Prazos
        mg.prazo_medio_total += chunk_tipo['PRAZO_MEDIO'].sum()
        mg.prazo_medio_total_a_vencer += chunk_tipo.loc[a_vencer, 'PRAZO_MEDIO'].sum()
        mg.prazo_medio_total_vencido += chunk_tipo.loc[vencido, 'PRAZO_MEDIO'].sum()
        
        self._atualizar_ultima_quinzena_por_tipo(chunk_tipo, tipo)
        self._atualizar_sacados_cedentes_por_tipo(chunk_tipo, tipo)
        self._atualizar_metricas_mensais_por_tipo(chunk_tipo, tipo)
        self._atualizar_metricas_vencimento_por_tipo(chunk_tipo, tipo)
    
    def _atualizar_ultima_quinzena_por_tipo(self, chunk_tipo: pd.DataFrame, tipo: str) -> None:
        """Atualiza métricas da última quinzena para um tipo específico."""
        if 'DATA_AQUISICAO' not in chunk_tipo.columns:
            return
        
        mg = self.metricas_globais_por_tipo[tipo]
        data_corte = self.data_ref - pd.Timedelta(days=15)
        chunk_filtrado = chunk_tipo[chunk_tipo['DATA_AQUISICAO'] >= data_corte]
        
        if chunk_filtrado.empty:
            return
        
        vencido = chunk_filtrado['SITUACAO_RECEBIVEL'] == 'Vencido'
        a_vencer = chunk_filtrado['SITUACAO_RECEBIVEL'] == 'A vencer'
        # Valores presentes
        mg.ultima_quinzena_valor_presente += chunk_filtrado['VALOR_PRESENTE'].sum()
        mg.ultima_quinzena_valor_vencido += chunk_filtrado.loc[vencido, 'VALOR_PRESENTE'].sum()
        mg.ultima_quinzena_valor_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_PRESENTE'].sum()
        # Valores de aquisição
        mg.ultima_quinzena_valor_aquisicao += chunk_filtrado['VALOR_AQUISICAO'].sum()
        mg.ultima_quinzena_valor_aquisicao_vencido += chunk_filtrado.loc[vencido, 'VALOR_AQUISICAO'].sum()
        mg.ultima_quinzena_valor_aquisicao_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_AQUISICAO'].sum()
        # Valores nominais
        mg.ultima_quinzena_valor_nominal += chunk_filtrado['VALOR_NOMINAL'].sum()
        mg.ultima_quinzena_valor_nominal_vencido += chunk_filtrado.loc[vencido, 'VALOR_NOMINAL'].sum()
        mg.ultima_quinzena_valor_nominal_a_vencer += chunk_filtrado.loc[a_vencer, 'VALOR_NOMINAL'].sum()
        # Quantidades
        mg.ultima_quinzena_qtd_vencido += vencido.sum()
        mg.ultima_quinzena_qtd_a_vencer += a_vencer.sum()
        mg.ultima_quinzena_qtd_aquisicao += len(chunk_filtrado)
        # Prazos
        mg.ultima_quinzena_prazo_medio_total += chunk_filtrado['PRAZO_MEDIO'].sum()
        mg.ultima_quinzena_prazo_medio_total_a_vencer += chunk_filtrado.loc[a_vencer, 'PRAZO_MEDIO'].sum()
        mg.ultima_quinzena_prazo_medio_total_vencido += chunk_filtrado.loc[vencido, 'PRAZO_MEDIO'].sum()
    
    def _atualizar_sacados_cedentes_por_tipo(self, chunk_tipo: pd.DataFrame, tipo: str) -> None:
        """Atualiza sacados e cedentes por tipo."""
        if 'DOC_SACADO' in chunk_tipo.columns:
            sacados_chunk = chunk_tipo['DOC_SACADO'].dropna().unique()
            self.sacados_por_tipo[tipo].update(sacados_chunk)
        if 'DOC_CEDENTE' in chunk_tipo.columns:
            cedentes_chunk = chunk_tipo['DOC_CEDENTE'].dropna().unique()
            self.cedentes_por_tipo[tipo].update(cedentes_chunk)
    
    def _atualizar_metricas_mensais_por_tipo(self, chunk_tipo: pd.DataFrame, tipo: str) -> None:
        """Atualiza métricas mensais por tipo."""
        if 'DATA_AQUISICAO' not in chunk_tipo.columns:
            return
        
        data_inicio = self.data_ref.replace(day=1)
        data_fim = data_inicio + pd.DateOffset(months=1)
        
        df_mes_tipo = chunk_tipo[
            (chunk_tipo['DATA_AQUISICAO'] >= data_inicio) &
            (chunk_tipo['DATA_AQUISICAO'] < data_fim)
        ]
        
        mm = self.metricas_mensais_por_tipo[tipo]
        mm.valor_aquisicao_mes += df_mes_tipo['VALOR_AQUISICAO'].sum()
        mm.qtd_aquisicao_mes += len(df_mes_tipo)
    
    def _atualizar_metricas_vencimento_por_tipo(self, chunk_tipo: pd.DataFrame, tipo: str) -> None:
        """Atualiza métricas de vencimento por tipo."""
        if not all(col in chunk_tipo.columns for col in ['PRAZO_ATUAL', 'SITUACAO_RECEBIVEL', 'VALOR_PRESENTE']):
            return
        
        mv = self.metricas_vencimento_por_tipo[tipo]
        
        # Faixas A vencer
        faixas_a_vencer = [
            ('a_vencer_0_15', 0, 15),
            ('a_vencer_16_30', 16, 30),
            ('a_vencer_31_60', 31, 60),
            ('a_vencer_61_90', 61, 90),
            ('a_vencer_91_120', 91, 120),
            ('a_vencer_121_150', 121, 150),
            ('a_vencer_151_180', 151, 180),
            ('a_vencer_181_360', 181, 360),
            ('a_vencer_acima_360', 361, None),
        ]
        
        for attr, prazo_min, prazo_max in faixas_a_vencer:
            # Valor Presente
            valor = self._somar_vencimento(chunk_tipo, prazo_min, prazo_max, 'A vencer', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
            
            # PDD
            attr_pdd = f'pdd_{attr}'
            valor_pdd = self._somar_vencimento(chunk_tipo, prazo_min, prazo_max, 'A vencer', 'VALOR_PDD')
            setattr(mv, attr_pdd, getattr(mv, attr_pdd) + valor_pdd)
        
        # Faixas Vencido
        faixas_vencido = [
            ('vencido_0_15', -15, -1),
            ('vencido_16_30', -30, -16),
            ('vencido_31_60', -60, -31),
            ('vencido_61_90', -90, -61),
            ('vencido_91_120', -120, -91),
            ('vencido_121_150', -150, -121),
            ('vencido_151_180', -180, -151),
            ('vencido_181_360', -360, -181),
            ('vencido_acima_360', None, -361),
        ]
        
        for attr, prazo_min, prazo_max in faixas_vencido:
            # Valor Presente
            valor = self._somar_vencimento(chunk_tipo, prazo_min, prazo_max, 'Vencido', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
            # PDD
            attr_pdd = f'pdd_{attr}'
            valor_pdd = self._somar_vencimento(chunk_tipo, prazo_min, prazo_max, 'Vencido', 'VALOR_PDD')
            setattr(mv, attr_pdd, getattr(mv, attr_pdd) + valor_pdd)
    
    # ==================== ACUMULADORES ====================
    
    def _acumular_cedentes(self, chunk: pd.DataFrame) -> None:
        """Acumula dados de cedentes para posterior agregação."""
        if not all(col in chunk.columns for col in ['DOC_CEDENTE', 'NOME_CEDENTE', 'VALOR_PRESENTE']):
            return
        
        agrupado = chunk.groupby(['DOC_CEDENTE', 'NOME_CEDENTE'], observed=True)['VALOR_PRESENTE'].sum()
        
        for (doc, nome), valor in agrupado.items():
            chave = (doc, nome)
            self.cedentes_acum[chave] = self.cedentes_acum.get(chave, 0) + valor
    
    def _acumular_recebiveis(self, chunk: pd.DataFrame) -> None:
        """Acumula dados de recebíveis para posterior agregação."""
        if not all(col in chunk.columns for col in ['TIPO_RECEBIVEL', 'VALOR_PRESENTE', 'VALOR_NOMINAL', 'VALOR_AQUISICAO']):
            return
        agrupado = chunk.groupby('TIPO_RECEBIVEL', observed=True).agg({
            'VALOR_PRESENTE': 'sum',
            'VALOR_NOMINAL': 'sum',
            'VALOR_AQUISICAO': 'sum'
        })
        for tipo, row in agrupado.iterrows():
            if tipo not in self.recebiveis_acum:
                self.recebiveis_acum[tipo] = {
                    'VALOR_PRESENTE': 0,
                    'VALOR_NOMINAL': 0,
                    'VALOR_AQUISICAO': 0
                }
            self.recebiveis_acum[tipo]['VALOR_PRESENTE'] += row['VALOR_PRESENTE']
            self.recebiveis_acum[tipo]['VALOR_NOMINAL'] += row['VALOR_NOMINAL']
            self.recebiveis_acum[tipo]['VALOR_AQUISICAO'] += row['VALOR_AQUISICAO']
    
    def _acumular_sacados(self, chunk: pd.DataFrame) -> None:
        """Acumula sacados únicos."""
        if 'DOC_SACADO' in chunk.columns:
            sacados_chunk = chunk['DOC_SACADO'].dropna().unique()
            self.sacados_acum.update(sacados_chunk)
     
    def _acumular_taxa_media_completa(self, chunk: pd.DataFrame) -> None:
        """Acumula valores para cálculo de mediana de taxa."""
        if 'TAXA_CESSAO' not in chunk.columns:
            return
    
        chunk_vencido = chunk['SITUACAO_RECEBIVEL'] == 'Vencido'
        chunk_a_vencer = chunk['SITUACAO_RECEBIVEL'] == 'A vencer'
        
        valores_aquisicao = chunk['VALOR_AQUISICAO'].dropna()
        valores_aquisicao_a_vencer = chunk.loc[chunk_a_vencer, 'VALOR_AQUISICAO'].dropna()
        valores_aquisicao_vencido = chunk.loc[chunk_vencido, 'VALOR_AQUISICAO'].dropna()
        
        # CORREÇÃO: Usar TAXA_CESSAO diretamente, não TAXA_MEDIA
        taxas_cessao = chunk['TAXA_CESSAO'].dropna()
        
        if not taxas_cessao.empty:
            self._todos_valores_aquisicao.extend(valores_aquisicao.tolist())
            self._todos_valores_aquisicao_vencido.extend(valores_aquisicao_vencido.tolist())
            self._todos_valores_aquisicao_a_vencer.extend(valores_aquisicao_a_vencer.tolist())
            self._todas_taxas_media.extend(taxas_cessao.tolist())

        if 'TIPO_RECEBIVEL' in chunk.columns:
            for tipo in chunk['TIPO_RECEBIVEL'].cat.categories:
                chunk_tipo = chunk[chunk['TIPO_RECEBIVEL'] == tipo]
                
                # Inicializar acumuladores para o tipo se não existirem
                if tipo not in self._todas_taxas_media_por_tipo:
                    self._todas_taxas_media_por_tipo[tipo] = []
                    self._todas_taxas_cessao_por_tipo[tipo] = []
                    self._todos_valores_aquisicao_por_tipo[tipo] = []
                    self._todos_valores_aquisicao_vencido_por_tipo[tipo] = []
                    self._todos_valores_aquisicao_a_vencer_por_tipo[tipo] = []
                
                chunk_tipo_vencido = chunk_tipo['SITUACAO_RECEBIVEL'] == 'Vencido'
                chunk_tipo_a_vencer = chunk_tipo['SITUACAO_RECEBIVEL'] == 'A vencer'
                
                valores_aquisicao_tipo = chunk_tipo['VALOR_AQUISICAO'].dropna()
                valores_aquisicao_a_vencer_tipo = chunk_tipo.loc[chunk_tipo_a_vencer, 'VALOR_AQUISICAO'].dropna()
                valores_aquisicao_vencido_tipo = chunk_tipo.loc[chunk_tipo_vencido, 'VALOR_AQUISICAO'].dropna()
                
                # CORREÇÃO: Usar TAXA_CESSAO diretamente
                taxas_cessao_tipo = chunk_tipo['TAXA_CESSAO'].dropna()                
                taxas_de_cessao_tipo = chunk_tipo['TAXA_DE_CESSAO'].dropna()
                
                if not taxas_cessao_tipo.empty:
                    self._todos_valores_aquisicao_por_tipo[tipo].extend(valores_aquisicao_tipo.tolist())
                    self._todos_valores_aquisicao_vencido_por_tipo[tipo].extend(valores_aquisicao_vencido_tipo.tolist())
                    self._todos_valores_aquisicao_a_vencer_por_tipo[tipo].extend(valores_aquisicao_a_vencer_tipo.tolist())
                    self._todas_taxas_media_por_tipo[tipo].extend(taxas_cessao_tipo.tolist())
                    
                    self._todas_taxas_cessao_por_tipo[tipo].extend(taxas_de_cessao_tipo.tolist())


    def _acumular_taxa_cessao_completa(self, chunk: pd.DataFrame) -> None:
        """Acumula valores para cálculo de mediana de taxa."""
        if 'TAXA_DE_CESSAO' not in chunk.columns:
            return
    
        # Usar TAXA_DE_CESSAO diretamente
        taxas_de_cessao = chunk['TAXA_DE_CESSAO'].dropna()
        
        if not taxas_de_cessao.empty:
            # CORREÇÃO: Usar lista separada para taxas gerais
            self._todas_taxas_cessao_geral.extend(taxas_de_cessao.tolist())  # Lista para taxas gerais
    
        if 'TIPO_RECEBIVEL' in chunk.columns:
            for tipo in chunk['TIPO_RECEBIVEL'].unique():
                chunk_tipo = chunk[chunk['TIPO_RECEBIVEL'] == tipo]
                
                # Inicializar acumuladores para o tipo se não existirem
                if tipo not in self._todas_taxas_cessao_por_tipo:
                    self._todas_taxas_cessao_por_tipo[tipo] = []  # Dicionário para taxas por tipo
                    
                # Usar TAXA_DE_CESSAO diretamente
                taxas_de_cessao_tipo = chunk_tipo['TAXA_DE_CESSAO'].dropna()
            
                if not taxas_de_cessao_tipo.empty:
                    self._todas_taxas_cessao_por_tipo[tipo].extend(taxas_de_cessao_tipo.tolist())

    # ==================== FINALIZAÇÃO ====================
    
    def _finalizar_calculos(self) -> None:
        """Finaliza cálculos que dependem de todos os chunks."""
        self._calcular_metricas_globais_finais()
        
        for tipo in self.metricas_mensais_por_tipo.keys():
            self._finalizar_calculos_por_tipo(tipo)
        
        logger.info("Métricas calculadas para %d tipos de recebível", len(self.metricas_mensais_por_tipo))
    
    def _mediana_ratio(self, valores, taxas):
        # Invertido: agora garante que v (aquisição) não é zero para calcular taxa / aquisição
        pares = [(v, t) for v, t in zip(valores, taxas) if v not in (0, None)]
        if not pares:
            return None
        ratios = [t / v for v, t in pares]
        return statistics.median(ratios)
    
    def _calcular_metricas_globais_finais(self) -> None:
        m = self.metricas_globais

        m.total_sacados = len(self.sacados_acum)
        m.total_cedentes = len(self.cedentes_acum)

        self._calcular_tickets_medios(m)
        self._calcular_tickets_medios_ultima_quinzena(m)

        # Medianas
        if self._todas_taxas_media:
            m.mediana_taxa_media = statistics.median(self._todas_taxas_media)

        if self._todos_valores_aquisicao and self._todas_taxas_cessao_geral:
            m.mediana_valor_aquisicao = self._mediana_ratio(
                self._todos_valores_aquisicao,
                self._todas_taxas_cessao_geral
            )

        if self._todos_valores_aquisicao_a_vencer and self._todas_taxas_cessao_geral:
            m.mediana_a_vencer = self._mediana_ratio(
                self._todos_valores_aquisicao_a_vencer,
                self._todas_taxas_cessao_geral
            )

        if self._todos_valores_aquisicao_vencido and self._todas_taxas_cessao_geral:
            m.mediana_vencido = self._mediana_ratio(
                self._todos_valores_aquisicao_vencido,
                self._todas_taxas_cessao_geral
            )

        self._calcular_prazos_medios(m)
    
    def _calcular_tickets_medios(self, m: MetricasGlobais) -> None:
        """Calcula tickets médios gerais."""
        if m.qtd_aquisicao > 0:
            m.ticket_medio_presente_total = m.valor_presente / m.qtd_aquisicao
            m.ticket_medio_aquisicao_total = m.valor_aquisicao / m.qtd_aquisicao
            m.ticket_medio_nominal_total = m.valor_nominal / m.qtd_aquisicao
        
        if m.qtd_a_vencer > 0:
            m.ticket_medio_presente_a_vencer = m.valor_a_vencer / m.qtd_a_vencer
            m.ticket_medio_aquisicao_a_vencer = m.valor_aquisicao_a_vencer / m.qtd_a_vencer
            m.ticket_medio_nominal_a_vencer = m.valor_nominal_a_vencer / m.qtd_a_vencer
        
        if m.qtd_vencido > 0:
            m.ticket_medio_presente_vencido = m.valor_vencido / m.qtd_vencido
            m.ticket_medio_aquisicao_vencido = m.valor_aquisicao_vencido / m.qtd_vencido
            m.ticket_medio_nominal_vencido = m.valor_nominal_vencido / m.qtd_vencido
    
    def _calcular_tickets_medios_ultima_quinzena(self, m: MetricasGlobais) -> None:
        """Calcula tickets médios da última quinzena."""
        if m.ultima_quinzena_qtd_aquisicao > 0:
            m.ultima_quinzena_ticket_medio_presente_total = m.ultima_quinzena_valor_presente / m.ultima_quinzena_qtd_aquisicao
            m.ultima_quinzena_ticket_medio_aquisicao_total = m.ultima_quinzena_valor_aquisicao / m.ultima_quinzena_qtd_aquisicao
            m.ultima_quinzena_ticket_medio_nominal_total = m.ultima_quinzena_valor_nominal / m.ultima_quinzena_qtd_aquisicao
        
        if m.ultima_quinzena_qtd_a_vencer > 0:
            m.ultima_quinzena_ticket_medio_presente_a_vencer = m.ultima_quinzena_valor_a_vencer / m.ultima_quinzena_qtd_a_vencer
            m.ultima_quinzena_ticket_medio_aquisicao_a_vencer = m.ultima_quinzena_valor_aquisicao_a_vencer / m.ultima_quinzena_qtd_a_vencer
            m.ultima_quinzena_ticket_medio_nominal_a_vencer = m.ultima_quinzena_valor_nominal_a_vencer / m.ultima_quinzena_qtd_a_vencer
        
        if m.ultima_quinzena_qtd_vencido > 0:
            m.ultima_quinzena_ticket_medio_presente_vencido = m.ultima_quinzena_valor_vencido / m.ultima_quinzena_qtd_vencido
            m.ultima_quinzena_ticket_medio_aquisicao_vencido = m.ultima_quinzena_valor_aquisicao_vencido / m.ultima_quinzena_qtd_vencido
            m.ultima_quinzena_ticket_medio_nominal_vencido = m.ultima_quinzena_valor_nominal_vencido / m.ultima_quinzena_qtd_vencido
    
    def _calcular_prazos_medios(self, m: MetricasGlobais) -> None:
        """Calcula prazos médios."""
        if m.valor_aquisicao > 0:
            m.prazo_medio = m.prazo_medio_total / m.valor_aquisicao
        
        if m.valor_aquisicao_a_vencer > 0:
            m.prazo_medio_a_vencer = m.prazo_medio_total_a_vencer / m.valor_aquisicao_a_vencer
        
        if m.valor_aquisicao_vencido > 0:
            m.prazo_medio_vencido = m.prazo_medio_total_vencido / m.valor_aquisicao_vencido
        
        # Última quinzena
        if m.ultima_quinzena_valor_aquisicao > 0:
            m.ultima_quinzena_prazo_medio = m.ultima_quinzena_prazo_medio_total / m.ultima_quinzena_valor_aquisicao
        
        if m.ultima_quinzena_valor_aquisicao_a_vencer > 0:
            m.ultima_quinzena_prazo_medio_a_vencer = m.ultima_quinzena_prazo_medio_total_a_vencer / m.ultima_quinzena_valor_aquisicao_a_vencer
        
        if m.ultima_quinzena_valor_aquisicao_vencido > 0:
            m.ultima_quinzena_prazo_medio_vencido = m.ultima_quinzena_prazo_medio_total_vencido / m.ultima_quinzena_valor_aquisicao_vencido
    
    def _finalizar_calculos_por_tipo(self, tipo: str) -> None:
        """Finaliza cálculos para um tipo específico de recebível."""
        mg = self.metricas_globais_por_tipo[tipo]
        mm = self.metricas_mensais_por_tipo[tipo]
        
        mg.total_sacados = len(self.sacados_por_tipo.get(tipo, set()))
        mg.total_cedentes = len(self.cedentes_por_tipo.get(tipo, set()))
        
        # Tickets médios
        self._calcular_tickets_medios(mg)
        self._calcular_tickets_medios_ultima_quinzena(mg)
        
        # Prazos médios
        self._calcular_prazos_medios(mg)
        
        # Ticket médio mensal
        if mm.qtd_aquisicao_mes > 0:
            mm.ticket_medio_mensal = mm.valor_aquisicao_mes / mm.qtd_aquisicao_mes

        # Medianas - Primeiro calcula a mediana da taxa de cessão
        if tipo in self._todas_taxas_media_por_tipo and self._todas_taxas_media_por_tipo[tipo]:
            mg.mediana_taxa_media = statistics.median(self._todas_taxas_media_por_tipo[tipo])
            mg.mediana_taxa_cessao = statistics.median(self._todas_taxas_cessao_por_tipo[tipo])

       # self._todas_taxas_cessao_por_tipo[tipo].extend(taxas_de_cessao_tipo.tolist())
        else:
            mg.mediana_taxa_media = 0
        
        # Calcula medianas da taxa divididas pela mediana do valor de aquisição (taxa / aquisição)
        # Só calcula se a mediana do valor for maior que zero para evitar divisão por zero
        if tipo in self._todos_valores_aquisicao_por_tipo and self._todos_valores_aquisicao_por_tipo[tipo]:
            mediana_aq = statistics.median(self._todos_valores_aquisicao_por_tipo[tipo])
            if mediana_aq > 0:
                mg.mediana_valor_aquisicao = mg.mediana_taxa_cessao / mediana_aq
            else:
                mg.mediana_valor_aquisicao = 0
            
        if tipo in self._todos_valores_aquisicao_vencido_por_tipo and self._todos_valores_aquisicao_vencido_por_tipo[tipo]:
            mediana_aq_v = statistics.median(self._todos_valores_aquisicao_vencido_por_tipo[tipo])
            if mediana_aq_v > 0:
                mg.mediana_vencido = mg.mediana_taxa_cessao / mediana_aq_v
            else:
                mg.mediana_vencido = 0
            
        if tipo in self._todos_valores_aquisicao_a_vencer_por_tipo and self._todos_valores_aquisicao_a_vencer_por_tipo[tipo]:
            mediana_aq_av = statistics.median(self._todos_valores_aquisicao_a_vencer_por_tipo[tipo])
            if mediana_aq_av > 0:
                mg.mediana_a_vencer = mg.mediana_taxa_cessao / mediana_aq_av
            else:
                mg.mediana_a_vencer = 0
    
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
    
