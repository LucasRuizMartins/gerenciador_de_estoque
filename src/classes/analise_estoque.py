import pandas as pd
import numpy as np 
from zipfile import ZipFile
import humanize
import statistics
from zipfile import ZipFile
from typing import Dict, Optional, Iterator
from dataclasses import dataclass, field
import gc
import tempfile
import os
import io
from src.metricas import MetricasGlobais  
from src.metricas import MetricasVencimento 
from src.metricas import MetricasMensais  

humanize.activate("pt_BR")


class AnaliseEstoque:
    """
    Classe otimizada para análise de estoque de recebíveis com grandes volumes.
    Processa dados em chunks para minimizar uso de memória.
    """
    
    # Constantes de configuração
    COLUNAS_ESSENCIAIS = [
        'TIPO_RECEBIVEL', 'VALOR_NOMINAL', 'VALOR_PRESENTE', 'VALOR_AQUISICAO',
        'DATA_REFERENCIA', 'DATA_AQUISICAO', 'DATA_VENCIMENTO_ORIGINAL',
        'PRAZO_ATUAL', 'PRAZO', 'SITUACAO_RECEBIVEL', 'TAXA_CESSAO',
        'DOC_CEDENTE', 'NOME_CEDENTE', 'NOME_FUNDO', 'DOC_SACADO', 'NOME_SACADO', 'VALOR_PDD'
    ]    
    
    CHUNK_SIZE = 500_000

    DTYPE_MAP = {
        'TIPO_RECEBIVEL': 'category',
        'SITUACAO_RECEBIVEL': 'category',
        'DOC_CEDENTE': 'category',
        'NOME_CEDENTE': 'category',
        'DOC_SACADO': 'category',
        'NOME_SACADO': 'category',
        'NOME_FUNDO': 'category',
        'VALOR_NOMINAL': 'float64',
        'VALOR_PRESENTE': 'float64',
        'VALOR_AQUISICAO': 'float64',
        'PRAZO_ATUAL': 'int16',
        'TAXA_CESSAO': 'float64',
        'VALOR_PDD': 'float64',
    }
    
 
    def __init__(self, arquivo):

        self._inicializar_metricas()
        self._inicializar_acumuladores()
        self.data_ref = pd.Timestamp.now().replace(day=1)

        try:
            # 🔥 Normalização: garantir caminho físico
            if hasattr(arquivo, "read"):  # UploadedFile
                arquivo.seek(0)

                sufixo = os.path.splitext(arquivo.name)[-1]

                with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
                    tmp.write(arquivo.read())
                    caminho = tmp.name
            else:
                caminho = arquivo  # já é path

            print(f"Iniciando processamento de {caminho}...")
            self._processar_arquivo_chunks(caminho)
            self._finalizar_calculos()
            print("Processamento concluído com sucesso!")

        except Exception as e:
            (f"Erro ao processar arquivo: {e}")
        
    
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
    
    # ==================== PROCESSAMENTO EM CHUNKS ====================
    
    def _processar_arquivo_chunks(self, path: str) -> None:
        """Processa arquivo em chunks para economizar memória."""
        self._determinar_data_referencia(path)
        print(f"Data de referência identificada: {self.data_ref.strftime('%Y-%m-%d')}")
        
        chunk_iterator = self._obter_chunk_iterator(path)
        
        for chunk_num, chunk in enumerate(chunk_iterator, 1):
            if chunk_num % 10 == 0:
                print(f"Processando chunk {chunk_num}...")
            
            chunk = self._preparar_chunk(chunk)
            self._processar_chunk(chunk)
            del chunk
            
            if chunk_num % 20 == 0:
                gc.collect()
    
    def _determinar_data_referencia(self, path: str) -> None:
        """Determina a data de referência usando apenas o primeiro registro válido."""
        try:
            chunk = next(self._obter_chunk_iterator(path), None)
            if chunk is not None and not chunk.empty:
                data_str = chunk.get('DATA_REFERENCIA', [None])[0]
                data_ref = pd.to_datetime(data_str, dayfirst=True, errors='coerce')
                if pd.notna(data_ref):
                    self.data_ref = data_ref
        except Exception:
            pass
        
        self.metricas_mensais.data_ref = self.data_ref
    
    def _obter_chunk_iterator(self, path: str) -> Iterator[pd.DataFrame]:
        """Retorna iterador de chunks baseado no tipo de arquivo."""
        extensao = path.lower()
        
        if extensao.endswith('.csv'):
            return self._chunks_csv(path)
        elif extensao.endswith(('.xlsx', '.xls')):
            return self._chunks_excel(path)
        elif extensao.endswith('.zip'):
            return self._chunks_zip(path)
        else:
            raise ValueError("Formato não suportado. Use .csv, .xlsx, .xls ou .zip")
    
    def _chunks_csv(self, path: str) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivo CSV."""
        return pd.read_csv(
            path,
            encoding='ISO-8859-1',
            on_bad_lines='skip',
            delimiter=';',
            decimal=',',
            thousands='.',
            low_memory=False,
            chunksize=self.CHUNK_SIZE,
            usecols=lambda col: col in self.COLUNAS_ESSENCIAIS
        )
    
    def _chunks_excel(self, path: str) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivo Excel."""
        df = pd.read_excel(path, usecols=lambda col: col in self.COLUNAS_ESSENCIAIS)
        for i in range(0, len(df), self.CHUNK_SIZE):
            yield df.iloc[i:i + self.CHUNK_SIZE].copy()
    
    def _chunks_zip(self, path: str) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivos CSV dentro de ZIP."""
        with ZipFile(path) as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    print(f"Processando arquivo: {filename}")
                    with z.open(filename) as f:
                        yield from pd.read_csv(
                            f,
                            encoding='ISO-8859-1',
                            delimiter=';',
                            decimal=',',
                            thousands='.',
                            low_memory=False,
                            chunksize=self.CHUNK_SIZE,
                            on_bad_lines='skip',
                            usecols=lambda col: col in self.COLUNAS_ESSENCIAIS
                        )
    
    # ==================== PREPARAÇÃO DE DADOS ====================
    
    def _preparar_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Prepara chunk com conversões de tipo otimizadas."""
        self._converter_datas(chunk)
        self._converter_tipos(chunk)
        self._adicionar_colunas_calculadas(chunk)
        return chunk
    
    def _converter_datas(self, chunk: pd.DataFrame) -> None:
        """Converte colunas de data."""
        colunas_data = ['DATA_REFERENCIA', 'DATA_AQUISICAO', 'DATA_VENCIMENTO_ORIGINAL']
        for col in colunas_data:
            if col in chunk.columns:
                chunk[col] = pd.to_datetime(chunk[col], dayfirst=True, errors='coerce')
    
    def _converter_tipos(self, chunk: pd.DataFrame) -> None:
        """Converte tipos de dados das colunas."""
        for col, dtype in self.DTYPE_MAP.items():
            if col not in chunk.columns:
                continue
            
            if dtype == 'category':
                chunk[col] = chunk[col].astype('category')
            elif dtype in ['float32', 'float64']:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(dtype)
            elif dtype in ['int16', 'int32']:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(dtype)
    
    def _adicionar_colunas_calculadas(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Adiciona colunas calculadas ao dataframe."""
        if 'VALOR_AQUISICAO' in chunk.columns and 'TAXA_CESSAO' in chunk.columns:
            chunk['TAXA_MEDIA'] = (
                pd.to_numeric(chunk['VALOR_AQUISICAO'], errors='coerce').fillna(0) *
                pd.to_numeric(chunk['TAXA_CESSAO'], errors='coerce').fillna(0)
            ).astype('float64')
        
        if 'PRAZO' in chunk.columns and 'VALOR_AQUISICAO' in chunk.columns:
            chunk['PRAZO_MEDIO'] = (chunk['VALOR_AQUISICAO'] * chunk['PRAZO']).astype('float64')
            chunk['TAXA_DE_CESSAO'] = taxa_anual = ((chunk['VALOR_NOMINAL'] / chunk['VALOR_AQUISICAO']) ** (252 / chunk['PRAZO']) - 1) * 100
     

        
        return chunk
    
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
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'A vencer', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
        
        # Faixas Vencido (Valor Presente)
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
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'Vencido', 'VALOR_PRESENTE')
            setattr(mv, attr, getattr(mv, attr) + valor)
        
        # PDD A vencer
        for attr, prazo_min, prazo_max in faixas_a_vencer:
            attr_pdd = f'pdd_{attr}'
            valor = self._somar_vencimento(chunk, prazo_min, prazo_max, 'A vencer', 'VALOR_PDD')
            setattr(mv, attr_pdd, getattr(mv, attr_pdd) + valor)
        
        # PDD Vencido
        for attr, prazo_min, prazo_max in faixas_vencido:
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
        
        print(f"\nMétricas calculadas para {len(self.metricas_mensais_por_tipo)} tipos de recebível")
    
    def _mediana_ratio(self,valores, taxas):
        pares = [(v, t) for v, t in zip(valores, taxas) if t not in (0, None)]
        if not pares:
            return None
        ratios = [v / t for v, t in pares]
        return statistics.median(ratios)
    
    def _calcular_metricas_globais_finais(self) -> None:
        m = self.metricas_globais

        self.total_sacados = len(self.sacados_acum)
        self.total_cedentes = len(self.cedentes_acum)

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
        
        # Calcula medianas dos valores de aquisição divididas pela mediana da taxa
        # Só calcula se a mediana da taxa for maior que zero para evitar divisão por zero

        print(f"mg.mediana_taxa_cessao - {mg.mediana_taxa_cessao}")
        if mg.mediana_taxa_media > 0:
            if tipo in self._todos_valores_aquisicao_por_tipo and self._todos_valores_aquisicao_por_tipo[tipo]:
                mg.mediana_valor_aquisicao = statistics.median(self._todos_valores_aquisicao_por_tipo[tipo]) / statistics.median(self._todas_taxas_cessao_por_tipo[tipo]) #mg.mediana_taxa_media
            
            if tipo in self._todos_valores_aquisicao_vencido_por_tipo and self._todos_valores_aquisicao_vencido_por_tipo[tipo]:
                mg.mediana_vencido = statistics.median(self._todos_valores_aquisicao_vencido_por_tipo[tipo]) / statistics.median(self._todas_taxas_cessao_por_tipo[tipo]) #mg.mediana_taxa_media
            
            if tipo in self._todos_valores_aquisicao_a_vencer_por_tipo and self._todos_valores_aquisicao_a_vencer_por_tipo[tipo]:
                mg.mediana_a_vencer = statistics.median(self._todos_valores_aquisicao_a_vencer_por_tipo[tipo]) /statistics.median(self._todas_taxas_cessao_por_tipo[tipo]) #mg.mediana_taxa_media
        else:
            mg.mediana_valor_aquisicao = 0
            mg.mediana_vencido = 0
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
    
    # ==================== EXPORTAÇÃO ====================
    
    def exportar_para_excel(self, output) -> bool:
        """Exporta métricas para Excel (arquivo ou buffer)."""
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_relatorio = self._construir_dataframe_relatorio()

                if df_relatorio.empty:
                    print("DataFrame principal vazio!")

                df_relatorio.to_excel(writer, sheet_name='Relatório Consolidado', index=False)
                self._formatar_planilha_excel(writer, df_relatorio)

                df_cedentes = self.obter_cedentes_agrupados()
                if not df_cedentes.empty:
                    df_cedentes.to_excel(writer, sheet_name='Cedentes', index=False)

                df_recebiveis = self.obter_recebiveis_agrupados()
                if not df_recebiveis.empty:
                    df_recebiveis.to_excel(writer, sheet_name='Recebíveis', index=False)

                writer.close()  # 🔥 importante para buffer

            return True

        except Exception as e:
            print(f"Erro na exportação: {e}")
        return False
  
    
    def _construir_dataframe_relatorio(self) -> pd.DataFrame:
        """Constrói DataFrame com todas as métricas."""
        metricas = [
            "Nome Fundo",
            "Data de Referência",
            "Valor Nominal Total",
            "Vencido",
            "A vencer",
            "PDD",
            "Total",
            "Valor Aquisição Total",
            "Quantidade de Titulos",
            "Quantidade de Titulos a vencer",
            "Quantidade de titulos vencido",
            "Total de Sacados",
            "Total de Cedentes",
            "Valor Aquisição no Mês",
            "Quantidade Aquisição no Mês",
            "Ticket Médio Aquisicao a vencer",
            "Ticket Médio Aquisicao a vencido",
            "Ticket Médio Aquisicao a total",
            "Ticket Médio Presente a vencer",
            "Ticket Médio Presente a vencido",
            "Ticket Médio Presente a total",
            "Ticket Médio Nominal a vencer",
            "Ticket Médio Nominal a vencido",
            "Ticket Médio Nominal a total",            
            "taxa cessao mediana a vencer",
            "taxa cessao mediana vencido",
            "taxa cessao mediana total",            
            "Ultima Quinzena Ticket Médio Aquisicao a vencer",
            "Ultima Quinzena Ticket Médio Aquisicao a vencido",
            "Ultima Quinzena Ticket Médio Aquisicao a total",
            "Ultima Quinzena Ticket Médio Presente a vencer",
            "Ultima Quinzena Ticket Médio Presente a vencido",
            "Ultima Quinzena Ticket Médio Presente a total",
            "Ultima Quinzena Ticket Médio Nominal a vencer",
            "Ultima Quinzena Ticket Médio Nominal a vencido",
            "Ultima Quinzena Ticket Médio Nominal a total",
            "Prazo Médio TOTAL",
            "Prazo Médio Vencido",
            "Prazo Médio A vencer",
            "Ultima Quinzena Prazo Médio TOTAL",
            "Ultima Quinzena Prazo Médio Vencido",
            "Ultima Quinzena Prazo Médio A vencer",
            "Taxa Média do Mês",
        ]
        
        # Adicionar faixas de vencimento
        for situacao in ["A Vencer", "Vencido", "PDD A Vencer", "PDD Vencido"]:
            for faixa in ["0-15", "16-30", "31-60", "61-90", "91-120", "121-150", "151-180", "181-360", "+ 360"]:
                metricas.append(f"{situacao} {faixa} dias")
        
        valores_totais = self._obter_valores_totais()
        
        dados = {"Métrica": metricas, "Valor Total": valores_totais}
        
        df = pd.DataFrame(dados)
        
        # Adicionar colunas por tipo
        for tipo in sorted(self.metricas_globais_por_tipo.keys()):
            df[tipo] = self._obter_valores_por_tipo(tipo)
        
        return df
    
    def _obter_valores_totais(self) -> list:
        """Obtém lista de valores totais."""
        m = self.metricas_globais
        mm = self.metricas_mensais
        mv = self.metricas_vencimento
        
        valores = [
            m.nome_fundo,
            mm.data_ref.strftime("%Y/%m/%d"),
            m.valor_nominal,
            m.valor_vencido,
            m.valor_a_vencer,
            m.valor_pdd,
            m.valor_presente,
            m.valor_aquisicao,
            m.cont_transacoes,
            m.qtd_a_vencer,
            m.qtd_vencido,
            m.total_sacados,
            m.total_cedentes,
            mm.valor_aquisicao_mes,
            mm.qtd_aquisicao_mes,
            m.ticket_medio_aquisicao_a_vencer,
            m.ticket_medio_aquisicao_vencido,
            m.ticket_medio_aquisicao_total,
            m.ticket_medio_presente_a_vencer,
            m.ticket_medio_presente_vencido,
            m.ticket_medio_presente_total,
            m.ticket_medio_nominal_a_vencer,
            m.ticket_medio_nominal_vencido,
            m.ticket_medio_nominal_total,
            
            m.mediana_a_vencer,
            m.mediana_vencido,
            m.mediana_valor_aquisicao,
            
            m.ultima_quinzena_ticket_medio_aquisicao_a_vencer,
            m.ultima_quinzena_ticket_medio_aquisicao_vencido,
            m.ultima_quinzena_ticket_medio_aquisicao_total,
            m.ultima_quinzena_ticket_medio_presente_a_vencer,
            m.ultima_quinzena_ticket_medio_presente_vencido,
            m.ultima_quinzena_ticket_medio_presente_total,
            m.ultima_quinzena_ticket_medio_nominal_a_vencer,
            m.ultima_quinzena_ticket_medio_nominal_vencido,
            m.ultima_quinzena_ticket_medio_nominal_total,
            m.prazo_medio,
            m.prazo_medio_vencido,
            m.prazo_medio_a_vencer,
            m.ultima_quinzena_prazo_medio,
            m.ultima_quinzena_prazo_medio_vencido,
            m.ultima_quinzena_prazo_medio_a_vencer,
            mm.taxa_media_mes,
        ]
        
        # Adicionar valores de vencimento
        faixas_attr = [
            ('a_vencer', mv), ('vencido', mv),
            ('pdd_a_vencer', mv), ('pdd_vencido', mv)
        ]
        
        intervalos = ['0_15', '16_30', '31_60', '61_90', '91_120', '121_150', '151_180', '181_360', 'acima_360']
        
        for prefixo, obj in faixas_attr:
            for intervalo in intervalos:
                attr = f'{prefixo}_{intervalo}'
                valores.append(getattr(obj, attr, 0))
        
        return valores
    
    def _obter_valores_por_tipo(self, tipo: str) -> list:
        """Obtém lista de valores para um tipo específico."""
        mg = self.metricas_globais_por_tipo.get(tipo, MetricasGlobais())
        mm = self.metricas_mensais_por_tipo.get(tipo, MetricasMensais())
        mv = self.metricas_vencimento_por_tipo.get(tipo, MetricasVencimento())
        
        valores = [
            self.metricas_globais.nome_fundo,  # Nome Fundo
            self.metricas_mensais.data_ref.strftime("%Y/%m/%d"),  # Data Referência
            mg.valor_nominal,
            mg.valor_vencido,
            mg.valor_a_vencer,
            mg.valor_pdd,
            mg.valor_presente,
            mg.valor_aquisicao,
            mg.cont_transacoes,
            mg.qtd_a_vencer,
            mg.qtd_vencido,
            mg.total_sacados,
            mg.total_cedentes,
            mm.valor_aquisicao_mes,
            mm.qtd_aquisicao_mes,
            mg.ticket_medio_aquisicao_a_vencer,
            mg.ticket_medio_aquisicao_vencido,
            mg.ticket_medio_aquisicao_total,
            mg.ticket_medio_presente_a_vencer,
            mg.ticket_medio_presente_vencido,
            mg.ticket_medio_presente_total,
            mg.ticket_medio_nominal_a_vencer,
            mg.ticket_medio_nominal_vencido,
            mg.ticket_medio_nominal_total,
            
            mg.mediana_a_vencer,
            mg.mediana_vencido,
            mg.mediana_valor_aquisicao,  
            
            mg.ultima_quinzena_ticket_medio_aquisicao_a_vencer,
            mg.ultima_quinzena_ticket_medio_aquisicao_vencido,
            mg.ultima_quinzena_ticket_medio_aquisicao_total,
            mg.ultima_quinzena_ticket_medio_presente_a_vencer,
            mg.ultima_quinzena_ticket_medio_presente_vencido,
            mg.ultima_quinzena_ticket_medio_presente_total,
            mg.ultima_quinzena_ticket_medio_nominal_a_vencer,
            mg.ultima_quinzena_ticket_medio_nominal_vencido,
            mg.ultima_quinzena_ticket_medio_nominal_total,
            mg.prazo_medio,
            mg.prazo_medio_vencido,
            mg.prazo_medio_a_vencer,
            mg.ultima_quinzena_prazo_medio,
            mg.ultima_quinzena_prazo_medio_vencido,
            mg.ultima_quinzena_prazo_medio_a_vencer,
            mm.taxa_media_mes,
        ]
        
        # Adicionar valores de vencimento com os nomes corretos dos atributos
        intervalos = ['0_15', '16_30', '31_60', '61_90', '91_120', '121_150', '151_180', '181_360', 'acima_360']
        
        # A Vencer
        for intervalo in intervalos:
            attr = f'a_vencer_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # Vencido
        for intervalo in intervalos:
            attr = f'vencido_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # PDD A Vencer
        for intervalo in intervalos:
            attr = f'pdd_a_vencer_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # PDD Vencido
        for intervalo in intervalos:
            attr = f'pdd_vencido_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        return valores
    
    def _formatar_planilha_excel(self, writer, df: pd.DataFrame) -> None:
        """Aplica formatação ao arquivo Excel."""
        workbook = writer.book
        worksheet = writer.sheets['Relatório Consolidado']
        
        # Formatos
        money_fmt = workbook.add_format({'num_format': '#,##0.00'})
        percent_fmt = workbook.add_format({'num_format': '0.00%'})
        integer_fmt = workbook.add_format({'num_format': '#,##0'})
        
        # Formato monetário padrão
        for col_num in range(1, len(df.columns)):
            worksheet.set_column(col_num, col_num, 18, money_fmt)
        
        # Formato inteiro para contagens
        metricas_inteiro = ["Quantidade de Titulos", "Quantidade Aquisição no Mês",
                           "Quantidade de Titulos a vencer", "Quantidade de titulos vencido",
                           "Total de Sacados", "Total de Cedentes"]
        
        for metrica in metricas_inteiro:
            indices = df[df['Métrica'] == metrica].index
            if len(indices) > 0:
                row = indices[0] + 1
                for col_num in range(1, len(df.columns)):
                    worksheet.write(row, col_num, df.iloc[indices[0], col_num], integer_fmt)
        
        # Formato percentual para taxa
        indices_taxa = df[df['Métrica'] == 'Taxa Média do Mês'].index
        if len(indices_taxa) > 0:
            row = indices_taxa[0] + 1
            for col_num in range(1, len(df.columns)):
                worksheet.write(row, col_num, df.iloc[indices_taxa[0], col_num], percent_fmt)
        
        # Largura da coluna de métricas
        worksheet.set_column(0, 0, 40)
    
    @staticmethod
    def formatar_numero(valor: float) -> str:
        """Formata valor para padrão monetário brasileiro."""
        return f"{valor:,.0f}".replace(",", ".")
    
    @staticmethod
    def formatar_moeda(valor: float) -> str:
        """Formata valor para padrão monetário brasileiro."""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    @staticmethod
    def formatar_percentual(valor: float) -> str:
        """Formata valor para percentual brasileiro."""
        return f"{valor*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    
    @staticmethod
    def formatar_pl_humano(valor):
        try:
            # 1. Garante que o valor seja numérico (float/int)
            valor_num = pd.to_numeric(valor, errors='coerce')
            
            if pd.isna(valor_num) or valor_num == 0:
                return "R$ 0,00"                
            # 2. Transforma 1.000.000 em "1,0 milhão"
            res = humanize.intword(valor_num)
            return f"R$ {res}"
            
        except Exception as e: # 'Exception' com E maiúsculo e sem erro de grafia
            print(f"Erro na formatação: {e}")
            return "R$ 0,00"
    
def salvar(path,df):
    if path:
        output_excel_path = path
        if not output_excel_path.lower().endswith('.xlsx'):
            output_excel_path += '.xlsx'
        if df:
            if df.exportar_para_excel(output_excel_path):
               print(f"Dados exportados com sucesso para: {output_excel_path}")
            else:
                print("Erro ao exportar dados para Excel.")                 
        else:
          print("Nenhum dado para exportar. Carregue um arquivo primeiro.")           
    else:
        print("Nenhum local de salvamento selecionado.")
        
        
    def exportar_para_excel(self, destino):
        with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
            self.df.to_excel(writer, index=False)
            # outras abas se tiver